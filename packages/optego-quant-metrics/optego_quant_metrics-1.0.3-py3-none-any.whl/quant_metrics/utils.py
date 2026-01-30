"""Utility functions for quantitative metrics calculations."""

import csv
from math import erfc, exp, sqrt
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from scipy.stats import norm


def load_strategy_returns(csv_path: Path) -> Dict[str, List[float]]:
    """
    Load strategy returns from a CSV file.

    Parameters:
        csv_path: Path to the CSV file containing strategy returns.

    Returns:
        Dictionary mapping strategy names to lists of returns (as decimals)

    Example:
        >>> from pathlib import Path
        >>> returns = load_strategy_returns(Path("strategies_monthly_returns.csv"))
        >>> print(returns["Strategy 1"][:3])  # First 3 returns
    """
    with open(csv_path, "r") as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip header

        # Initialize arrays for each strategy (skip first column which is typically date/month)
        strategy_columns = header[1:]
        strategy_returns: Dict[str, List[float]] = {strategy: [] for strategy in strategy_columns}

        # Read all data rows
        for row in reader:
            for i, strategy in enumerate(strategy_columns):
                # Parse percentage string (e.g., "2.10%" -> 0.0210)
                value_str = row[i + 1].rstrip("%")
                value = float(value_str) / 100.0
                strategy_returns[strategy].append(value)

    return strategy_returns


def get_data_length(csv_path: Path) -> int:
    """
    Get the number of data rows in a CSV file (excluding header).

    Parameters:
        csv_path: Path to the CSV file.

    Returns:
        Number of data rows (excluding header)

    Example:
        >>> from pathlib import Path
        >>> length = get_data_length(Path("strategies_monthly_returns.csv"))
        >>> print(f"Number of data rows: {length}")
    """
    with open(csv_path, "r") as f:
        reader = csv.reader(f)
        rows = list(reader)
        # Exclude header row
        data_rows = rows[1:]
        return len(data_rows)


def calculate_strategy_returns(
    strategy_returns: Optional[Dict[str, List[float]]] = None,
    csv_path: Optional[Path] = None,
) -> Dict[str, float]:
    """
    Calculate geometric mean returns for each strategy.

    Formula: ((1+r1)*(1+r2)*...*(1+rn))^(1/n) - 1

    Parameters:
        strategy_returns: Dictionary mapping strategy names to lists of returns (as decimals).
                          If None, csv_path must be provided.
        csv_path: Path to CSV file. Required if strategy_returns is None.

    Returns:
        Dictionary mapping strategy names to geometric mean returns (as percentages)

    Raises:
        ValueError: If both strategy_returns and csv_path are None.

    Example:
        >>> from pathlib import Path
        >>> # Load from file
        >>> mean_returns = calculate_strategy_returns(csv_path=Path("strategies_monthly_returns.csv"))
        >>> print(f"Strategy 1 return: {mean_returns['Strategy 1']:.2f}%")
        >>> # Or provide returns directly
        >>> returns = {"Strategy 1": [0.01, 0.02, -0.01]}
        >>> mean_returns = calculate_strategy_returns(strategy_returns=returns)
    """
    if strategy_returns is None:
        if csv_path is None:
            raise ValueError("Either strategy_returns or csv_path must be provided")
        strategy_returns = load_strategy_returns(csv_path)
    calculated_returns = {}
    for strategy, returns_list in strategy_returns.items():
        returns_array = np.array(returns_list)
        n = len(returns_array)
        if n == 0:
            calculated_returns[strategy] = 0.0
        else:
            geometric_mean = (np.prod(1 + returns_array) ** (1.0 / n)) - 1
            calculated_returns[strategy] = geometric_mean * 100  # Convert to percentage
    return calculated_returns


