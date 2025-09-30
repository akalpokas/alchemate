######################################################################
# alchemate: Modular SOMD2 processing workflows
#
# Copyright: 2025
#
# Authors: Audrius Kalpokas
#
# alchemate is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# alchemate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with alchemate. If not, see <http://www.gnu.org/licenses/>.
#####################################################################

from copy import deepcopy
import logging
import numpy as np
import sire as sr
import BioSimSpace.FreeEnergy as BSS

from .base import WorkflowStep
from ..context import SimulationContext
from ._run_somd2 import _run_somd2_workflow

_logger = logging.getLogger("alchemate.logger")


class OptimizeLambdaProbabilities(WorkflowStep):
    """
    Workflow step to optimize probabilities by adjusting the lambda schedule.

    This step runs a short simulation (in vacuum by default) to evaluate the overlap/exchange probabilities
    between neighboring replicas. If any pair of replicas exhibits a low probability
    (below the specified threshold), new lambda values are inserted between those replicas to improve
    overlap/exchange rates. The optimization is performed iteratively for a specified number of attempts.

    Attributes
    ----------
    optimization_target(str): Whether to optimize the 'overlap_matrix' or 'repex_matrix'.
    optimization_attempts (int): Number of optimization iterations to perform.
    optimization_threshold (float): Minimum acceptable probability between replicas.
    optimization_runtime (str): Duration of each optimization simulation.
    vacuum_optimization (bool): Whether to perform optimization in vacuum.

    Methods
    -------
    _optimize_matrix(context):
        Reads the matrix and lambda schedule, identifies pairs with low
        probabilities, and inserts new lambda values to improve overlap/exchange rates.

    _execute(context):
        Runs the optimization workflow, updating the lambda schedule as needed and restoring
        the original system after optimization.
    """

    def __init__(
        self,
        optimization_target="overlap_matrix",
        optimization_attempts: int = 3,
        optimization_threshold: float = 0.10,
        optimization_runtime: str = "100ps",
        vacuum_optimization: bool = True,
    ) -> None:
        super().__init__()
        self.optimization_target: str = optimization_target
        self.optimization_attempts: int = optimization_attempts
        self.optimization_threshold: float = optimization_threshold
        self.optimization_runtime: str = optimization_runtime
        self.vacuum_optimization = vacuum_optimization

    def _optimize_matrix(self, context: SimulationContext):
        """Internal function to optimize matrix."""
        if self.optimization_target == "repex_matrix":
            try:
                repex_matrix = (
                    context.somd2_config.output_directory / "repex_matrix.txt"
                )
                repex_matrix = np.loadtxt(repex_matrix)
                matrix = repex_matrix
            except Exception as e:
                _logger.error(f"Error reading repex_matrix: {e}")
        elif self.optimization_target == "overlap_matrix":
            try:
                _, overlap_matrix = BSS.Relative.analyse(
                    str(context.somd2_config.output_directory)
                )
                overlap_matrix = overlap_matrix.tolist()
                matrix = overlap_matrix
            except Exception as e:
                _logger.error(f"Error reading overlap_matrix: {e}")
        else:
            _logger.error(f"Unknown optimization target: {self.optimization_target}")
            raise NotImplementedError

        if context.somd2_config.lambda_values is None:
            lambda_values = np.linspace(0, 1, context.somd2_config.num_lambda).tolist()
        else:
            lambda_values = context.somd2_config.lambda_values

        require_optimization = []
        for i, row in enumerate(matrix):
            if i < len(matrix) - 1:
                exchange_prob = round(row[i + 1], ndigits=2)
                _logger.info(
                    f"Overlap/Exchange probability between window {i} and {i+1}: {exchange_prob}"
                )
                if exchange_prob < self.optimization_threshold:
                    require_optimization.append((i, i + 1))
                    _logger.warning(
                        f"Low overlap/exchange probability detected ({exchange_prob})"
                    )

        _logger.info("Windows requiring optimization:")
        for window_pair in require_optimization:
            _logger.info(f" - Window {window_pair[0]} and {window_pair[1]}")

        # Insert a new lambda between lambda values that require optimization
        new_lambdas = []
        for i, j in require_optimization:
            new_lambda = (lambda_values[i] + lambda_values[j]) / 2
            new_lambdas.append(round(new_lambda, 3))

        for new_lambda in new_lambdas:
            lambda_values.append(new_lambda)

        lambda_values = sorted(lambda_values)
        _logger.info(f"New lambda values after optimization: {lambda_values}")
        return lambda_values

    def _execute(self, context: SimulationContext):
        if self.vacuum_optimization:
            # Retain the original system
            original_system = deepcopy(context.system)
            sire_system = sr.stream.load(context.system)
            perturbable_mols = sire_system.molecules("property is_perturbable")
            system = sr.system.System()
            system.add(perturbable_mols)
            context.system = system

        # Overwrite SOMD2 config with step specific params
        context.somd2_config.runtime = self.optimization_runtime
        context.somd2_config.overwrite = True
        _logger.info(context.somd2_config)
        _run_somd2_workflow(context=context)

        for _ in range(self.optimization_attempts):
            if context.somd2_config.lambda_values is None:
                old_lambda_values = np.linspace(
                    0, 1, context.somd2_config.num_lambda
                ).tolist()
            else:
                old_lambda_values = context.somd2_config.lambda_values

            optimized_lambda_values = self._optimize_matrix(context=context)

            # Success condition test
            if old_lambda_values == optimized_lambda_values:
                _logger.info("Optimization successful!")
                break
            else:
                context.somd2_config.lambda_values = optimized_lambda_values
                _run_somd2_workflow(context=context)

        # Now restore the old system to prevent any modifications
        if self.vacuum_optimization:
            context.system = original_system
