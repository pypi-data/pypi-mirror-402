from pathlib import Path

import pytest

from quant_metrics.utils import (
    calculate_dsr_from_formula,
    calculate_kurtosis,
    calculate_psr,
    calculate_risk_free_rate,
    calculate_sharpe_ratio,
    calculate_skewness,
    calculate_sr_star,
    calculate_strategy_returns,
    calculate_strategy_risk,
    calculate_variance_across_trials,
    calculate_volatility_sharpe,
    get_data_length,
)


@pytest.fixture
def test_data_path():
    """Fixture providing path to the test data CSV file."""
    return Path(__file__).parent / "strategy_wise_monthly_returns.csv"


def test_calculate_risk_free_rate():
    rf_rate = calculate_risk_free_rate(4.0, 12)
    assert abs(rf_rate - 0.0033) < 0.0001  # Should be around 0.33


def test_test_data_length(test_data_path):
    length = get_data_length(test_data_path)
    assert length == 120


def test_calculate_strategy_returns(test_data_path):
    # Expected returns as percentages
    expected_returns = {
        "Strategy 1": 1.01,
        "Strategy 2": 1.29,
        "Strategy 3": 1.28,
        "Strategy 4": 0.30,
        "Strategy 5": 0.73,
        "Strategy 6": 0.88,
        "Strategy 7": 1.24,
        "Strategy 8": 0.30,
        "Strategy 9": 0.82,
        "Strategy 10": 1.52,
    }

    calculated_returns = calculate_strategy_returns(csv_path=test_data_path)

    # Compare with expected values (allow small tolerance for rounding)
    for strategy, expected in expected_returns.items():
        calculated = calculated_returns[strategy]
        assert abs(calculated - expected) < 0.005, f"{strategy}: expected {expected}, got {calculated:.2f}"


def test_calculate_strategy_risk(test_data_path):
    """Test that calculated risk (standard deviation) from test data file matches expected values."""
    # Expected risk values as percentages (standard deviation)
    expected_risk = {
        "Strategy 1": 6.30,
        "Strategy 2": 6.00,
        "Strategy 3": 5.71,
        "Strategy 4": 6.13,
        "Strategy 5": 5.80,
        "Strategy 6": 6.97,
        "Strategy 7": 6.56,
        "Strategy 8": 5.59,
        "Strategy 9": 5.05,
        "Strategy 10": 4.91,
    }

    calculated_risk = calculate_strategy_risk(csv_path=test_data_path)

    # Compare with expected values (allow small tolerance for rounding)
    for strategy, expected in expected_risk.items():
        calculated = calculated_risk[strategy]
        assert abs(calculated - expected) < 0.005, f"{strategy}: expected {expected}, got {calculated:.2f}"


def test_calculate_sharpe_ratio(test_data_path):
    """Test that calculated Sharpe ratio from test data file matches expected values."""
    # Expected Sharpe ratio values
    expected_sharpe = {
        "Strategy 1": 0.1079,
        "Strategy 2": 0.1611,
        "Strategy 3": 0.1671,
        "Strategy 4": -0.0043,
        "Strategy 5": 0.0691,
        "Strategy 6": 0.0798,
        "Strategy 7": 0.1393,
        "Strategy 8": -0.0041,
        "Strategy 9": 0.0984,
        "Strategy 10": 0.2430,
    }

    calculated_sharpe = calculate_sharpe_ratio(csv_path=test_data_path)

    # Compare with expected values (allow small tolerance for rounding)
    for strategy, expected in expected_sharpe.items():
        calculated = calculated_sharpe[strategy]
        assert abs(calculated - expected) < 0.0001, f"{strategy}: expected {expected:.4f}, got {calculated:.4f}"


def test_calculate_skewness(test_data_path):
    """Test that calculated skewness from test data file matches expected values."""
    # Expected skewness values
    expected_skewness = {
        "Strategy 1": -0.3382,
        "Strategy 2": -0.3345,
        "Strategy 3": 0.1644,
        "Strategy 4": -0.1056,
        "Strategy 5": 0.3904,
        "Strategy 6": 1.1562,
        "Strategy 7": 0.9549,
        "Strategy 8": -0.0584,
        "Strategy 9": -0.0594,
        "Strategy 10": 0.0868,
    }

    calculated_skewness = calculate_skewness(csv_path=test_data_path)

    # Compare with expected values (allow small tolerance for rounding)
    for strategy, expected in expected_skewness.items():
        calculated = calculated_skewness[strategy]
        assert abs(calculated - expected) < 0.0005, f"{strategy}: expected {expected:.4f}, got {calculated:.4f}"


