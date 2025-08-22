from somd2.config import Config as somd2_config
from alchemate.manager import WorkflowManager
from alchemate.context import SimulationContext
from alchemate.steps.preprocessing import OptimizeExchangeProbabilities
from alchemate.logger import setup_logging

somd2_config = somd2_config()
somd2_config.cutoff_type = "RF"
somd2_config.cutoff = "12A"
somd2_config.num_lambda = 4
somd2_config.replica_exchange = True
somd2_config.log_level = "debug"

context = SimulationContext(system="merged_molecule.s3", somd2_config=somd2_config)

setup_logging(log_path=f"{context.somd2_config.output_directory}/alchemate.log")

simulation_workflow = [
    OptimizeExchangeProbabilities(optimization_runtime="100ps"),
]

manager = WorkflowManager(context=context, workflow_steps=simulation_workflow)
final_context = manager.execute()

# Access the final context for all of the results.
if final_context:
    print("\n--- Final Results ---")
    print(f"Final analysis results: {final_context.results}")
