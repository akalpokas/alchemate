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
from .context import SimulationContext
from .steps.base import WorkflowStep


# A helper function to create and display the masthead
def _display_masthead(package_name: str):
    """Fetches the package version and displays a startup masthead."""
    try:
        # Fetch the version of the installed package
        version = importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        version = "unknown"

    masthead = f"""
+--------------------------------------------------+
|   alchemate:                                     |
|   Modular SOMD2 processing workflows.            |
|   Version: {version:<38}|
+--------------------------------------------------+
"""
    print(masthead)


class WorkflowManager:
    def __init__(self, workflow_steps: list[WorkflowStep]):
        self.workflow_steps = workflow_steps

    def execute(self, system: str, somd2_config):
        _display_masthead(package_name="alchemate")

        context = SimulationContext(system=system, somd2_config=somd2_config)

        for step in self.workflow_steps:
            try:
                step.run(context)
            except Exception as e:
                print(f"ERROR in step {step.__class__.__name__}: {e}")
                print("Workflow halted.")
                return None  # Or handle the error more gracefully

        print("\nWorkflow finished successfully!")
        return context
