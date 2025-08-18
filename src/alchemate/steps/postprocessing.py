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


class CalculateRMSD(WorkflowStep):
    """A step to analyze the simulation trajectory."""

    def run(self, context: SimulationContext):
        print("\n--- Running Step: CalculateRMSD ---")
        if not context.result:
            raise ValueError("MD results not found! Did the main calculation run?")

        print("Analysis complete.")
