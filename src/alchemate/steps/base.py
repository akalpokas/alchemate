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
    """
    Base class for all workflow steps in a simulation workflow.

    This abstract class defines the interface and common behavior for workflow steps.
    Subclasses must implement the `_execute` method, which contains the main logic for the step.

    Methods
    -------
    run(context: SimulationContext)
        Executes the workflow step by calling the subclass-defined `_execute` method,
        and marks the step as completed in the provided context.

    _execute(context: SimulationContext)
        Abstract method to be implemented by subclasses. Contains the main logic for the workflow step.

    Attributes
    ----------
    None defined in the base class.
    """

    def __init__(
        self,
        independent: bool = False,
    ) -> None:
        self._independent = independent

    def is_independent(self) -> bool:
        """Indicates whether the step is independent, i.e. will run in its own sub-directory."""
        return self._independent

    def run(self, context: SimulationContext):
        """Runs the workflow step."""

        # Carry out the main logic for the step
        self._execute(context)

        # Mark step as completed
        step_name = self.__class__.__name__
        context.completed_steps.add(step_name)

    @abstractmethod
    def _execute(self, context: SimulationContext):
        """Executes the main logic for the workflow step. Implemented in subclasses."""


class RunBasicCalculation(WorkflowStep):
    """A step to run a basic SOMD2 calculation."""

    def __init__(
        self,
        independent: bool = False,
        calculation_runtime: str = "5000ps",
    ) -> None:
        super().__init__(independent=independent)

        self.calculation_runtime: str = calculation_runtime

    def _execute(self, context: SimulationContext):
        context.somd2_config.runtime = self.calculation_runtime
        _run_somd2_workflow(context=context)