def calculate_strategy_risk(
    strategy_returns: Optional[Dict[str, List[float]]] = None,
    csv_path: Optional[Path] = None,
) -> Dict[str, float]:
    """
    Calculate risk (standard deviation) for each strategy.

    Parameters:
        strategy_returns: Dictionary mapping strategy names to lists of returns (as decimals).
                          If None, csv_path must be provided.
        csv_path: Path to CSV file. Required if strategy_returns is None.

    Returns:
        Dictionary mapping strategy names to standard deviations (as percentages)

    Raises:
        ValueError: If both strategy_returns and csv_path are None.

    Example:
        >>> from pathlib import Path
        >>> # Load from file
        >>> risk = calculate_strategy_risk(csv_path=Path("strategies_monthly_returns.csv"))
        >>> print(f"Strategy 1 risk: {risk['Strategy 1']:.2f}%")
        >>> # Or provide returns directly
        >>> returns = {"Strategy 1": [0.01, 0.02, -0.01]}
        >>> risk = calculate_strategy_risk(strategy_returns=returns)
    """
    if strategy_returns is None:
        if csv_path is None:
            raise ValueError("Either strategy_returns or csv_path must be provided")
        strategy_returns = load_strategy_returns(csv_path)
    calculated_risk = {}
    for strategy, returns_list in strategy_returns.items():
        returns_array = np.array(returns_list)
        if len(returns_array) < 2:
            calculated_risk[strategy] = 0.0
        else:
            std_dev = np.std(returns_array, ddof=1)  # Sample standard deviation
            calculated_risk[strategy] = std_dev * 100  # Convert to percentage
    return calculated_risk


def calculate_sharpe_ratio(
    strategy_returns: Optional[Dict[str, List[float]]] = None,
    csv_path: Optional[Path] = None,
    risk_free_rate: Optional[float] = None,
    annual_rate: float = 4.0,
    periods_per_year: int = 12,
) -> Dict[str, float]:
    """
    Calculate Sharpe ratio for each strategy.

    Formula: (Return - Risk_free_rate) / Risk

    Parameters:
        strategy_returns: Dictionary mapping strategy names to lists of returns (as decimals).
                          If None, csv_path must be provided.
        csv_path: Path to CSV file. Required if strategy_returns is None.
        risk_free_rate: Risk-free rate as decimal (e.g., 0.00327 for ~0.327%).
                       If None, calculated from annual_rate and periods_per_year.
        annual_rate: Annual interest rate as percentage (default: 4.0 for 4%).
                     Used only if risk_free_rate is None.
        periods_per_year: Number of periods per year (default: 12 for monthly).
                         Used only if risk_free_rate is None.

    Returns:
        Dictionary mapping strategy names to Sharpe ratios

    Raises:
        ValueError: If both strategy_returns and csv_path are None.

    Example:
        >>> from pathlib import Path
        >>> # Load from file with default risk-free rate
        >>> sharpe = calculate_sharpe_ratio(csv_path=Path("strategies_monthly_returns.csv"))
        >>> print(f"Strategy 1 Sharpe: {sharpe['Strategy 1']:.4f}")
        >>> # Or provide returns directly with custom risk-free rate
        >>> returns = {"Strategy 1": [0.01, 0.02, -0.01]}
        >>> sharpe = calculate_sharpe_ratio(strategy_returns=returns, risk_free_rate=0.003)
    """
    if strategy_returns is None:
        if csv_path is None:
            raise ValueError("Either strategy_returns or csv_path must be provided")
        strategy_returns = load_strategy_returns(csv_path)

    # Calculate returns and risk
    returns = calculate_strategy_returns(strategy_returns=strategy_returns)
    risk = calculate_strategy_risk(strategy_returns=strategy_returns)

    # Get risk-free rate
    if risk_free_rate is None:
        risk_free_rate = calculate_risk_free_rate(annual_rate, periods_per_year)

    # Calculate Sharpe ratio for each strategy
    # Formula: (Return - Risk_free_rate) / Risk
    # Note: returns and risk are in percentages, risk_free_rate is in decimal
    calculated_sharpe = {}
    for strategy in returns.keys():
        return_decimal = returns[strategy] / 100.0  # Convert percentage to decimal
        risk_decimal = risk[strategy] / 100.0  # Convert percentage to decimal

        if risk_decimal == 0:
            calculated_sharpe[strategy] = 0.0
        else:
            sharpe = (return_decimal - risk_free_rate) / risk_decimal
            calculated_sharpe[strategy] = sharpe

    return calculated_sharpe


