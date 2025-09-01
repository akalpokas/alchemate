import pytest
import tempfile
import sire as sr
import somd2
from somd2.config import Config
from alchemate.context import SimulationContext


@pytest.fixture
def mock_context(tmp_path):
    context = SimulationContext(system="mock_system", somd2_config=Config())
    context.somd2_config.cutoff = "14A"
    context.somd2_config.num_lambda = 21
    context.somd2_config.output_directory = tmp_path
    return context


def test_immutable_properties(mock_context):
    with pytest.raises(AttributeError):
        mock_context.foo = "bar"


def test_pickle_saving_and_loading(tmp_path, mock_context):
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


def test_rebuilding_from_previous_somd2_output(tmp_path):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a SOMD2 output directory to mimick a previously ran simulation
        merged_mols = sr.load(sr.expand(sr.tutorial_url, "merged_molecule.s3"))
        config = Config(platform="cpu", output_directory=tmpdir, cutoff="14A")
        _ = somd2.runner.Runner(merged_mols, config)

        # Now test the alchemate SimulationContext can be rebuilt from the SOMD2 output
        somd2_config = Config().from_yaml(f"{tmpdir}/config.yaml")

        context = SimulationContext(
            system="merged_molecule.s3", somd2_config=somd2_config
        )

        assert context.somd2_config.cutoff == "14A"
