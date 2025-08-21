from somd2.config import Config as somd2_config
from alchemate.manager import WorkflowManager
from alchemate.context import SimulationContext
from alchemate.steps.preprocessing import OptimizeExchangeProbabilities

somd2_config = somd2_config()
somd2_config.cutoff_type = "PME"
somd2_config.cutoff = "14A"
somd2_config.replica_exchange = True
somd2_config.log_level = "debug"

context = SimulationContext(system="merged_molecule.s3", somd2_config=somd2_config)

simulation_workflow = [
    OptimizeExchangeProbabilities(),
]

manager = WorkflowManager(context=context, workflow_steps=simulation_workflow)
final_context = manager.execute()

# Access the final context for all of the results.
if final_context:
    print("\n--- Final Results ---")
    print(f"Final analysis results: {final_context.results}")
