import pytest
from unittest.mock import Mock, patch
from queue import Empty
from alchemate.steps._run_somd2 import _run_somd2_workflow
from alchemate.context import SimulationContext


class TestRunSomd2Workflow:
    @pytest.fixture
    def mock_context(self):
        context = Mock(spec=SimulationContext)
        context.somd2_config = Mock()
        context.system = Mock()
        return context

    @patch("alchemate.steps._run_somd2.multiprocessing.Process")
    @patch("alchemate.steps._run_somd2.multiprocessing.Queue")
    def test_successful_execution_first_attempt(
        self, mock_queue_class, mock_process_class, mock_context
    ):
        # Setup
        mock_queue = Mock()
        mock_queue.get.return_value = {"success": True}
        mock_queue_class.return_value = mock_queue

        mock_process = Mock()
        mock_process.pid = 12345
        mock_process_class.return_value = mock_process

        # Execute
        _run_somd2_workflow(mock_context)

        # Assert
        mock_process.start.assert_called_once()
        mock_process.join.assert_called_once()
        mock_queue.get.assert_called_once_with(timeout=10)
        assert mock_context.somd2_config.restart is False

    @patch("alchemate.steps._run_somd2.multiprocessing.Process")
    @patch("alchemate.steps._run_somd2.multiprocessing.Queue")
    def test_hard_restart_after_error(
        self, mock_queue_class, mock_process_class, mock_context
    ):
        # Setup
        mock_queue = Mock()
        mock_queue.get.side_effect = [
            {"error": "Test error"},  # First hard attempt fails
            {"success": True},  # Second hard attempt succeeds
        ]
        mock_queue_class.return_value = mock_queue

        mock_process = Mock()
        mock_process.pid = 12345
        mock_process_class.return_value = mock_process

        # Execute
        _run_somd2_workflow(mock_context, max_hard_restarts=2, max_soft_restarts=1)

        # Assert
        assert mock_process.start.call_count == 2
        assert mock_process.join.call_count == 2

    @patch("alchemate.steps._run_somd2.multiprocessing.Process")
    @patch("alchemate.steps._run_somd2.multiprocessing.Queue")
    def test_soft_restart_success(
        self, mock_queue_class, mock_process_class, mock_context
    ):
        # Setup
        mock_queue = Mock()
        mock_queue.get.side_effect = [
            {"error": "Test error"},  # Hard attempt fails
            {"success": True},  # Soft restart succeeds
        ]
        mock_queue_class.return_value = mock_queue

        mock_process = Mock()
        mock_process.pid = 12345
        mock_process_class.return_value = mock_process

        # Execute
        _run_somd2_workflow(mock_context, max_hard_restarts=1, max_soft_restarts=2)

        # Assert
        assert mock_process.start.call_count == 2
        # Verify restart flag is set for soft restart
        assert mock_context.somd2_config.restart is True

    @patch("alchemate.steps._run_somd2.multiprocessing.Process")
    @patch("alchemate.steps._run_somd2.multiprocessing.Queue")
    def test_all_attempts_fail_raises_runtime_error(
        self, mock_queue_class, mock_process_class, mock_context
    ):
        # Setup
        mock_queue = Mock()
        mock_queue.get.return_value = {"error": "Persistent error"}
        mock_queue_class.return_value = mock_queue

        mock_process = Mock()
        mock_process.pid = 12345
        mock_process_class.return_value = mock_process

        # Execute & Assert
        with pytest.raises(
            RuntimeError, match="SOMD2 workflow failed after multiple attempts"
        ):
            _run_somd2_workflow(mock_context, max_hard_restarts=1, max_soft_restarts=1)

    @patch("alchemate.steps._run_somd2.multiprocessing.Process")
    @patch("alchemate.steps._run_somd2.multiprocessing.Queue")
    def test_queue_timeout_handling(
        self, mock_queue_class, mock_process_class, mock_context
    ):
        # Setup
        mock_queue = Mock()
        mock_queue.get.side_effect = [
            {"error": "Test error"},  # Hard attempt fails
            Empty(),  # Soft restart times out
            {"success": True},  # Next soft restart succeeds
        ]
        mock_queue_class.return_value = mock_queue

        mock_process = Mock()
        mock_process.pid = 12345
        mock_process_class.return_value = mock_process

        # Execute
        _run_somd2_workflow(mock_context, max_hard_restarts=1, max_soft_restarts=3)

        # Assert
        assert mock_process.start.call_count == 3

    @patch("alchemate.steps._run_somd2.multiprocessing.Process")
    @patch("alchemate.steps._run_somd2.multiprocessing.Queue")
    def test_custom_restart_limits(
        self, mock_queue_class, mock_process_class, mock_context
    ):
        # Setup
        mock_queue = Mock()
        mock_queue.get.return_value = {"error": "Test error"}
        mock_queue_class.return_value = mock_queue

        mock_process = Mock()
        mock_process_class.return_value = mock_process

        # Execute & Assert
        with pytest.raises(RuntimeError):
            _run_somd2_workflow(mock_context, max_hard_restarts=2, max_soft_restarts=3)

        # Should have 2 hard attempts, each with 3 soft attempts = 2 + (2 * 3) = 8 total
        assert mock_process.start.call_count == 8