def calculate_skewness(
    strategy_returns: Optional[Dict[str, List[float]]] = None,
    csv_path: Optional[Path] = None,
) -> Dict[str, float]:
    """
    Calculate skewness for each strategy.

    Skewness measures the asymmetry of the probability distribution.
    Formula: (n / ((n-1)(n-2))) * Σ((xi - mean) / std)^3

    Parameters:
        strategy_returns: Dictionary mapping strategy names to lists of returns (as decimals).
                          If None, csv_path must be provided.
        csv_path: Path to CSV file. Required if strategy_returns is None.

    Returns:
        Dictionary mapping strategy names to skewness values

    Raises:
        ValueError: If both strategy_returns and csv_path are None.

    Example:
        >>> from pathlib import Path
        >>> # Load from file
        >>> skewness = calculate_skewness(csv_path=Path("strategies_monthly_returns.csv"))
        >>> print(f"Strategy 1 skewness: {skewness['Strategy 1']:.4f}")
        >>> # Or provide returns directly
        >>> returns = {"Strategy 1": [0.01, 0.02, -0.01]}
        >>> skewness = calculate_skewness(strategy_returns=returns)
    """
    if strategy_returns is None:
        if csv_path is None:
            raise ValueError("Either strategy_returns or csv_path must be provided")
        strategy_returns = load_strategy_returns(csv_path)

    calculated_skewness = {}
    for strategy, returns_list in strategy_returns.items():
        returns_array = np.array(returns_list)
        n = len(returns_array)

        if n < 3:
            # Need at least 3 observations for skewness
            calculated_skewness[strategy] = 0.0
        else:
            mean = np.mean(returns_array)
            std_dev = np.std(returns_array, ddof=1)  # Sample standard deviation

            if std_dev == 0:
                calculated_skewness[strategy] = 0.0
            else:
                # Calculate skewness: (n / ((n-1)(n-2))) * Σ((xi - mean) / std)^3
                standardized = (returns_array - mean) / std_dev
                skewness = (n / ((n - 1) * (n - 2))) * np.sum(standardized**3)
                calculated_skewness[strategy] = skewness

    return calculated_skewness


def calculate_kurtosis(
    strategy_returns: Optional[Dict[str, List[float]]] = None,
    csv_path: Optional[Path] = None,
) -> Dict[str, float]:
    """
    Calculate kurtosis (excess kurtosis) for each strategy.

    Kurtosis measures the "tailedness" of the probability distribution.
    Formula: (n(n+1) / ((n-1)(n-2)(n-3))) * Σ((xi - mean) / std)^4 - 3(n-1)^2 / ((n-2)(n-3))

    Parameters:
        strategy_returns: Dictionary mapping strategy names to lists of returns (as decimals).
                          If None, csv_path must be provided.
        csv_path: Path to CSV file. Required if strategy_returns is None.

    Returns:
        Dictionary mapping strategy names to kurtosis values (excess kurtosis)

    Raises:
        ValueError: If both strategy_returns and csv_path are None.

    Example:
        >>> from pathlib import Path
        >>> # Load from file
        >>> kurtosis = calculate_kurtosis(csv_path=Path("strategies_monthly_returns.csv"))
        >>> print(f"Strategy 1 kurtosis: {kurtosis['Strategy 1']:.4f}")
        >>> # Or provide returns directly
        >>> returns = {"Strategy 1": [0.01, 0.02, -0.01]}
        >>> kurtosis = calculate_kurtosis(strategy_returns=returns)
    """
    if strategy_returns is None:
        if csv_path is None:
            raise ValueError("Either strategy_returns or csv_path must be provided")
        strategy_returns = load_strategy_returns(csv_path)

    calculated_kurtosis = {}
    for strategy, returns_list in strategy_returns.items():
        returns_array = np.array(returns_list)
        n = len(returns_array)

        if n < 4:
            # Need at least 4 observations for kurtosis
            calculated_kurtosis[strategy] = 0.0
        else:
            mean = np.mean(returns_array)
            std_dev = np.std(returns_array, ddof=1)  # Sample standard deviation

            if std_dev == 0:
                calculated_kurtosis[strategy] = 0.0
            else:
                # Calculate excess kurtosis
                # Formula: (n(n+1) / ((n-1)(n-2)(n-3))) * Σ((xi - mean) / std)^4 - 3(n-1)^2 / ((n-2)(n-3))
                standardized = (returns_array - mean) / std_dev
                sum_fourth_power = np.sum(standardized**4)

                first_term = (n * (n + 1)) / ((n - 1) * (n - 2) * (n - 3))
                second_term = 3 * (n - 1) ** 2 / ((n - 2) * (n - 3))

                kurtosis = first_term * sum_fourth_power - second_term
                calculated_kurtosis[strategy] = kurtosis

    return calculated_kurtosis


