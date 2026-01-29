"""
Example: Comparing Different Model Types

This example shows how to use different model types and compare their results.
"""

import numpy as np
from mercury_package import MercurySimulator, ObservedData
from mercury_package.models import (
    EmpiricalMercuryModel,
    MechanisticMercuryModel,
    CompartmentalMercuryModel,
    SimplifiedMercuryModel,
)

# Create observation data
my_data = ObservedData(
    water_times=np.array([0, 180, 365, 1095, 1825]),
    water_conc=np.array([0.002, 0.072, 0.054, 0.031, 0.018]),
    sed_times=np.array([0, 180, 365, 1095, 1825]),
    sed_conc=np.array([0.4, 3.2, 5.1, 6.8, 7.6]),
    topsoil_times=np.array([0, 365, 1825]),
    topsoil_conc=np.array([0.15, 2.1, 3.0]),
    subsoil_times=np.array([0, 365, 1825]),
    subsoil_conc=np.array([0.04, 0.5, 1.1])
)

# Model types to compare
model_types = {
    "Empirical": "empirical",
    "Mechanistic": "mechanistic",
    "Compartmental": "compartmental",
    "Simplified": "simplified",
}

print("=" * 70)
print("COMPARING DIFFERENT MODEL TYPES")
print("=" * 70)

results_summary = {}

for model_name, model_type in model_types.items():
    print(f"\n{model_name} Model:")
    print("-" * 50)
    
    # Create simulator with specific model
    simulator = MercurySimulator(
        observed_data=my_data,
        model_type=model_type,
        seed=42
    )
    
    # Get validation
    validation = simulator.get_validation()
    print(f"  Validation R² values:")
    for comp in ["water", "sediment", "topsoil", "subsoil"]:
        r2 = validation[comp]["r2"]
        print(f"    {comp}: {r2:.3f}")
    
    # Run simulation (smaller for comparison)
    results = simulator.run_simulation(n_iterations=1000)
    
    # Store summary
    results_summary[model_name] = {
        "water_y5": np.mean(results["water"][-1, :]),
        "sediment_y5": np.mean(results["sediment"][-1, :]),
        "hq_y5": np.mean(results["hazard_quotient"][-1, :]),
        "avg_r2": np.mean([validation[c]["r2"] for c in ["water", "sediment", "topsoil", "subsoil"]])
    }

# Print comparison table
print("\n" + "=" * 70)
print("MODEL COMPARISON SUMMARY (Year 5)")
print("=" * 70)
print(f"{'Model':<15} {'Water (mg/L)':<15} {'Sediment (mg/kg)':<18} {'HQ':<10} {'Avg R²':<10}")
print("-" * 70)

for model_name, summary in results_summary.items():
    print(f"{model_name:<15} {summary['water_y5']:<15.4f} {summary['sediment_y5']:<18.2f} "
          f"{summary['hq_y5']:<10.2f} {summary['avg_r2']:<10.3f}")

print("\n" + "=" * 70)
print("RECOMMENDATIONS:")
print("=" * 70)
print("  - Empirical: Best fit when calibration data is available (recommended)")
print("  - Mechanistic: Use when physical parameters are well-known")
print("  - Compartmental: Good for understanding mass transfer between compartments")
print("  - Simplified: Quick assessments with limited data")
print("=" * 70)
