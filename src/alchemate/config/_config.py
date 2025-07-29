######################################################################
# alchemate: Modular SOMD2 post-processing workflows
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
# along with SOMD2. If not, see <http://www.gnu.org/licenses/>.
#####################################################################

"""
Configuration class for alchemate
"""

__all__ = ["Config"]

class Config:
    def __init__(
        self,
        log_level="debug",
        workflows=None,
    ):
        self.log_level=log_level
        self.workflows=workflows
        
    @property
    def log_level(self):
        return self._log_level

    @log_level.setter
    def log_level(self, value):
        self._log_level = value

    @property
    def workflows(self):
        return self._workflows

    @workflows.setter
    def workflows(self, value):
        # Verify a list of strings is provided
        if value is not None:
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                raise ValueError("Workflows must be a list of strings.")
        
        self._workflows = value