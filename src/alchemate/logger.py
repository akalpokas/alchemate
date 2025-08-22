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

import logging
from colorlog import ColoredFormatter
import sys


def setup_logging(log_path=None):
    # Main runtime logger will be alchemate.logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Prevent messages from propagating to the root logger
    logger.propagate = False

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create a file handler
    if log_path:
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.DEBUG)
        formatter = ColoredFormatter(
            "{asctime} {levelname} alchemate:{module}:{funcName}:{lineno} {message}",
            reset=False,
            secondary_log_colors={},
            style="{",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Create a console handler
    handler = logging.StreamHandler(sys.stdout)
    formatter = ColoredFormatter(
        "{green}{asctime} {log_color} {levelname} {cyan} alchemate:{module}:{funcName}:{lineno}{log_color} {message}",
        reset=True,
        log_colors={
            "DEBUG": "blue",
            "INFO": "white",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
        secondary_log_colors={},
        style="{",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Get the root logger and remove any handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    # Add a NullHandler to effectively disable it
    root_logger.addHandler(logging.NullHandler())

    return logger
