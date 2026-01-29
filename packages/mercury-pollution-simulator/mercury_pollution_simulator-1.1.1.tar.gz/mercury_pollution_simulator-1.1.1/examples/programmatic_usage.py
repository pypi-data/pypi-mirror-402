"""
Example: Programmatic usage without generating plots

This example shows how to use the package programmatically
to access results directly without generating visualization files.
"""

import numpy as np
from mercury_package import MercurySimulator, ObservedData, calculate_risk_probabilities, sensitivity_analysis

# Create simulator
simulator = MercurySimulator(seed=42)

# Run simulation without plots (faster)
results = simulator.run_simulation(n_iterations=10000)

# Calculate risk probabilities
probs = calculate_risk_probabilities(results, time_idx=-1)

# Perform sensitivity analysis
sens = sensitivity_analysis(results, "hazard_quotient", time_idx=-1)

# Access and analyze results
print("Risk Assessment Summary:")
print(f"  P(Water > EPA limit): {probs['Water > EPA (0.002 mg/L)']:.1f}%")
print(f"  P(Sediment > PEC): {probs['Sediment > PEC (1.06 mg/kg)']:.1f}%")
print(f"  P(HQ > 1): {probs['HQ > 1 (health risk)']:.1f}%")

print("\nTop 3 Risk Drivers:")
for i, (param, corr) in enumerate(list(sens.items())[:3], 1):
    print(f"  {i}. {param}: {corr:+.3f}")

# Extract time series data
time_years = results['time'] / 365
water_mean = np.mean(results['water'], axis=1)
sediment_mean = np.mean(results['sediment'], axis=1)

print("\nTime Series (Mean values):")
for i, t in enumerate(time_years):
    if i % 2 == 0:  # Print every other time point
        print(f"  Year {t:.1f}: Water={water_mean[i]:.4f} mg/L, Sediment={sediment_mean[i]:.2f} mg/kg")
