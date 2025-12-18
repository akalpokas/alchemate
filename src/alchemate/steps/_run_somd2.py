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
import traceback
import multiprocessing
import somd2

from ..context import SimulationContext

_logger = logging.getLogger("alchemate.logger")


def _run_somd2_workflow(
    context: SimulationContext, max_hard_restarts: int = 3, max_soft_restarts: int = 5
):
    """Internal function to run a SOMD2 workflow. Handles the isolated process running and queuing of child SOMD2 processes.

    Args:
        context : SimulationContext
            The simulation context containing the SOMD2 configuration, system, and other
            necessary parameters for running the workflow.
        max_hard_restarts : int, default=3
            Maximum number of hard restart attempts. Hard restarts run the workflow from
            scratch without attempting to resume from a previous state.
        max_soft_restarts : int, default=5
            Maximum number of soft restart attempts per hard restart cycle. Soft restarts
            attempt to resume the workflow from its last checkpoint or saved state.

    Notes:

        This function is designed to be resilient to SOMD2 failures by implementing both hard and soft restart strategies.
        Under the hood this happens:
        1. We enter a hard restart loop, where we will not attempt to restart a failed workflow, we will simply
        try to run it again from scratch.
        2. If a workflow fails for some reason, we will enter the soft restart loop, where we will attempt to
        restart the workflow. This is important in case we finished a substantial part of the workflow before the failure.
        3. If we exhaust all soft restart attempts, we will return to the hard restart loop.
        4. If we exhaust all hard restart attempts, we will give up and return an error.
        The function utilizes multiprocessing to run the SOMD2 workflow in an isolated process, allowing for better error handling and recovery.
    """

    result_queue = multiprocessing.Queue()

    _logger.debug(f"Provided somd2_config: {context.somd2_config}")

    # 1. Begin hard restart loop, here we will not attempt to restart a failed workflow, we will simply
    # try to run it again from scratch
    for hard_attempt in range(max_hard_restarts):
        _logger.debug(f"Starting hard attempt {hard_attempt + 1}/{max_hard_restarts}")

        context.somd2_config.restart = False

        # TODO: Need to think how to handle overwritting for certain workflows

        # Create a process object for the SOMD2 workflow
        process = multiprocessing.Process(
            target=_run_somd2_process, args=(context, result_queue)
        )
        process.start()

        _logger.debug(f"Process started with PID: {process.pid}")

        # Wait for the process to complete, without timeout
        process.join()

        _logger.debug(f"Process with PID {process.pid} has completed.")
        # Add a timeout here, in case we cannot access the result
        result = result_queue.get(timeout=10)

        # 2. If the result contains an error, enter the soft restart loop
        if "error" in result:
            _logger.error(
                f"Error occurred while running SOMD2 workflow: {result['error']}"
            )
            _logger.error(traceback.format_exc())

            # Begin soft restart loop, here we will try to restart a failed workflow
            for soft_attempt in range(max_soft_restarts):
                _logger.debug(
                    f"Starting soft attempt {soft_attempt + 1}/{max_soft_restarts}"
                )

                context.somd2_config.restart = True

                process = multiprocessing.Process(
                    target=_run_somd2_process, args=(context, result_queue)
                )
                process.start()
                _logger.debug(f"Process started with PID: {process.pid}")
                process.join()
                _logger.debug(f"Process with PID {process.pid} has completed.")

                try:
                    result = result_queue.get(timeout=10)
                except Exception as e:
                    _logger.error(f"SOMD2 workflow timed out: {e}")
                    continue

                if "error" in result:
                    _logger.error(
                        f"Error occurred while running SOMD2 workflow: {result['error']}"
                    )
                    _logger.error(traceback.format_exc())

                    # 3. Continue soft restart attempts
                    continue
                else:
                    _logger.info("SOMD2 workflow completed successfully.")
                    return

        elif "success" in result:
            _logger.info("SOMD2 workflow completed successfully.")
            return

    # 4. If we reach here, it means every attempt has failed
    _logger.error("All attempts to run SOMD2 workflow have failed.")
    raise RuntimeError("SOMD2 workflow failed after multiple attempts.")


def _run_somd2_process(context: SimulationContext, result_queue: multiprocessing.Queue):
    """
    Execute SOMD2 simulation in an isolated process.

    Args:
        context (SimulationContext): Contains the SOMD2 configuration and system setup
            required for the simulation, including somd2_config and system attributes.
        result_queue (multiprocessing.Queue): Queue for inter-process communication to
            return simulation results or error information to the parent process.

    Note:
        This function is designed to be used with multiprocessing and should not be
        called directly. It handles all exceptions internally to prevent process crashes.
    """
    runner = somd2.runner.RepexRunner(
        config=context.somd2_config, system=context.system
    )
    _logger.debug(f"Initialized runner with: {runner}")
    try:
        runner.run()
        result_queue.put({"success": True})

    except Exception as e:
        _logger.error(f"Error occurred while running SOMD2 workflow: {e}")
        _logger.error(traceback.format_exc())
        result_queue.put({"error": str(e)})
