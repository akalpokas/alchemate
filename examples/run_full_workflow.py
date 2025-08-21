from somd2.config import Config as somd2_config
from alchemate.manager import WorkflowManager
from alchemate.context import SimulationContext
from alchemate.steps.base import RunBasicCalculation
from alchemate.steps.postprocessing import OptimizeConvergence

somd2_config = somd2_config()
somd2_config.cutoff_type = "RF"
somd2_config.cutoff = "12A"
somd2_config.runtime = "100ps"
somd2_config.replica_exchange = True

context = SimulationContext(system="merged_molecule.s3", somd2_config=somd2_config)

simulation_workflow = [
    RunBasicCalculation(),
    OptimizeConvergence(),
]

manager = WorkflowManager(context=context, workflow_steps=simulation_workflow)
final_context = manager.execute()

# Access the final context for all of the results.
if final_context:
    print("\n--- Final Results ---")
    print(f"Final analysis results: {final_context.results}")
