"""
Mercury Pollution Monte Carlo Simulator

A Python package for simulating mercury pollution transport, accumulation,
and risk assessment in water and soil systems using Monte Carlo methods.

Main API:
    - MercurySimulator: Main class for running simulations with custom data
    - run_simulation: Convenience function for quick simulations
    - ObservedData: Data class for providing field observations
"""

from mercury_package.models.empirical_model import (
    MonteCarloPraRiver,
    THRESHOLDS,
    calculate_risk_probabilities,
    sensitivity_analysis,
)
from mercury_package.models.observed_data import ObservedData
from mercury_package.models import (
    BaseMercuryModel,
    EmpiricalMercuryModel,
    MechanisticMercuryModel,
    CompartmentalMercuryModel,
    SimplifiedMercuryModel,
)
from mercury_package.simulator import MercurySimulator

__version__ = "1.1.1"
__all__ = [
    "MercurySimulator",
    "BaseMercuryModel",
    "EmpiricalMercuryModel",
    "MechanisticMercuryModel",
    "CompartmentalMercuryModel",
    "SimplifiedMercuryModel",
    "MonteCarloPraRiver",
    "ObservedData",
    "THRESHOLDS",
    "calculate_risk_probabilities",
    "sensitivity_analysis",
    "run_simulation",
]


def run_simulation(
    observed_data=None,
    model_type="empirical",
    n_iterations=10000,
    seed=42,
    output_dir="./results",
    generate_plots=True,
    time_points=None,
    **model_kwargs
):
    """
    Convenience function to run a complete mercury pollution simulation.
    
    Parameters
    ----------
    observed_data : ObservedData, optional
        Field observation data. If None, uses default Pra River data.
    model_type : str, default="empirical"
        Model type to use: "empirical", "mechanistic", "compartmental", or "simplified"
    n_iterations : int, default=10000
        Number of Monte Carlo iterations
    seed : int, default=42
        Random seed for reproducibility
    output_dir : str, default="./results"
        Directory to save results
    generate_plots : bool, default=True
        Whether to generate visualization plots
    time_points : array-like, optional
        Time points for simulation (in days). Default: [0, 30, 90, 180, 365, 730, 1095, 1460, 1825]
    **model_kwargs
        Additional keyword arguments passed to model constructor
    
    Returns
    -------
    dict
        Dictionary containing simulation results with keys:
        - 'water': Water mercury concentrations (mg/L)
        - 'sediment': Sediment mercury concentrations (mg/kg)
        - 'topsoil': Topsoil mercury concentrations (mg/kg)
        - 'subsoil': Subsoil mercury concentrations (mg/kg)
        - 'hazard_quotient': Human health risk metric
        - 'methylmercury_fish': Fish methylmercury concentrations (mg/kg)
        - 'time': Time points (days)
        - 'parameters': Parameter samples used in simulation
    
    Examples
    --------
    >>> from mercury_package import run_simulation, ObservedData
    >>> import numpy as np
    >>> 
    >>> # Use default Pra River data
    >>> results = run_simulation(n_iterations=1000)
    >>> 
    >>> # Use custom data
    >>> my_data = ObservedData(
    ...     water_times=np.array([0, 180, 365]),
    ...     water_conc=np.array([0.001, 0.05, 0.03]),
    ...     sed_times=np.array([0, 365, 1825]),
    ...     sed_conc=np.array([0.3, 4.0, 6.0]),
    ...     topsoil_times=np.array([0, 365, 1825]),
    ...     topsoil_conc=np.array([0.1, 1.5, 2.5]),
    ...     subsoil_times=np.array([0, 365, 1825]),
    ...     subsoil_conc=np.array([0.03, 0.4, 0.9])
    ... )
    >>> results = run_simulation(observed_data=my_data, n_iterations=5000)
    >>> 
    >>> # Use different model
    >>> results = run_simulation(model_type="mechanistic", n_iterations=5000)
    """
    simulator = MercurySimulator(
        observed_data=observed_data,
        model_type=model_type,
        seed=seed,
        **model_kwargs
    )
    return simulator.run_full_simulation(
        n_iterations=n_iterations,
        output_dir=output_dir,
        generate_plots=generate_plots,
        time_points=time_points,
    )