def calculate_volatility_sharpe(
    strategy_returns: Optional[Dict[str, List[float]]] = None,
    csv_path: Optional[Path] = None,
    risk_free_rate: Optional[float] = None,
    annual_rate: float = 4.0,
    periods_per_year: int = 12,
) -> Dict[str, float]:
    """
    Calculate Volatility (Sharpe) for each strategy.

    This adjusts volatility for skewness and kurtosis effects.
    Formula: SQRT((1 - Skewness*Sharpe + (Kurtosis+2)/4*Sharpe^2)/(Sample size-1))

    Parameters:
        strategy_returns: Dictionary mapping strategy names to lists of returns (as decimals).
                          If None, csv_path must be provided.
        csv_path: Path to CSV file. Required if strategy_returns is None.
        risk_free_rate: Risk-free rate as decimal (e.g., 0.00327 for ~0.327%).
                       If None, calculated from annual_rate and periods_per_year.
        annual_rate: Annual interest rate as percentage (default: 4.0 for 4%).
                     Used only if risk_free_rate is None.
        periods_per_year: Number of periods per year (default: 12 for monthly).
                         Used only if risk_free_rate is None.

    Returns:
        Dictionary mapping strategy names to Volatility (Sharpe) values

    Raises:
        ValueError: If both strategy_returns and csv_path are None.

    Example:
        >>> from pathlib import Path
        >>> # Load from file with default risk-free rate
        >>> vol_sharpe = calculate_volatility_sharpe(csv_path=Path("strategies_monthly_returns.csv"))
        >>> print(f"Strategy 1 Volatility (Sharpe): {vol_sharpe['Strategy 1']:.4f}")
    """
    if strategy_returns is None:
        if csv_path is None:
            raise ValueError("Either strategy_returns or csv_path must be provided")
        strategy_returns = load_strategy_returns(csv_path)

    # Calculate required metrics
    sharpe = calculate_sharpe_ratio(
        strategy_returns=strategy_returns,
        risk_free_rate=risk_free_rate,
        annual_rate=annual_rate,
        periods_per_year=periods_per_year,
    )
    skewness = calculate_skewness(strategy_returns=strategy_returns)
    kurtosis = calculate_kurtosis(strategy_returns=strategy_returns)

    # Calculate Volatility (Sharpe) for each strategy
    # Formula: SQRT((1 - Skewness*Sharpe + (Kurtosis+2)/4*Sharpe^2)/(Sample size-1))
    calculated_vol_sharpe = {}
    for strategy in strategy_returns.keys():
        returns_array = np.array(strategy_returns[strategy])
        n = len(returns_array)

        if n < 2:
            calculated_vol_sharpe[strategy] = 0.0
        else:
            sharpe_val = sharpe[strategy]
            skew_val = skewness[strategy]
            kurt_val = kurtosis[strategy]

            # Calculate numerator: 1 - Skewness*Sharpe + (Kurtosis+2)/4*Sharpe^2
            numerator = 1 - (skew_val * sharpe_val) + ((kurt_val + 2) / 4) * (sharpe_val**2)

            # Calculate denominator: Sample size - 1
            denominator = n - 1

            if denominator <= 0 or numerator < 0:
                calculated_vol_sharpe[strategy] = 0.0
            else:
                vol_sharpe = np.sqrt(numerator / denominator)
                calculated_vol_sharpe[strategy] = vol_sharpe

    return calculated_vol_sharpe


