"""Quant Metrics - A package for quantitative portfolio metrics calculations."""

from quant_metrics.utils import (
    calculate_risk_free_rate,
    load_strategy_returns,
    get_data_length,
    calculate_strategy_returns,
    calculate_strategy_risk,
    calculate_sharpe_ratio,
    calculate_skewness,
    calculate_kurtosis,
    calculate_volatility_sharpe,
    calculate_psr,
    calculate_variance_across_trials,
    calculate_sr_star,
    calculate_dsr_from_formula,
)

__version__ = "0.1.0"
__all__ = [
    "calculate_risk_free_rate",
    "load_strategy_returns",
    "get_data_length",
    "calculate_strategy_returns",
    "calculate_strategy_risk",
    "calculate_sharpe_ratio",
    "calculate_skewness",
    "calculate_kurtosis",
    "calculate_volatility_sharpe",
    "calculate_psr",
    "calculate_variance_across_trials",
    "calculate_sr_star",
    "calculate_dsr_from_formula",
]
