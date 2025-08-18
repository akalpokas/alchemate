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

from .base import WorkflowStep
from ..context import SimulationContext
from ._run_somd2 import _run_somd2_workflow
from copy import deepcopy
import numpy as np

class PrepareSystem(WorkflowStep):
    """A step to set up simulation parameters."""
    def run(self, context: SimulationContext):
        print("\n--- Running Step: PrepareSystem ---")
        print(f"Reading from {context.preprocess_parameters} to determine parameters.")
        
        # This step's logic would go here. For now, we'll just add some params.
        context.preprocess_parameters["temperature"] = 300  # in Kelvin
        context.preprocess_parameters["box_size"] = (10, 10, 10) # in Angstroms
        print("System parameters prepared and added to context.")

class OptimizeExchangeProbabilities(WorkflowStep):
    """A step to optimize exchange probabilities.
    This is done by running a short simulation of the target system in vacuum.
    Replica exchange matrix is then read along with the lambda schedule in order
    to determine where the optimization should occur.
    """
    def __init__(self, optimization_attempts: int = 3,
                 optimization_threshold: float = 0.15,
                 optimization_runtime: str = "500ps",
                 vacuum_optimization: bool = True) -> None:
        super().__init__()
        self.optimization_attempts: int = optimization_attempts
        self.optimization_threshold: float = optimization_threshold
        self.optimization_runtime: str = optimization_runtime
        self.vacuum_optimization = vacuum_optimization

    def _optimize_exchange_matrix(self, context: SimulationContext):
        """Internal function to optimize the exchange matrix."""
        try:
            repex_matrix = context.somd2_config.output_directory / "repex_matrix.txt"
            repex_matrix = np.loadtxt(repex_matrix)
        except Exception as e:
            print(f"Error reading repex_matrix: {e}")

        if context.somd2_config.lambda_values is None:
            lambda_values = np.linspace(0, 1, context.somd2_config.num_lambda).tolist()
        else:
            lambda_values = context.somd2_config.lambda_values

        require_optimization = []
        for i, row in enumerate(repex_matrix):
            if i < len(repex_matrix) - 1:
                exchange_prob = row[i+1]
                print(f"Exchange probability between replica {i} and {i+1}: {exchange_prob}")
                if exchange_prob < self.optimization_threshold:
                    require_optimization.append((i, i+1))
                    print(f"Warning: Low exchange probability detected ({exchange_prob})")

        print("Replicas requiring optimization:")
        for replica_pair in require_optimization:
            print(f" - Replica {replica_pair[0]} and {replica_pair[1]}")

        # insert a new lambda between lambda values that require optimization
        new_lambdas = []
        for i, j in require_optimization:
            new_lambda = (lambda_values[i] + lambda_values[j]) / 2
            new_lambdas.append(round(new_lambda, 3))

        # insert new lambdas into the original array
        for new_lambda in new_lambdas:
            lambda_values.append(new_lambda)

        lambda_values = sorted(lambda_values)
        print(f"New lambda values after optimization: {lambda_values}")
        return lambda_values

    def run(self, context: SimulationContext):

        print("\n--- Running Step: OptimizeExchangeProbabilities ---")
        print(f"Using parameters from {context.preprocess_parameters}.")
        print("System parameters prepared and added to context.")

        if self.vacuum_optimization:
            import sire as sr
            sire_system = sr.stream.load(context.system)
            perturbable_mols = sire_system.molecules("property is_perturbable")
            system = sr.system.System()
            system.add(perturbable_mols)
            context.system = system
        

        # overwrite SOMD2 config
        context.somd2_config.runtime = self.optimization_runtime
        context.somd2_config.overwrite = True
        _run_somd2_workflow(context=context)

        for i in range(self.optimization_attempts):
            if context.somd2_config.lambda_values is None:
                old_lambda_values = np.linspace(0, 1, context.somd2_config.num_lambda).tolist()
            else:
                old_lambda_values = context.somd2_config.lambda_values

            optimized_lambda_values = self._optimize_exchange_matrix(context=context)
            if old_lambda_values == optimized_lambda_values:
                print("Optimization successful!")
                break
            else:
                context.somd2_config.lambda_values = optimized_lambda_values
                _run_somd2_workflow(context=context)