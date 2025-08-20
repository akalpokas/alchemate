from somd2.config import Config as somd2_config
from alchemate.manager import WorkflowManager
from alchemate.context import SimulationContext


# Import the modular workflows you need for the calculation
from alchemate.steps.preprocessing import OptimizeExchangeProbabilities

# Define SOMD2 configuration for setting up the physical simultion (PME, cutoff, timestep, etc.)
somd2_config = somd2_config()
somd2_config.cutoff_type = "PME"
somd2_config.cutoff = "14A"
somd2_config.replica_exchange = True
somd2_config.log_level = "debug"


if __name__ == "__main__":
    # Define the desired workflow
    simulation_workflow = [
        OptimizeExchangeProbabilities(),
    ]

    context = SimulationContext(system="merged_molecule.s3", somd2_config=somd2_config)

    # Create the manager with this workflow
    manager = WorkflowManager(context=context, workflow_steps=simulation_workflow)

    # Run everything
    final_context = manager.execute()

    # Access the final context for all of the results.
    if final_context:
        print("\n--- Final Results ---")
        print(f"Final analysis output: {final_context.analysis_output}")
