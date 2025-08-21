import pytest
from somd2.config import Config as somd2_config
from alchemate.context import SimulationContext


@pytest.fixture
def dummy_context(tmp_path):
    context = SimulationContext(system="dummy_system", somd2_config=somd2_config())
    context.somd2_config.cutoff = "14A"
    context.somd2_config.num_lambda = 21
    context.somd2_config.output_directory = tmp_path
    return context


def test_saving_and_loading(tmp_path, dummy_context):
    dummy_context.save()
    loaded_context = SimulationContext.load(f"{tmp_path}/alchemate_context.pkl")

    assert loaded_context.system == dummy_context.system
    assert loaded_context.somd2_config.cutoff == dummy_context.somd2_config.cutoff
    assert (
        loaded_context.somd2_config.num_lambda == dummy_context.somd2_config.num_lambda
    )
    assert (
        loaded_context.somd2_config.output_directory
        == dummy_context.somd2_config.output_directory
    )
