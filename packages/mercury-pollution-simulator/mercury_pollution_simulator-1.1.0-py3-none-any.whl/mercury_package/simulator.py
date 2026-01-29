"""
Main simulator class for mercury pollution assessment
Provides a clean API for running simulations with custom data
"""

import os
import numpy as np
from typing import Dict, Optional, Union
from pathlib import Path

from mercury_package.models.empirical_model import (
    ObservedData,
    MonteCarloPraRiver,
    calculate_risk_probabilities,
    sensitivity_analysis,
)
from mercury_package.models.base_model import BaseMercuryModel
from mercury_package.models.empirical_model import EmpiricalMercuryModel
from mercury_package.models.mechanistic_model import MechanisticMercuryModel
from mercury_package.models.compartmental_model import CompartmentalMercuryModel
from mercury_package.models.simplified_model import SimplifiedMercuryModel


class MercurySimulator:
    """
    Main class for running mercury pollution Monte Carlo simulations.
    
    This class provides a clean interface for running simulations with custom
    field observation data. It handles model calibration, Monte Carlo simulation,
    and optional visualization/reporting.
    
    Parameters
    ----------
    observed_data : ObservedData, optional
        Field observation data for model calibration. If None, uses default
        Pra River data.
    model_type : str or BaseMercuryModel, default="empirical"
        Model type to use. Options:
        - "empirical": Empirical model fitted to data (default, recommended)
        - "mechanistic": Physics-based transport model
        - "compartmental": Multi-compartment box model
        - "simplified": Simple exponential decay model
        Alternatively, pass a model instance directly.
    seed : int, default=42
        Random seed for reproducibility
    
    Examples
    --------
    >>> from mercury_package import MercurySimulator, ObservedData
    >>> import numpy as np
    >>> 
    >>> # Use default empirical model
    >>> simulator = MercurySimulator()
    >>> 
    >>> # Use mechanistic model
    >>> simulator = MercurySimulator(model_type="mechanistic")
    >>> 
    >>> # Use custom model instance
    >>> from mercury_package.models import CompartmentalMercuryModel
    >>> model = CompartmentalMercuryModel()
    >>> simulator = MercurySimulator(model=model)
    """
    
    def __init__(
        self,
        observed_data: Optional[ObservedData] = None,
        model_type: Union[str, BaseMercuryModel, type] = "empirical",
        seed: int = 42,
        **model_kwargs
    ):
        """
        Initialize the mercury simulator.
        
        Parameters
        ----------
        observed_data : ObservedData, optional
            Field observation data. If None, uses default Pra River data.
        model_type : str or BaseMercuryModel or type, default="empirical"
            Model type or instance to use. String options:
            - "empirical": Empirical model (default)
            - "mechanistic": Physics-based model
            - "compartmental": Compartmental box model
            - "simplified": Simplified exponential model
        seed : int, default=42
            Random seed for reproducibility
        **model_kwargs
            Additional keyword arguments passed to model constructor
        """
        self.observed_data = observed_data if observed_data is not None else ObservedData()
        self.seed = seed
        
        # Create model
        if isinstance(model_type, BaseMercuryModel):
            # User provided a model instance
            self.model = model_type
        elif isinstance(model_type, type):
            # User provided a model class
            self.model = model_type(observed_data=self.observed_data, **model_kwargs)
        else:
            # User provided a string
            self.model = self._create_model(model_type, **model_kwargs)
        
        # Create MC simulator with custom model
        self.mc_simulator = MonteCarloPraRiver(seed=seed, observed_data=self.observed_data)
        self.mc_simulator.model = self.model
    
    def _create_model(self, model_type: str = "empirical", **kwargs) -> BaseMercuryModel:
        """
        Create a model instance based on model type.
        
        Parameters
        ----------
        model_type : str
            Model type: "empirical", "mechanistic", "compartmental", or "simplified"
        **kwargs
            Additional arguments for model constructor
        
        Returns
        -------
        BaseMercuryModel
            Model instance
        """
        model_classes = {
            "empirical": EmpiricalMercuryModel,
            "mechanistic": MechanisticMercuryModel,
            "compartmental": CompartmentalMercuryModel,
            "simplified": SimplifiedMercuryModel,
        }
        
        if model_type not in model_classes:
            raise ValueError(
                f"Unknown model type: {model_type}. "
                f"Choose from: {list(model_classes.keys())}"
            )
        
        ModelClass = model_classes[model_type]
        return ModelClass(observed_data=self.observed_data, **kwargs)
    
    def run_simulation(
        self,
        n_iterations: int = 10000,
        time_points: Optional[np.ndarray] = None,
    ) -> Dict:
        """
        Run Monte Carlo simulation.
        
        Parameters
        ----------
        n_iterations : int, default=10000
            Number of Monte Carlo iterations
        time_points : array-like, optional
            Time points for simulation (in days). 
            Default: [0, 30, 90, 180, 365, 730, 1095, 1460, 1825]
        
        Returns
        -------
        dict
            Dictionary containing simulation results
        """
        if time_points is None:
            time_points = np.array([0, 30, 90, 180, 365, 730, 1095, 1460, 1825])
        
        return self.mc_simulator.run_simulation(n_iterations, time_points)
    
    def get_validation(self) -> Dict:
        """
        Get model validation results against observed data.
        
        Returns
        -------
        dict
            Dictionary with validation metrics (R², RMSE) for each compartment
        """
        return self.model.validate()
    
    def run_full_simulation(
        self,
        n_iterations: int = 10000,
        output_dir: str = "./results",
        generate_plots: bool = True,
        time_points: Optional[np.ndarray] = None,
    ) -> Dict:
        """
        Run complete simulation with optional visualization and reporting.
        
        Parameters
        ----------
        n_iterations : int, default=10000
            Number of Monte Carlo iterations
        output_dir : str, default="./results"
            Directory to save results
        generate_plots : bool, default=True
            Whether to generate visualization plots
        time_points : array-like, optional
            Time points for simulation (in days)
        
        Returns
        -------
        dict
            Dictionary containing simulation results
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Run simulation
        results = self.run_simulation(n_iterations, time_points)
        
        # Generate plots and reports if requested
        if generate_plots:
            try:
                # Import here to avoid circular dependencies
                from mercury_package.visualization import generate_all_plots
                from mercury_package.reporting import generate_report, export_results
                
                validation = self.get_validation()
                probs = calculate_risk_probabilities(results, time_idx=-1)
                sens = sensitivity_analysis(results, "hazard_quotient", time_idx=-1)
                
                time_pts = results["time"] if time_points is None else time_points
                
                # Generate visualizations
                generate_all_plots(
                    results, validation, probs, sens, time_pts, output_dir, model=self.model
                )
                
                # Generate reports
                generate_report(results, validation, probs, sens, output_dir)
                export_results(results, validation, probs, sens, time_pts, output_dir)
                
            except ImportError:
                # If visualization module not available, just run simulation
                print("Warning: Visualization modules not available. Skipping plots.")
        
        return results
