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

import pickle
from types import SimpleNamespace
from somd2.config import Config as _somd2_config


class SimulationContext:
    """A simple data bucket for passing along information through workflows."""

    _mutable_attrs = [
        "system",
        "somd2_config",
        "results",
    ]

    def __init__(self, system, somd2_config):
        """Initializes the context and its mutable attributes."""

        # Flag for locking the instance
        self._initialized = False

        # Perform input validation
        if not isinstance(somd2_config, type(_somd2_config())):
            raise TypeError(
                f"Expected somd2_config to be an instance of {_somd2_config}, got {type(somd2_config)}"
            )

        # Define mutable attributes
        self.system = system
        self.somd2_config = somd2_config
        self.results = SimpleNamespace()  # to allow dynamic attribute assignment, i.e. self.results.new_attribute = value

        # Lock the instance to prevent further modifications outside mutable properties
        self._initialized = True

    def __setattr__(self, name, value) -> None:
        """Override attribute setting to enforce immutability."""
        is_initialized = hasattr(self, "_initialized") and self._initialized
        if is_initialized and name not in self._mutable_attrs:
            raise AttributeError(
                f"'{type(self).__name__}' attribute '{name}' is immutable. "
                "Use the 'results' property for storing new data."
            )

        # If everything is fine, set the attribute
        super().__setattr__(name, value)

    def save(self):
        """Save context to a file."""
        with open(
            f"{self.somd2_config.output_directory}/alchemate_context.pkl", "wb"
        ) as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path):
        """Load context from a file."""
        with open(path, "rb") as f:
            return pickle.load(f)
