import pytest
import numpy as np
from pathlib import Path
from alchemate.steps.preprocessing import OptimizeExchangeProbabilities
from alchemate.context import SimulationContext
from somd2.config import Config as somd2_config


@pytest.fixture
def dummy_context():
    context = SimulationContext(system="dummy_system", somd2_config=somd2_config())
    context.somd2_config.num_lambda = 4
    return context

@pytest.fixture
def repex_matrix_low_prob(tmp_path):
    # 4x4 matrix, low exchange probability (< 0.15) between 0-1 and 2-3
    matrix = np.array([
        [1.00, 0.00, 0.00, 0.00],
        [0.00, 0.75, 0.25, 0.00],
        [0.00, 0.25, 0.65, 0.10],
        [0.00, 0.00, 0.10, 0.90]
    ])
    return matrix

@pytest.fixture
def repex_matrix_high_prob(tmp_path):
    # 4x4 matrix, high exchange probability
    matrix = np.array([
        [0.75, 0.25, 0.00, 0.00],
        [0.25, 0.50, 0.25, 0.00],
        [0.00, 0.25, 0.50, 0.25],
        [0.00, 0.00, 0.25, 0.75]
    ])
    return matrix

def test_optimize_exchange_matrix_inserts_new_lambdas(tmp_path, dummy_context, repex_matrix_low_prob):
    dummy_context.somd2_config.output_directory = tmp_path
    np.savetxt(tmp_path / "repex_matrix.txt", repex_matrix_low_prob)
    optimizer = OptimizeExchangeProbabilities()

    # Should insert new lambdas between pairs with <0.15 exchange prob
    result = optimizer._optimize_exchange_matrix(dummy_context)
    
    # Should add lambdas between 0-1, 2-3, so we should have 6 in total
    assert len(result) == 6

    # Test that the new lambdas have been inserted correctly
    answer = [0.0, 0.167, 0.333, 0.667, 0.833, 1.0]
    assert result == pytest.approx(answer, abs=0.01)


def test_optimize_exchange_matrix_no_new_lambdas(tmp_path, dummy_context, repex_matrix_high_prob):
    dummy_context.somd2_config.output_directory = tmp_path
    np.savetxt(tmp_path / "repex_matrix.txt", repex_matrix_high_prob)
    optimizer = OptimizeExchangeProbabilities()

    # Should not insert any new lambdas
    result = optimizer._optimize_exchange_matrix(dummy_context)

    assert len(result) == 4

    # Test that the lambda values have not changed
    assert result == pytest.approx([0.0, 0.333, 0.666, 1.00], abs=0.01)