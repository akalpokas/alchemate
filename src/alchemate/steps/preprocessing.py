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

class PrepareSystem(WorkflowStep):
    """A step to set up simulation parameters."""
    def run(self, context: SimulationContext):
        print("\n--- Running Step: PrepareSystem ---")
        print(f"Reading from {context.input_file} to determine parameters.")
        # This step's logic would go here. For now, we'll just add some params.
        context.preprocess_parameters["temperature"] = 300  # in Kelvin
        context.preprocess_parameters["box_size"] = (10, 10, 10) # in Angstroms
        print("System parameters prepared and added to context.")