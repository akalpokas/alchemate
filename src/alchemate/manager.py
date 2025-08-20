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

import importlib.metadata
from .steps.base import WorkflowStep

from loguru import logger as _logger


# a helper function to create and display the masthead
def _display_masthead():
    """Fetches the package version and displays a startup masthead."""
    try:
        # fetch the version of the installed package
        version = importlib.metadata.version("alchemate")
    except importlib.metadata.PackageNotFoundError:
        version = "unknown"

    masthead = f"""
+--------------------------------------------------+
|   alchemate:                                     |
|   Modular SOMD2 processing workflows.            |
|   Version: {version:<38}|
+--------------------------------------------------+
"""
    _logger.debug(masthead)


class WorkflowManager:
    def __init__(self, context, workflow_steps: list[WorkflowStep]):
        self.context = context
        self.workflow_steps = workflow_steps

    def execute(self):
        _display_masthead()

        for step in self.workflow_steps:
            try:
                step.run(self.context)
            except Exception as e:
                _logger.error(f"ERROR in step {step.__class__.__name__}: {e}")
                _logger.error("Workflow execution failed.")
                return None

        _logger.success("Workflow finished successfully!")
        return self.context
