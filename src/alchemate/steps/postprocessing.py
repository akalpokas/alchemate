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

import logging
from pathlib import Path
import BioSimSpace.FreeEnergy as BSS
from alchemlyb import convergence, visualisation, estimators
import matplotlib.pyplot as plt
import pandas as pd
import sire as sr
import seaborn as sns

from .base import WorkflowStep
from ..context import SimulationContext
from ._run_somd2 import _run_somd2_workflow

_logger = logging.getLogger("alchemate.logger")


class OptimizeConvergence(WorkflowStep):
    """
    Workflow step for optimizing the convergence of free energy calculations.

    This class attempts to ensure that the free energy estimator error falls below a specified threshold
    by repeatedly extending the simulation runtime and re-evaluating convergence. It extracts energy data
    from SOMD2 parquet files, estimates convergence using the MBAR estimator, and manages simulation restarts.

    Attributes
    ----------
    optimization_attempts (int): Maximum number of optimization attempts to achieve convergence.
    optimization_threshold (float): Acceptable estimator error threshold (in kT/mol).
    optimization_runtime (str): Amount of simulation time to add per optimization attempt.
    plot_convergence (bool): Whether to plot convergence results.

    Methods
    -------
    _extract_somd2_parquet(context):
        Extracts energy data from SOMD2 parquet files in the simulation output directory.

    _estimate_convergence(context):
        Calculates current free energy convergence using extracted data and MBAR estimator.

    _test_convergence(df):
        Tests if the estimator error in the provided DataFrame is below the optimization threshold.

    _execute(context):
        Runs the optimization loop, extending simulation runtime and restarting as needed until
        convergence is achieved or the maximum number of attempts is reached.
    """

    def __init__(
        self,
        optimization_attempts: int = 3,
        optimization_threshold: float = 0.20,
        optimization_runtime: str = "500ps",
        plot_convergence: bool = True,
    ) -> None:
        super().__init__()
        self.optimization_attempts: int = optimization_attempts
        self.optimization_threshold: float = optimization_threshold
        self.optimization_runtime: str = optimization_runtime
        self.plot_convergence: bool = plot_convergence

    def _extract_somd2_parquet(self, context: SimulationContext):
        """
        Extracts energies from SOMD2 parquet files.

        Returns:
        - extracted_dfs (list): A list of dataframes containing the extracted results for work directory.
        """

        temperature = sr.u(context.somd2_config.temperature).value()
        extracted_dfs = []
        glob_path = Path(context.somd2_config.output_directory)
        files = sorted(glob_path.glob("**/*.parquet"))

        for f in files:
            path = Path(f)
            extracted_df = BSS.Relative._somd2_extract(path, T=temperature)
            extracted_dfs.append(extracted_df)

        return extracted_dfs

    def _estimate_convergence(self, context: SimulationContext):
        """Internal function to calculate current free energy convergence."""
        extracted_dfs = []
        try:
            extracted_dfs = self._extract_somd2_parquet(context)
        except Exception as e:
            _logger.error(f"Error reading extracted data: {e}")

        if not extracted_dfs:
            raise RuntimeError(
                "No extracted dataframes available for convergence analysis."
            )

        convergence_df = convergence.forward_backward_convergence(
            extracted_dfs, estimator="MBAR"
        )
        converged = self._test_convergence(convergence_df)

        if converged and self.plot_convergence:
            _logger.info("Plotting convergence results")
            sns.set_context("notebook", font_scale=1.5)
            # Now we need to plot:
            # 1. dG convergence
            # 2. Overlap matrix
            # 3. PMF evolution

            # Step 1. Plot dG convergence plot
            _logger.debug("Plotting dG convergence")
            fig, ax = plt.subplots(figsize=(10, 10))
            ax = visualisation.plot_convergence(convergence_df, ax=ax)
            fig.tight_layout()
            fig.savefig(f"{context.somd2_config.output_directory}/convergence_plot.png")

            # Step 2. Plot overlap matrix
            _logger.debug("Plotting overlap matrix")
            fig, ax = plt.subplots(figsize=(10, 10))

            # Concat dataframes for the estimator
            extracted_df = pd.concat(extracted_dfs)
            mbar = estimators.MBAR()
            mbar.fit(extracted_df)
            ax = visualisation.plot_mbar_overlap_matrix(mbar.overlap_matrix, ax=ax)
            ax.set_ylabel(r"$\Delta G$ ({})".format("kT/mol"))
            fig.tight_layout()
            fig.savefig(f"{context.somd2_config.output_directory}/overlap_matrix.png")

            # Step 3. Plot the PMF evolution
            _logger.debug("Plotting PMF evolution")

            # Calculate index length by taking the total df length divide it by the number of lambda windows
            # This assumes that all lambda windows have the same number of samples
            index_length = len(extracted_df.index)
            index_length = int(index_length / len(extracted_dfs))

            fractions = 10
            fraction_values = []
            pmfs = []
            for i in range(1, fractions + 1):
                fraction_value = i / fractions
                subsampled_dfs = []

                samples_drawn = int(index_length * fraction_value)

                # Figure out starting index value for each lambda window
                for j in range(len(extracted_dfs)):
                    start_index = j * index_length
                    end_index = start_index + samples_drawn
                    subsampled_dfs.append(extracted_df.iloc[start_index:end_index])

                # Do dG estimation on the subsampled data
                combined_df = pd.concat(subsampled_dfs)
                mbar = estimators.MBAR()
                mbar.fit(combined_df)

                pmf = mbar.delta_f_.loc[0.0].to_numpy()
                pmfs.append(pmf)
                fraction_values.append(fraction_value)

            pmf_df = pd.DataFrame({"fraction": fraction_values, "pmf": pmfs})

            fig, ax = plt.subplots(figsize=(10, 10))
            for i in range(len(pmf_df)):
                lambda_vals = [i for i in range(len(pmf_df.iloc[i]["pmf"]))]
                sns.lineplot(
                    x=lambda_vals,
                    y=pmf_df.iloc[i]["pmf"],
                    ax=ax,
                    label=f"Fraction {pmf_df.iloc[i]['fraction']}",
                )

            ax.set_title("PMF evolution")
            ax.set_xlabel("Lambda window")
            ax.set_ylabel("PMF (kT/mol)")
            ax.legend()
            fig.tight_layout()
            fig.savefig(f"{context.somd2_config.output_directory}/pmf_evolution.png")

        return converged

    def _test_convergence(self, df):
        estimator_error = df["Forward_Error"].iloc[-1]
        _logger.info(f"Free energy estimator error: {estimator_error:.4f} kT/mol")

        if estimator_error < self.optimization_threshold:
            return True
        else:
            return False

    def _execute(self, context: SimulationContext):
        for _ in range(self.optimization_attempts):
            converged = self._estimate_convergence(context)
            if converged:
                _logger.info("Simulation converged!")
                break
            else:
                old_runtime = context.somd2_config.runtime
                new_runtime = sr.u(old_runtime) + sr.u(self.optimization_runtime)
                _logger.info(f"Extending runtime from {old_runtime} to {new_runtime}")
                context.somd2_config.restart = True
                context.somd2_config.runtime = new_runtime.to_string()
                _run_somd2_workflow(context=context)
