import pytest
import numpy as np
import pandas as pd
from somd2.config import Config as somd2_config
from alchemate.steps.postprocessing import OptimizeConvergence
from alchemate.context import SimulationContext


@pytest.fixture
def dummy_context():
    context = SimulationContext(system="dummy_system", somd2_config=somd2_config())
    return context


@pytest.fixture
def good_convergence_data():
    """Generate a DataFrame with good convergence data, i.e. in the final 50 % of the simulation,
    free energy does not change significantly (> 0.25 kT/mol)
    """
    forward_free_energy = np.linspace(2, 1, 10)
    data_fraction = np.linspace(0.1, 1, 10)

    df = pd.DataFrame({"Forward": forward_free_energy, "data_fraction": data_fraction})
    return df


@pytest.fixture
def poor_convergence_data():
    """Generate a DataFrame with poor convergence data, i.e. in the final 50 % of the simulation,
    free energy changes significantly (> 0.25 kT/mol)
    """
    forward_free_energy = np.linspace(8, 1, 10)
    data_fraction = np.linspace(0.1, 1, 10)

    df = pd.DataFrame({"Forward": forward_free_energy, "data_fraction": data_fraction})
    return df


def test_optimize_convergence_needs_sampling(dummy_context, poor_convergence_data):
    optimizer = OptimizeConvergence()

    # Should insert new lambdas between pairs with <0.15 exchange prob
    result = optimizer._test_convergence(poor_convergence_data)

    # Should add lambdas between 0-1, 2-3, so we should have 6 in total
    assert result is False


def test_optimize_convergence_finished_sampling(dummy_context, good_convergence_data):
    optimizer = OptimizeConvergence()

    # Should insert new lambdas between pairs with <0.15 exchange prob
    result = optimizer._test_convergence(good_convergence_data)

    # Should add lambdas between 0-1, 2-3, so we should have 6 in total
    assert result is True
