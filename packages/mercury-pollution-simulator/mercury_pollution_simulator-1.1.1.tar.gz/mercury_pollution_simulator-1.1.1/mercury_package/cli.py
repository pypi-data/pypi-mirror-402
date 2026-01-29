"""
Command-line interface for mercury pollution simulator
"""

import argparse
import sys
from mercury_package import run_simulation, ObservedData
import numpy as np


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Mercury Pollution Monte Carlo Simulator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default Pra River data
  mercury-sim
  
  # Run with custom iterations and output directory
  mercury-sim --iterations 50000 --output ./my_results
  
  # Run without generating plots (faster)
  mercury-sim --no-plots
        """
    )
    
    parser.add_argument(
        '-n', '--iterations',
        type=int,
        default=10000,
        help='Number of Monte Carlo iterations (default: 10000)'
    )
    
    parser.add_argument(
        '-s', '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='./results',
        help='Output directory (default: ./results)'
    )
    
    parser.add_argument(
        '--no-plots',
        action='store_true',
        help='Skip generating visualization plots (faster execution)'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("MERCURY POLLUTION MONTE CARLO SIMULATOR")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Iterations: {args.iterations:,}")
    print(f"  Random Seed: {args.seed}")
    print(f"  Output Dir: {args.output}")
    print(f"  Generate Plots: {not args.no_plots}")
    print()
    
    # Run simulation
    results = run_simulation(
        observed_data=None,  # Use default Pra River data
        n_iterations=args.iterations,
        seed=args.seed,
        output_dir=args.output,
        generate_plots=not args.no_plots,
    )
    
    # Print quick summary
    print("\n" + "=" * 70)
    print("QUICK RESULTS SUMMARY")
    print("=" * 70)
    
    print(f"\n5-YEAR PROJECTIONS (Mean [5th - 95th percentile]):")
    print("-" * 50)
    
    compartments = [
        ('water', 'Water (mg/L)', 4),
        ('sediment', 'Sediment (mg/kg)', 2),
        ('topsoil', 'Topsoil (mg/kg)', 2),
        ('subsoil', 'Subsoil (mg/kg)', 2),
    ]
    
    for key, label, decimals in compartments:
        data = results[key][-1, :]
        mean = np.mean(data)
        p5 = np.percentile(data, 5)
        p95 = np.percentile(data, 95)
        print(f"  {label:20s}: {mean:.{decimals}f} [{p5:.{decimals}f} - {p95:.{decimals}f}]")
    
    print(f"\nHEALTH RISK:")
    print("-" * 50)
    hq = results['hazard_quotient'][-1, :]
    print(f"  Mean Hazard Quotient: {np.mean(hq):.2f}")
    print(f"  P(HQ > 1): {(hq > 1).mean()*100:.1f}%")
    print(f"  P(HQ > 10): {(hq > 10).mean()*100:.1f}%")
    
    risk_level = "HIGH" if np.mean(hq) > 1 else "MODERATE" if np.percentile(hq, 95) > 1 else "LOW"
    print(f"\n  *** OVERALL RISK LEVEL: {risk_level} ***")
    
    print(f"\nResults saved to: {args.output}/")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
