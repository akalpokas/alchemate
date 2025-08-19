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
from ._run_somd2 import _run_somd2_workflow


# Template class for all processing steps.
class WorkflowStep(ABC):
    """Base class for all workflow steps."""

    @abstractmethod
    def run(self, context: SimulationContext):
        """Runs the workflow step."""


# THE MAIN CALCULATION STEP (A WRAPPER)
class RunBasicCalculation(WorkflowStep):
    """A step to run the external MD engine."""

    def run(self, context: SimulationContext):
        _run_somd2_workflow(context=context)
