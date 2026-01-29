"""
Example: Using custom field observation data

This example shows how to provide your own field observation data
to calibrate the model for a different site.
"""

import numpy as np
from mercury_package import MercurySimulator, ObservedData

# Create custom observation data for your site
# Replace these values with your actual field measurements
my_observations = ObservedData(
    # Water column measurements (mg/L)
    water_times=np.array([0, 90, 180, 365, 730]),  # days
    water_conc=np.array([0.001, 0.045, 0.060, 0.040, 0.025]),  # your measurements
    
    # Sediment measurements (mg/kg)
    sed_times=np.array([0, 180, 365, 1095, 1825]),
    sed_conc=np.array([0.3, 2.5, 4.0, 5.5, 6.5]),  # your measurements
    
    # Topsoil measurements (mg/kg)
    topsoil_times=np.array([0, 365, 1825]),
    topsoil_conc=np.array([0.10, 1.5, 2.5]),  # your measurements
    
    # Subsoil measurements (mg/kg)
    subsoil_times=np.array([0, 365, 1825]),
    subsoil_conc=np.array([0.03, 0.4, 0.8])  # your measurements
)

# Create simulator with custom data
simulator = MercurySimulator(observed_data=my_observations, seed=42)

# Get validation metrics
validation = simulator.get_validation()
print("Model Validation (R² values):")
for comp in ["water", "sediment", "topsoil", "subsoil"]:
    print(f"  {comp}: {validation[comp]['r2']:.3f}")

# Run simulation
print("\nRunning Monte Carlo simulation...")
results = simulator.run_full_simulation(
    n_iterations=5000,
    output_dir="./custom_results",
    generate_plots=True
)

# Access results
print("\nSimulation Results (Year 5):")
print(f"  Water: {results['water'][-1, :].mean():.4f} mg/L")
print(f"  Sediment: {results['sediment'][-1, :].mean():.2f} mg/kg")
print(f"  Topsoil: {results['topsoil'][-1, :].mean():.2f} mg/kg")
print(f"  Hazard Quotient: {results['hazard_quotient'][-1, :].mean():.2f}")
