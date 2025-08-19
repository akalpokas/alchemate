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


from pathlib import Path
import BioSimSpace.FreeEnergy as BSS
from alchemlyb.convergence import forward_backward_convergence
import sire as sr

from .base import WorkflowStep
from ..context import SimulationContext
from ._run_somd2 import _run_somd2_workflow


class OptimizeConvergence(WorkflowStep):
    """ """

    def __init__(
        self,
        optimization_attempts: int = 3,
        optimization_threshold: float = 0.25,  # std. dev. of kT/mol for final 50% of data
        optimization_runtime: str = "500ps",
    ) -> None:
        super().__init__()
        self.optimization_attempts: int = optimization_attempts
        self.optimization_threshold: float = optimization_threshold
        self.optimization_runtime: str = optimization_runtime

    def _extract_somd2_parquet(self, context: SimulationContext):
        """
        Extracts energies from SOMD2 parquet files.

        Returns:
        - extracted_df_list (list): A list of dataframes containing the extracted results for work directory.
        """

        temperature = sr.u(context.somd2_config.temperature).value()
        extracted_df_list = []
        glob_path = Path(context.somd2_config.output_directory)
        files = sorted(glob_path.glob("**/*.parquet"))
        for f in files:
            path = Path(f)
            extracted_df = BSS.Relative._somd2_extract(path, T=temperature)
            extracted_df_list.append(extracted_df)

        return extracted_df_list

    def _estimate_convergence(self, context: SimulationContext):
        """Internal function to calculate current free energy convergence."""
        extracted_df_list = []
        try:
            extracted_df_list = self._extract_somd2_parquet(context)
        except Exception as e:
            print(f"Error reading extracted data: {e}")

        if not extracted_df_list:
            raise RuntimeError(
                "No extracted dataframes available for convergence analysis."
            )

        convergence_df = forward_backward_convergence(
            extracted_df_list, estimator="MBAR"
        )
        converged = self._test_convergence(convergence_df)
        return converged

    def _test_convergence(self, df):
        df = df[(df["data_fraction"] >= 0.5) & (df["data_fraction"] <= 1)]

        free_energy_std = df["Forward"].std()
        print(f"Free energy standard deviation: {free_energy_std:.4f} kT/mol")

        if free_energy_std < self.optimization_threshold:
            return True
        else:
            return False

    def run(self, context: SimulationContext):
        print("\n--- Running Step: ConvergenceAnalysis ---")

        for _ in range(self.optimization_attempts):
            converged = self._estimate_convergence(context)
            if converged:
                print("Simulation converged!")
                break
            else:
                old_runtime = context.somd2_config.runtime
                new_runtime = sr.u(old_runtime) + sr.u(self.optimization_runtime)
                print(f"Extending runtime from {old_runtime} to {new_runtime}")
                context.somd2_config.restart = True
                context.somd2_config.runtime = new_runtime.to_string()
                _run_somd2_workflow(context=context)
