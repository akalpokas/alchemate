import pytest
from somd2.config import Config as somd2_config
from alchemate.steps.postprocessing import OptimizeConvergence
from alchemate.context import SimulationContext


@pytest.fixture
def mock_context():
    context = SimulationContext(system="mock_system", somd2_config=somd2_config())
    return context


@pytest.fixture
def good_convergence_data():
    """
    Generate a dictionary with good convergence data, i.e. in the final 50 % of the simulation,
    free energy changes little
    """

    heuristics = {"estimator_error": 0.05, "dg_slope": 0.1}
    return heuristics


@pytest.fixture
def poor_convergence_data():
    """
    Generate a dictionary with poor convergence data, i.e. in the final 50 % of the simulation,
    free energy changes significantly
    """

    heuristics = {"estimator_error": 0.05, "dg_slope": 1}
    return heuristics


def test_optimize_convergence_needs_sampling(mock_context, poor_convergence_data):
    """A test case based on poor convergence data. The optimizer should indicate that more sampling is needed."""

    optimizer = OptimizeConvergence(
        mock_context, optimization_heuristics={"estimator_error": 0.1, "dg_slope": 0.25}
    )
    result = optimizer._test_for_convergence(poor_convergence_data)
    assert result is False


def test_optimize_convergence_finished_sampling(mock_context, good_convergence_data):
    """A test case based on good convergence data. The optimizer should indicate that no more sampling is needed."""

    optimizer = OptimizeConvergence(mock_context)
    result = optimizer._test_for_convergence(good_convergence_data)
    assert result is True


@pytest.mark.xfail(
    reason="This test is expected to fail because the optimizer should indicate that more sampling is needed."
)
def test_optimizer_is_incorrect(mock_context, poor_convergence_data):
    optimizer = OptimizeConvergence(
        mock_context, optimization_heuristics={"estimator_error": 0.1, "dg_slope": 0.25}
    )
    result = optimizer._test_for_convergence(poor_convergence_data)
    assert result is True
