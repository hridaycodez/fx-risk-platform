import matplotlib.pyplot as plt
import numpy as np
from exposure import Exposure
from scenario import FXScenario
from pnl import compute_pnl
from sensitivity import run_sensitivity_analysis
from stress import compute_risk_metrics
from montecarlo import run_monte_carlo
import config


def main():
    print("=" * 50)
    print("FX RISK SIMULATOR - CORE ANALYTICS ENGINE")
    print("=" * 50)

    # 1. Define sample company FX profile
    exposures = [
        Exposure("US_Sales", "revenue", 500000, "USD"),
        Exposure("UK_Sales", "revenue", 200000, "GBP"),
        Exposure("EU_Operations", "cost", 300000, "EUR"),
        Exposure("JP_Components", "cost", 10000000, "JPY"),
    ]

    # 2. Base Case Analysis
    print("\n[1] Running Base Case Analysis...")
    base_results = compute_pnl(exposures, config.BASE_FX_RATES, config.BASE_CURRENCY)
    base_profit = base_results['profit']
    print(f"Base Profit: {base_profit:,.2f} {config.BASE_CURRENCY}")
    print(f"Base Margin: {base_results['margin']:.2%}")

    # 3. Stress Scenario Analysis
    print("\n[2] Running Stress Scenario (USD Weakens 15%, GBP Strengthens 10%)...")
    stress_scenario = FXScenario("Market_Turmoil", {"USD": -0.15, "GBP": 0.10})
    shocked_rates = stress_scenario.apply_shock(config.BASE_FX_RATES)
    stress_results = compute_pnl(exposures, shocked_rates, config.BASE_CURRENCY)
    print(f"Stress Profit: {stress_results['profit']:,.2f} {config.BASE_CURRENCY}")
    print(f"Impact on Profit: {stress_results['profit'] - base_profit:,.2f} {config.BASE_CURRENCY}")

    # 4. Sensitivity Analysis
    print("\n[3] Running Sensitivity Analysis (USD Shock -20% to +20%)...")
    sensitivity_results = run_sensitivity_analysis(
        exposures, config.BASE_FX_RATES, "USD", config.BASE_CURRENCY
    )

    # Plot Sensitivity
    shocks = [r['shock_percent'] * 100 for r in sensitivity_results]
    profits = [r['profit'] for r in sensitivity_results]

    plt.figure(figsize=(10, 6))
    plt.plot(shocks, profits, marker='o', linestyle='-', color='b')
    plt.axhline(y=base_profit, color='r', linestyle='--', label='Base Profit')
    plt.title("Sensitivity Analysis: USD Shock vs Profit")
    plt.xlabel("USD Shock (%)")
    plt.ylabel(f"Profit ({config.BASE_CURRENCY})")
    plt.grid(True)
    plt.legend()
    plt.savefig("sensitivity_plot.png")
    print("Sensitivity plot saved as 'sensitivity_plot.png'")

    # 5. Monte Carlo Simulation
    print(f"\n[4] Running Monte Carlo Simulation ({config.MC_ITERATIONS} iterations)...")
    mc_profits = run_monte_carlo(
        exposures, config.BASE_FX_RATES, config.FX_VOLATILITY, config.BASE_CURRENCY, config.MC_ITERATIONS
    )

    # Compute Risk Metrics
    risk_metrics = compute_risk_metrics(mc_profits, base_profit, config.LOSS_THRESHOLD_PERCENT)

    print(f"Mean Simulated Profit: {risk_metrics['mean_profit']:,.2f} {config.BASE_CURRENCY}")
    print(f"5th Percentile (VaR): {risk_metrics['p5_profit']:,.2f} {config.BASE_CURRENCY}")
    print(f"95th Percentile: {risk_metrics['p95_profit']:,.2f} {config.BASE_CURRENCY}")
    print(f"Probability of >{config.LOSS_THRESHOLD_PERCENT}% Profit Drop: {risk_metrics['downside_probability']:.2f}%")

    # Plot Monte Carlo Distribution
    plt.figure(figsize=(10, 6))
    plt.hist(mc_profits, bins=50, color='skyblue', edgecolor='black', alpha=0.7)
    plt.axvline(x=base_profit, color='r', linestyle='--', label='Base Profit')
    plt.axvline(x=risk_metrics['p5_profit'], color='orange', linestyle='-', label='5th Percentile')
    plt.title("Monte Carlo Simulation: Profit Distribution")
    plt.xlabel(f"Profit ({config.BASE_CURRENCY})")
    plt.ylabel("Frequency")
    plt.legend()
    plt.grid(True)
    plt.savefig("monte_carlo_histogram.png")
    print("Monte Carlo histogram saved as 'monte_carlo_histogram.png'")

    print("\n" + "=" * 50)
    print("SIMULATION COMPLETE")
    print("=" * 50)


if __name__ == "__main__":
    main()