def test_calculate_kurtosis(test_data_path):
    """Test that calculated kurtosis from test data file matches expected values."""
    # Expected kurtosis values
    expected_kurtosis = {
        "Strategy 1": 1.4715,
        "Strategy 2": 0.4980,
        "Strategy 3": 0.2577,
        "Strategy 4": 1.5113,
        "Strategy 5": 0.6596,
        "Strategy 6": 5.1329,
        "Strategy 7": 6.1054,
        "Strategy 8": 0.2820,
        "Strategy 9": 1.1191,
        "Strategy 10": 0.6661,
    }

    calculated_kurtosis = calculate_kurtosis(csv_path=test_data_path)

    # Compare with expected values (allow small tolerance for rounding)
    for strategy, expected in expected_kurtosis.items():
        calculated = calculated_kurtosis[strategy]
        assert abs(calculated - expected) < 0.002, f"{strategy}: expected {expected:.4f}, got {calculated:.4f}"


def test_calculate_volatility_sharpe(test_data_path):
    """Test that calculated Volatility (Sharpe) from test data file matches expected values."""
    # Expected Volatility (Sharpe) values
    expected_vol_sharpe = {
        "Strategy 1": 0.0938,
        "Strategy 2": 0.0948,
        "Strategy 3": 0.0911,
        "Strategy 4": 0.0916,
        "Strategy 5": 0.0906,
        "Strategy 6": 0.0879,
        "Strategy 7": 0.0873,
        "Strategy 8": 0.0917,
        "Strategy 9": 0.0923,
        "Strategy 10": 0.0925,
    }

    calculated_vol_sharpe = calculate_volatility_sharpe(csv_path=test_data_path)

    # Compare with expected values (allow small tolerance for rounding)
    for strategy, expected in expected_vol_sharpe.items():
        calculated = calculated_vol_sharpe[strategy]
        assert abs(calculated - expected) < 0.0001, f"{strategy}: expected {expected:.4f}, got {calculated:.4f}"


def test_calculate_psr(test_data_path):
    """Test that calculated PSR from test data file matches expected values."""
    # Expected PSR values (as percentages)
    expected_psr = {
        "Strategy 1": 87.51,
        "Strategy 2": 95.53,
        "Strategy 3": 96.66,
        "Strategy 4": 48.12,
        "Strategy 5": 77.73,
        "Strategy 6": 81.82,
        "Strategy 7": 94.48,
        "Strategy 8": 48.23,
        "Strategy 9": 85.68,
        "Strategy 10": 99.57,
    }

    calculated_psr = calculate_psr(csv_path=test_data_path)

    # Compare with expected values (allow small tolerance for rounding)
    for strategy, expected in expected_psr.items():
        calculated = calculated_psr[strategy]
        assert abs(calculated - expected) < 0.03, f"{strategy}: expected {expected:.2f}, got {calculated:.2f}"


def test_calculate_variance_across_trials(test_data_path):
    """Test that calculated variance across trials matches expected value."""
    expected_variance = 0.0059

    variance = calculate_variance_across_trials(csv_path=test_data_path)

    # Compare with expected value (allow small tolerance for rounding)
    assert abs(variance - expected_variance) < 0.0001, f"Expected variance {expected_variance:.4f}, got {variance:.4f}"


def test_calculate_sr_star(test_data_path):
    """Test that calculated SR* matches expected value."""
    expected_sr_star = 0.1209

    # Calculate SR* using the function (num_trials automatically determined from CSV)
    sr_star = calculate_sr_star(csv_path=test_data_path, euler_mascheroni=0.5772)

    # Compare with expected value (allow small tolerance for rounding)
    assert abs(sr_star - expected_sr_star) < 0.0001, f"Expected SR* {expected_sr_star:.4f}, got {sr_star:.4f}"


def test_calculate_dsr_from_formula(test_data_path):
    """Test that calculated DSR from formula matches expected values."""
    # Expected DSR values as percentages
    expected_dsr = {
        "Strategy 1": 44.51,
        "Strategy 2": 66.43,
        "Strategy 3": 69.39,
        "Strategy 4": 8.60,
        "Strategy 5": 28.38,
        "Strategy 6": 32.02,
        "Strategy 7": 58.35,
        "Strategy 8": 8.64,
        "Strategy 9": 40.36,
        "Strategy 10": 90.67,
    }

    # Calculate DSR using the function (num_trials automatically determined from CSV)
    dsr = calculate_dsr_from_formula(csv_path=test_data_path, euler_mascheroni=0.5772)

    # Compare with expected values (allow small tolerance for rounding)
    for strategy, expected in expected_dsr.items():
        calculated = dsr[strategy]
        assert abs(calculated - expected) < 0.04, f"{strategy}: expected {expected:.2f}, got {calculated:.2f}"