def calculate_variance_across_trials(
    strategy_returns: Optional[Dict[str, List[float]]] = None,
    csv_path: Optional[Path] = None,
    risk_free_rate: Optional[float] = None,
    annual_rate: float = 4.0,
    periods_per_year: int = 12,
) -> float:
    """
    Calculate variance across trials using VAR.S of Sharpe ratios of all strategies.

    This calculates the sample variance of Sharpe ratios across all strategies,
    equivalent to Excel's VAR.S function.

    Parameters:
        strategy_returns: Dictionary mapping strategy names to lists of returns (as decimals).
                          If None, csv_path must be provided.
        csv_path: Path to CSV file. Required if strategy_returns is None.
        risk_free_rate: Risk-free rate as decimal (e.g., 0.00327 for ~0.327%).
                       If None, calculated from annual_rate and periods_per_year.
        annual_rate: Annual interest rate as percentage (default: 4.0 for 4%).
                     Used only if risk_free_rate is None.
        periods_per_year: Number of periods per year (default: 12 for monthly).
                         Used only if risk_free_rate is None.

    Returns:
        Variance of Sharpe ratios across all strategies (sample variance)

    Raises:
        ValueError: If both strategy_returns and csv_path are None.

    Example:
        >>> from pathlib import Path
        >>> # Load from file with default risk-free rate
        >>> variance = calculate_variance_across_trials(csv_path=Path("strategies_monthly_returns.csv"))
        >>> print(f"Variance across trials: {variance:.6f}")
    """
    if strategy_returns is None:
        if csv_path is None:
            raise ValueError("Either strategy_returns or csv_path must be provided")
        strategy_returns = load_strategy_returns(csv_path)

    # Calculate Sharpe ratios for all strategies
    sharpe_ratios = calculate_sharpe_ratio(
        strategy_returns=strategy_returns,
        risk_free_rate=risk_free_rate,
        annual_rate=annual_rate,
        periods_per_year=periods_per_year,
    )

    # Extract Sharpe ratio values as an array
    sharpe_values = np.array(list(sharpe_ratios.values()))

    # Calculate sample variance (VAR.S) - uses ddof=1
    if len(sharpe_values) < 2:
        return 0.0

    variance = np.var(sharpe_values, ddof=1)  # Sample variance
    return variance


def calculate_sr_star(
    strategy_returns: Optional[Dict[str, List[float]]] = None,
    csv_path: Optional[Path] = None,
    risk_free_rate: Optional[float] = None,
    annual_rate: float = 4.0,
    periods_per_year: int = 12,
    euler_mascheroni: float = 0.5772,
) -> float:
    """
    Calculate SR* (Sharpe Ratio*) using the formula:
    SR* = SQRT(Variance across trials) * ((1 - Euler-Mascheroni) * NORMSINV(1 - 1/Number of trials) +
          Euler-Mascheroni * NORMSINV(1 - 1/(Number of trials * EXP(1))))

    Parameters:
        strategy_returns: Dictionary mapping strategy names to lists of returns (as decimals).
                          If None, csv_path must be provided.
        csv_path: Path to CSV file. Required if strategy_returns is None.
        risk_free_rate: Risk-free rate as decimal (e.g., 0.00327 for ~0.327%).
                       If None, calculated from annual_rate and periods_per_year.
        annual_rate: Annual interest rate as percentage (default: 4.0 for 4%).
                     Used only if risk_free_rate is None.
        periods_per_year: Number of periods per year (default: 12 for monthly).
                         Used only if risk_free_rate is None.
        euler_mascheroni: Euler-Mascheroni constant (default: 0.5772).

    Returns:
        SR* value (Sharpe Ratio*)

    Raises:
        ValueError: If both strategy_returns and csv_path are None.

    Example:
        >>> from pathlib import Path
        >>> # Load from file - number of trials automatically determined from CSV
        >>> sr_star = calculate_sr_star(csv_path=Path("strategies_monthly_returns.csv"))
        >>> print(f"SR*: {sr_star:.6f}")
    """
    if strategy_returns is None:
        if csv_path is None:
            raise ValueError("Either strategy_returns or csv_path must be provided")
        strategy_returns = load_strategy_returns(csv_path)

    # Automatically determine number of trials from the number of strategies
    num_trials = len(strategy_returns)
    if num_trials == 0:
        raise ValueError("At least one strategy must be provided")

    # Calculate variance across trials
    variance = calculate_variance_across_trials(
        strategy_returns=strategy_returns,
        csv_path=None,  # Already loaded
        risk_free_rate=risk_free_rate,
        annual_rate=annual_rate,
        periods_per_year=periods_per_year,
    )

    # Calculate SQRT(Variance across trials)
    sqrt_variance = sqrt(variance)

    # Calculate NORMSINV values
    # NORMSINV is the inverse of the standard normal CDF (quantile function)
    # Using scipy.stats.norm.ppf for NORMSINV
    prob1 = 1 - 1 / num_trials
    prob2 = 1 - 1 / (num_trials * exp(1))

    norms_inv1 = norm.ppf(prob1)  # NORMSINV(1 - 1/Number of trials)
    norms_inv2 = norm.ppf(prob2)  # NORMSINV(1 - 1/(Number of trials * EXP(1)))

    # Calculate SR*
    sr_star = sqrt_variance * ((1 - euler_mascheroni) * norms_inv1 + euler_mascheroni * norms_inv2)

    return sr_star


