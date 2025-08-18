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

from alchemate.context import SimulationContext
import somd2


def _run_somd2_workflow(context: SimulationContext):
    "Wrapper function to run the SOMD2 workflow."
    runner = somd2.runner.RepexRunner(
        config=context.somd2_config, system=context.system
    )
    print(runner)
    try:
        runner.run()
    except Exception as e:
        print(f"Error occurred while running SOMD2 workflow: {e}")
