import somd2
from alchemate.manager import WorkflowManager

# Import the modular workflows you need for the calculation
from alchemate.steps.preprocessing import PrepareSystem
from alchemate.steps.base import RunMockCalculation
from alchemate.steps.postprocessing import CalculateRMSD

# Supress userwarnings
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

# Define SOMD2 configuration for setting up the physical simultion (PME, cutoff, timestep, etc.)
somd2_config = somd2.config.Config()

if __name__ == "__main__":

    # Define the desired workflow
    simulation_workflow = [
        PrepareSystem(),
        RunMockCalculation(),
        CalculateRMSD(),
    ]

    # Create the manager with this workflow
    manager = WorkflowManager(workflow_steps=simulation_workflow)

    # Run everything
    final_context = manager.execute(
        system="merged_molecule.s3", somd2_config=somd2_config
    )

    # Access the final context for all of the results.
    if final_context:
        print("\n--- Final Results ---")
        print(f"Final analysis output: {final_context.analysis_output}")
