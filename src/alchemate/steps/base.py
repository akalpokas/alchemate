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

from abc import ABC, abstractmethod
from ..context import SimulationContext

# Template class for all processing steps.
class WorkflowStep(ABC):
    @abstractmethod
    def run(self, context: SimulationContext):
        """Runs the workflow step."""
        pass

# THE MAIN CALCULATION STEP (A WRAPPER)
class RunMainCalculation(WorkflowStep):
    """A step to run the external MD engine."""
    def run(self, context: SimulationContext):
        print("\n--- Running Step: RunMainCalculation ---")
        if not context.preprocess_parameters:
            raise ValueError("Parameters not found in context! Did PrepareSystem run?")
        
        # 1. Get params from context
        engine_params = context.preprocess_parameters

        # 2. Call the external API
        # md_engine = SomeMDEngine(params=engine_params)
        # results = md_engine.run_simulation()
        results = "Testing"
        
        # 3. Store results back into the context
        context.md_results = results
        print("MD results stored in context.")
