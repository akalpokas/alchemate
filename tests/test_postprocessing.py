import pytest
import numpy as np
import pandas as pd
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
    Generate a DataFrame with good convergence data, i.e. in the final 50 % of the simulation,
    free energy does not change significantly (> 0.20 kT/mol)
    """
    forward_free_energy_err = np.linspace(1, 0.1, 10)
    data_fraction = np.linspace(0.1, 1, 10)

    df = pd.DataFrame(
        {"Forward_Error": forward_free_energy_err, "data_fraction": data_fraction}
    )
    return df


@pytest.fixture
def poor_convergence_data():
    """
    Generate a DataFrame with poor convergence data, i.e. in the final 50 % of the simulation,
    free energy changes significantly (> 0.20 kT/mol)
    """
    forward_free_energy_err = np.linspace(2, 0.25, 10)
    data_fraction = np.linspace(0.1, 1, 10)

    df = pd.DataFrame(
        {"Forward_Error": forward_free_energy_err, "data_fraction": data_fraction}
    )
    return df


def test_optimize_convergence_needs_sampling(mock_context, poor_convergence_data):
    """A test case based on poor convergence data. The optimizer should indicate that more sampling is needed."""

    optimizer = OptimizeConvergence()
    result = optimizer._test_convergence(poor_convergence_data)
    assert result is False


def test_optimize_convergence_finished_sampling(mock_context, good_convergence_data):
    """A test case based on good convergence data. The optimizer should indicate that no more sampling is needed."""

    optimizer = OptimizeConvergence()
    result = optimizer._test_convergence(good_convergence_data)
    assert result is True