def _norm_s_dist(x: float) -> float:
    """
    Calculate the cumulative distribution function (CDF) of the standard normal distribution.

    Equivalent to Excel's NORM.S.DIST function.
    Formula: 0.5 * erfc(-x / sqrt(2))

    Parameters:
        x: Value at which to evaluate the CDF

    Returns:
        CDF value (probability that a standard normal random variable is <= x)
    """
    # NORM.S.DIST(x) = 0.5 * erfc(-x / sqrt(2))
    return 0.5 * erfc(-x / sqrt(2))


def calculate_psr(
    strategy_returns: Optional[Dict[str, List[float]]] = None,
    csv_path: Optional[Path] = None,
    risk_free_rate: Optional[float] = None,
    annual_rate: float = 4.0,
    periods_per_year: int = 12,
) -> Dict[str, float]:
    """
    Calculate Probabilistic Sharpe Ratio (PSR) for each strategy.

    PSR = NORM.S.DIST(Sharpe / Volatility(Sharpe))
    This gives the probability that the Sharpe ratio is positive.

    Parameters:
        strategy_returns: Dictionary mapping strategy names to lists of returns (as decimals).
                          If None, csv_path must be provided.
        csv_path: Path to CSV file. Required if strategy_returns is None.
        risk_free_rate: Risk-free rate as decimal (e.g., 0.00327 for ~0.327%).
                       If None, calculated from annual_rate and periods_per_year.
        annual_rate: Annual interest rate as percentage (default: 4.0 for 4%).
                     Used only if risk_free_rate is None.
        periods_per_year: Number of periods per year (default: 12 for monthly).
                         Used only if risk_free_rate is None.

    Returns:
        Dictionary mapping strategy names to PSR values (as percentages)

    Raises:
        ValueError: If both strategy_returns and csv_path are None.

    Example:
        >>> from pathlib import Path
        >>> # Load from file with default risk-free rate
        >>> psr = calculate_psr(csv_path=Path("strategies_monthly_returns.csv"))
        >>> print(f"Strategy 1 PSR: {psr['Strategy 1']:.2f}%")
    """
    if strategy_returns is None:
        if csv_path is None:
            raise ValueError("Either strategy_returns or csv_path must be provided")
        strategy_returns = load_strategy_returns(csv_path)

    # Calculate required metrics
    sharpe = calculate_sharpe_ratio(
        strategy_returns=strategy_returns,
        risk_free_rate=risk_free_rate,
        annual_rate=annual_rate,
        periods_per_year=periods_per_year,
    )
    vol_sharpe = calculate_volatility_sharpe(
        strategy_returns=strategy_returns,
        risk_free_rate=risk_free_rate,
        annual_rate=annual_rate,
        periods_per_year=periods_per_year,
    )

    # Calculate PSR for each strategy
    # Formula: NORM.S.DIST(Sharpe / Volatility(Sharpe))
    # Returns as percentage
    calculated_psr = {}
    for strategy in strategy_returns.keys():
        sharpe_val = sharpe[strategy]
        vol_sharpe_val = vol_sharpe[strategy]

        if vol_sharpe_val == 0:
            calculated_psr[strategy] = 0.0
        else:
            ratio = sharpe_val / vol_sharpe_val
            psr = _norm_s_dist(ratio)
            calculated_psr[strategy] = psr * 100  # Convert to percentage

    return calculated_psr


