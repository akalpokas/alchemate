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

from somd2.config import Config as _somd2_config


# A simple data bucket for passing along information through workflows.
class SimulationContext:
    def __init__(self, system, somd2_config):
        self.system = system

        # Check type of somd2_config
        if not isinstance(somd2_config, type(_somd2_config())):
            raise TypeError(
                f"Expected somd2_config to be an instance of {_somd2_config}, got {type(somd2_config)}"
            )

        self.somd2_config = somd2_config
        self.preprocess_parameters = {}
        self.postprocess_parameters = {}
        self.analysis_output = None
        self.result = None
