import pytest
from somd2.config import Config as somd2_config
from alchemate.manager import WorkflowManager
from alchemate.steps.base import WorkflowStep
from alchemate.context import SimulationContext


@pytest.fixture
def mock_context(tmp_path):
    """Basic context fixture."""
    context = SimulationContext(system="dummy_system", somd2_config=somd2_config())
    context.somd2_config.output_directory = tmp_path
    return context


class MockStepOne(WorkflowStep):
    """A fake step that adds a property to the context."""

    def _execute(self, context: SimulationContext):
        print("Running MockStepOne")


class MockStepTwo(WorkflowStep):
    """A fake step that checks for the property from step one."""

    def _execute(self, context: SimulationContext):
        print("Running MockStepTwo")


class MockStepWithError(WorkflowStep):
    """A fake step that is designed to fail."""

    def _execute(self, context: SimulationContext):
        print("Running MockStepWithError")
        raise ValueError("An error occurred")


def test_workflow_manager_successful_execution(mock_context):
    """
    Tests a complete, successful workflow run.
    """

    # Create our test workflow and the manager
    test_workflow = [MockStepOne(), MockStepTwo()]
    manager = WorkflowManager(context=mock_context, workflow_steps=test_workflow)

    # ACT
    final_context = manager.execute()

    # Check that the workflow completed successfully
    assert final_context is not None

    # Check that the completion was recorded correctly
    assert "MockStepOne" in final_context.completed_steps
    assert "MockStepTwo" in final_context.completed_steps


def test_workflow_manager_stops_on_error(mock_context):
    """
    Tests that the workflow halts gracefully when a step fails.
    """

    # This workflow includes a step that will raise an error
    test_workflow = [MockStepOne(), MockStepWithError(), MockStepTwo()]
    manager = WorkflowManager(context=mock_context, workflow_steps=test_workflow)

    # ACT
    final_context = manager.execute()

    # ASSERT
    # Check that the workflow was halted and returned None
    assert final_context is None
