"""
Basic usage example for mercury_package

This example shows how to use the package with default Pra River data.
"""

from mercury_package import run_simulation

# Run simulation with default settings
print("Running simulation with default Pra River data...")
results = run_simulation(
    n_iterations=1000,  # Use fewer iterations for faster demo
    output_dir="./example_results",
    generate_plots=True
)

# Access results
print("\nResults Summary:")
print(f"  Water concentration (Year 5): {results['water'][-1, :].mean():.4f} mg/L")
print(f"  Sediment concentration (Year 5): {results['sediment'][-1, :].mean():.2f} mg/kg")
print(f"  Mean Hazard Quotient: {results['hazard_quotient'][-1, :].mean():.2f}")
