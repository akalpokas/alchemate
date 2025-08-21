import pytest
from somd2.config import Config as somd2_config
from alchemate.context import SimulationContext


@pytest.fixture
def mock_context(tmp_path):
    context = SimulationContext(system="mock_system", somd2_config=somd2_config())
    context.somd2_config.cutoff = "14A"
    context.somd2_config.num_lambda = 21
    context.somd2_config.output_directory = tmp_path
    return context


@pytest.mark.xfail(
    reason="This test is expected to fail as it tries to modify immutable properties of SimulationContext class"
)
def test_immutable_properties(mock_context):
    with pytest.raises(AttributeError):
        mock_context.foo = "bar"


def test_saving_and_loading(tmp_path, mock_context):
    mock_context.save()
    loaded_context = SimulationContext.load(f"{tmp_path}/alchemate_context.pkl")

    assert loaded_context.system == mock_context.system
    assert loaded_context.somd2_config.cutoff == mock_context.somd2_config.cutoff
    assert (
        loaded_context.somd2_config.num_lambda == mock_context.somd2_config.num_lambda
    )
    assert (
        loaded_context.somd2_config.output_directory
        == mock_context.somd2_config.output_directory
    )
