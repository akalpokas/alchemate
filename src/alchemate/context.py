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

from loguru import logger

# A simple data bucket for passing along information through workflows.
class SimulationContext:
    def __init__(self, input_file, somd2_config):
        self.input_file = input_file
        self.somd2_config = somd2_config
        self.preprocess_parameters = {}
        self.postprocess_parameters = {}
        self.analysis_output = None
        logger.debug(f"SimulationContext initialized with input file: {input_file} and SOMD2 config: {somd2_config}")