def calculate_dsr_from_formula(
    strategy_returns: Optional[Dict[str, List[float]]] = None,
    csv_path: Optional[Path] = None,
    risk_free_rate: Optional[float] = None,
    annual_rate: float = 4.0,
    periods_per_year: int = 12,
    euler_mascheroni: float = 0.5772,
) -> Dict[str, float]:
    """
    Calculate DSR (Deflated Sharpe Ratio) for each strategy using the formula:
    DSR = NORM.S.DIST((Sharpe - SR*) / Volatility (Sharpe))

    This formula adjusts the Sharpe ratio by accounting for multiple testing
    through SR* and non-normal distributions through Volatility (Sharpe).

    Parameters:
        strategy_returns: Dictionary mapping strategy names to lists of returns (as decimals).
                          If None, csv_path must be provided.
        csv_path: Path to CSV file. Required if strategy_returns is None.
        risk_free_rate: Risk-free rate as decimal (e.g., 0.00327 for ~0.327%).
                       If None, calculated from annual_rate and periods_per_year.
        annual_rate: Annual interest rate as percentage (default: 4.0 for 4%).
                     Used only if risk_free_rate is None.
        periods_per_year: Number of periods per year (default: 12 for monthly).
                         Used only if risk_free_rate is None.
        euler_mascheroni: Euler-Mascheroni constant (default: 0.5772).

    Returns:
        Dictionary mapping strategy names to DSR values (as percentages)

    Raises:
        ValueError: If both strategy_returns and csv_path are None.

    Example:
        >>> from pathlib import Path
        >>> # Load from file - number of trials automatically determined from CSV
        >>> dsr = calculate_dsr_from_formula(csv_path=Path("strategies_monthly_returns.csv"))
        >>> print(f"Strategy 1 DSR: {dsr['Strategy 1']:.4f}")
    """
    if strategy_returns is None:
        if csv_path is None:
            raise ValueError("Either strategy_returns or csv_path must be provided")
        strategy_returns = load_strategy_returns(csv_path)

    # Calculate required metrics
    sharpe = calculate_sharpe_ratio(
        strategy_returns=strategy_returns,
        risk_free_rate=risk_free_rate,
        annual_rate=annual_rate,
        periods_per_year=periods_per_year,
    )
    vol_sharpe = calculate_volatility_sharpe(
        strategy_returns=strategy_returns,
        risk_free_rate=risk_free_rate,
        annual_rate=annual_rate,
        periods_per_year=periods_per_year,
    )
    sr_star = calculate_sr_star(
        strategy_returns=strategy_returns,
        csv_path=None,  # Already loaded
        risk_free_rate=risk_free_rate,
        annual_rate=annual_rate,
        periods_per_year=periods_per_year,
        euler_mascheroni=euler_mascheroni,
    )

    # Calculate DSR for each strategy
    # Formula: NORM.S.DIST((Sharpe - SR*) / Volatility (Sharpe))
    calculated_dsr = {}
    for strategy in strategy_returns.keys():
        sharpe_val = sharpe[strategy]
        vol_sharpe_val = vol_sharpe[strategy]

        if vol_sharpe_val == 0:
            calculated_dsr[strategy] = 0.0
        else:
            # Volatility (Sharpe) is already in decimal form (not percentage)
            numerator = sharpe_val - sr_star
            ratio = numerator / vol_sharpe_val
            dsr_value = _norm_s_dist(ratio)
            calculated_dsr[strategy] = dsr_value * 100  # Convert to percentage

    return calculated_dsr


def calculate_risk_free_rate(annual_rate: float = 4.0, periods_per_year: int = 12) -> float:
    """
    Calculate the periodic risk-free rate from an annual rate.

    Converts an annual interest rate to a periodic (e.g., monthly) rate using
    the formula: (1 + annual_rate/100)^(1/periods_per_year) - 1

    Parameters:
        annual_rate: Annual interest rate as a percentage (default: 4.0 for 4%)
        periods_per_year: Number of periods per year (default: 12 for monthly)

    Returns:
        float: Periodic risk-free rate as a decimal (e.g., 0.00327 for ~0.327%)

    Example:
        >>> # Calculate monthly risk-free rate from 4% annual rate
        >>> monthly_rf = calculate_risk_free_rate(4.0, 12)
        >>> print(f"Monthly risk-free rate: {monthly_rf:.6f}")
    """
    if annual_rate < 0:
        raise ValueError("annual_rate must be non-negative")
    if periods_per_year < 1:
        raise ValueError("periods_per_year must be >= 1")

    # Convert percentage to decimal and calculate periodic rate
    annual_decimal = 1 + (annual_rate / 100.0)
    periodic_rate = annual_decimal ** (1.0 / periods_per_year) - 1

    return periodic_rate
