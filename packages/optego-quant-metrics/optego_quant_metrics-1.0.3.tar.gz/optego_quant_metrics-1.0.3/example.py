"""Example usage of quant_metrics package."""

from pathlib import Path

from quant_metrics import calculate_dsr_from_formula, calculate_risk_free_rate

# Example: Calculate DSR for multiple strategies from a CSV file
# This demonstrates the proper DSR calculation accounting for multiple testing
# and non-normal return distributions

# Load strategy returns from CSV file
csv_path = Path("tests/strategy_wise_monthly_returns.csv")

# Calculate DSR for all strategies
# This uses the formula: DSR = NORM.S.DIST((Sharpe - SR*) / Volatility (Sharpe))
# Number of trials is automatically determined from the number of strategies in the CSV
dsr_results = calculate_dsr_from_formula(csv_path=csv_path)

print("Deflated Sharpe Ratio (DSR) for each strategy:")
for strategy, dsr_value in sorted(dsr_results.items(), key=lambda x: int(x[0].split()[-1])):
    print(f"{strategy}: {dsr_value:.2f}")

# Calculate monthly risk-free rate from 4 annual rate
# Formula: (1 + 4)^(1/12) - 1
risk_free_rate = calculate_risk_free_rate(4.0, 12)
print(f"\nMonthly risk-free rate (from 4 annual): {risk_free_rate:.6f} ({risk_free_rate*100:.4f})")
