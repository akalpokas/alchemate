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
from alchemlyb import convergence, visualisation, estimators, preprocessing
from alchemlyb.postprocessors.units import to_kcalmol
import matplotlib.pyplot as plt
import pandas as pd
import sire as sr
import seaborn as sns
import numpy as np
import json

from rich.console import Console
from rich.table import Table

from .base import WorkflowStep
from ..context import SimulationContext
from ._run_somd2 import _run_somd2_workflow

_logger = logging.getLogger("alchemate.logger")


class OptimizeConvergence(WorkflowStep):
    """
    Workflow step for optimizing the convergence of free energy calculations.

    This class attempts to ensure that the free energy convergence heuristics fall below a specified threshold
    by repeatedly extending the simulation runtime and re-evaluating convergence. It extracts energy data
    from SOMD2 parquet files, estimates convergence using the MBAR estimator, and manages simulation restarts.

    Attributes
    ----------
    optimization_attempts (int): Maximum number of optimization attempts to achieve convergence.
    optimization_heuristics (dict): Heuristics for determining convergence (e.g., estimator error) and their thresholds.
    optimization_runtime (str): Amount of simulation time to add per optimization attempt.
    plot_convergence (bool): Whether to plot convergence results.

    Methods
    -------
    _extract_somd2_parquet(context):
        Extracts energy data from SOMD2 parquet files in the simulation output directory.

    _estimate_convergence(context):
        Calculates current free energy convergence using extracted data and MBAR estimator.

    _test_for_convergence(df):
        Tests if the estimator error in the provided DataFrame is below the optimization threshold.

    _compute_heuristics(convergence_df):
        Calculates various heuristics from the provided alchemlyb convergence DataFrame.

    _execute(context):
        Runs the optimization loop, extending simulation runtime and restarting as needed until
        convergence is achieved or the maximum number of attempts is reached.
    """

    def __init__(
        self,
        optimization_attempts: int = 3,
        optimization_heuristics: dict = None,
        optimization_runtime: str = "1000ps",
        plot_convergence: bool = True,
    ) -> None:
        super().__init__()

        if optimization_heuristics is None:
            optimization_heuristics = {"estimator_error": 0.05, "dg_slope": 0.25}
        self.optimization_attempts: int = optimization_attempts
        self.optimization_heuristics: dict = optimization_heuristics
        self.optimization_runtime: str = optimization_runtime
        self.estimated_heuristics = None
        self.estimated_decorr_heuristics = None
        self.dg_estimate = None
        self.decorr_dg_estimate = None
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

    def _compute_heuristics(self, convergence_df: pd.DataFrame) -> dict:
        """Estimate heuristics from the provided DataFrame."""
        implemented_heuristics = ["estimator_error", "dg_slope"]
        heuristics = {}

        _logger.debug(f"Convergence dataframe:\n {convergence_df}")

        for key, threshold in self.optimization_heuristics.items():
            if key not in implemented_heuristics:
                raise NotImplementedError(f"Heuristic {key} is not implemented.")

            if key == "estimator_error":
                _logger.debug("Calculating estimator error heuristic")
                estimator_error = convergence_df["Forward_Error"].iloc[-1]
                _logger.info(
                    f"Free energy estimator error: {estimator_error:.4f} kcal/mol"
                )
                heuristics[key] = estimator_error

            if key == "dg_slope":
                _logger.debug("Calculating dG slope heuristic")
                try:
                    forward_1 = convergence_df.loc[
                        convergence_df["data_fraction"] == 1.0, "Forward"
                    ]
                    forward_05 = convergence_df.loc[
                        convergence_df["data_fraction"] == 0.5, "Forward"
                    ]
                    if forward_1.empty or forward_05.empty:
                        raise ValueError(
                            "Required data_fraction values (1.0 and/or 0.5) are missing in convergence_df."
                        )
                    dg_slope = forward_1.to_numpy()[0] - forward_05.to_numpy()[0]
                    dg_slope = np.absolute(dg_slope)
                    _logger.info(f"dG slope: {dg_slope:.4f} kcal/mol")
                    heuristics[key] = dg_slope
                except Exception as e:
                    _logger.error(f"Error calculating dG slope heuristic: {e}")
                    heuristics[key] = np.nan
                    _logger.info(f"dG slope: {dg_slope:.4f} kcal/mol")
                    heuristics[key] = dg_slope

        return heuristics

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

        # Perform decorrelation analysis
        extracted_decorrelated_dfs = [
            preprocessing.decorrelate_u_nk(df) for df in extracted_dfs
        ]

        convergence_df = convergence.forward_backward_convergence(
            extracted_dfs, estimator="MBAR"
        )
        try:
            convergence_decorrelated_df = convergence.forward_backward_convergence(
                extracted_decorrelated_dfs, estimator="MBAR"
            )
        except ValueError as e:
            _logger.error(f"Error in decorrelated convergence calculation: {e}")
            _logger.error("Falling back to using original convergence data.")
            convergence_decorrelated_df = convergence_df.copy()

        # Need to retain data_fraction as the as to_kcalmol function will also convert it
        data_fraction = convergence_df["data_fraction"].copy()
        convergence_df = to_kcalmol(convergence_df)

        # Reinsert the datafraction
        convergence_df["data_fraction"] = data_fraction
        convergence_decorrelated_df = to_kcalmol(convergence_decorrelated_df)
        convergence_decorrelated_df["data_fraction"] = data_fraction

        # Retrieve and store current dG values
        self.dg_estimate = convergence_df["Forward"].iloc[-1]
        self.decorr_dg_estimate = convergence_decorrelated_df["Forward"].iloc[-1]

        _logger.info("Computing heuristics for the unprocessed data")
        estimated_heuristics = self._compute_heuristics(convergence_df)
        self.estimated_heuristics = estimated_heuristics
        _logger.info("Computing heuristics for the decorrelated data")
        estimated_decorr_heuristics = self._compute_heuristics(
            convergence_decorrelated_df
        )
        self.estimated_decorr_heuristics = estimated_decorr_heuristics

        # Compare the calculated heuristics with user-defined thresholds here
        converged = self._test_for_convergence(estimated_heuristics)

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
            ax.set_ylabel(r"$\Delta G$ (kcal/mol)")
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

                # Convert to kcal/mol
                delta_f_ = to_kcalmol(mbar.delta_f_)
                pmf = delta_f_.loc[0.0].to_numpy()
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
            ax.set_ylabel("PMF (kcal/mol)")
            ax.legend()
            fig.tight_layout()
            fig.savefig(f"{context.somd2_config.output_directory}/pmf_evolution.png")

        return converged

    def _test_for_convergence(self, heuristics):
        """Test function for comparing provided heuristics with self.optimization_heuristics"""

        # Check if all heuristics are satisfied with self.optimization_heuristics
        for heuristic, value in heuristics.items():
            _logger.debug(
                f"Testing heuristic '{heuristic}': {value} > {self.optimization_heuristics[heuristic]}"
            )
            if value > self.optimization_heuristics[heuristic]:
                _logger.debug(f"Heuristic '{heuristic}' not satisfied")
                return False

        return True

    def _execute(self, context: SimulationContext):
        for _ in range(self.optimization_attempts):
            converged = self._estimate_convergence(context)
            if converged:
                _logger.info("Simulation converged!")

                # Print the convergence results to a table
                table = Table(title="Convergence Results")
                table.add_column("Metric", justify="right", style="cyan", no_wrap=True)
                table.add_column("Value (kcal/mol)", justify="right", style="green")
                table.add_row("dG", str(round(self.dg_estimate, ndigits=2)))
                for heuristic, value in self.estimated_heuristics.items():
                    table.add_row(heuristic, str(round(value, ndigits=2)))
                console = Console()
                console.print(table)

                # Print the decorrelated convergence results to a table
                table = Table(title="Decorrelated Convergence Results")
                table.add_column("Metric", justify="right", style="cyan", no_wrap=True)
                table.add_column("Value (kcal/mol)", justify="right", style="green")
                table.add_row("dG", str(round(self.decorr_dg_estimate, ndigits=2)))
                for heuristic, value in self.estimated_decorr_heuristics.items():
                    table.add_row(heuristic, str(round(value, ndigits=2)))
                console = Console()
                console.print(table)

                # store the results as a json
                results = {
                    "correlated": {
                        "dG": round(self.dg_estimate, ndigits=2),
                        **{
                            heuristic: round(value, ndigits=2)
                            for heuristic, value in self.estimated_heuristics.items()
                        },
                    },
                    "decorrelated": {
                        "dG": round(self.decorr_dg_estimate, ndigits=2),
                        **{
                            heuristic: round(value, ndigits=2)
                            for heuristic, value in self.estimated_decorr_heuristics.items()
                        },
                    },
                }
                with open(
                    f"{context.somd2_config.output_directory}/convergence_results.json",
                    "w",
                ) as f:
                    json.dump(results, f)

                break

            else:
                old_runtime = context.somd2_config.runtime
                new_runtime = sr.u(old_runtime) + sr.u(self.optimization_runtime)
                _logger.info(f"Extending runtime from {old_runtime} to {new_runtime}")
                context.somd2_config.restart = True
                context.somd2_config.runtime = new_runtime.to_string()
                _run_somd2_workflow(context=context)
