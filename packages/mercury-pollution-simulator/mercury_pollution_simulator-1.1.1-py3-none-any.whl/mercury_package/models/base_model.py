"""
Base model interface for mercury transport models
All models should inherit from this base class
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
import numpy as np
from mercury_package.models.observed_data import ObservedData


class BaseMercuryModel(ABC):
    """
    Abstract base class for mercury transport models.
    
    All mercury models must implement these methods to be compatible
    with the simulator framework.
    """
    
    def __init__(self, observed_data: Optional[ObservedData] = None):
        """
        Initialize the model.
        
        Parameters
        ----------
        observed_data : ObservedData, optional
            Field observation data for calibration/validation
        """
        self.obs = observed_data if observed_data is not None else ObservedData()
    
    @abstractmethod
    def predict_water(self, t: np.ndarray, params: Optional[Dict] = None) -> np.ndarray:
        """
        Predict water mercury concentration over time.
        
        Parameters
        ----------
        t : array-like
            Time points (days)
        params : dict, optional
            Parameter values for uncertainty propagation
        
        Returns
        -------
        array
            Water mercury concentrations (mg/L)
        """
        pass
    
    @abstractmethod
    def predict_sediment(self, t: np.ndarray, params: Optional[Dict] = None) -> np.ndarray:
        """
        Predict sediment mercury concentration over time.
        
        Parameters
        ----------
        t : array-like
            Time points (days)
        params : dict, optional
            Parameter values for uncertainty propagation
        
        Returns
        -------
        array
            Sediment mercury concentrations (mg/kg)
        """
        pass
    
    @abstractmethod
    def predict_topsoil(self, t: np.ndarray, params: Optional[Dict] = None) -> np.ndarray:
        """
        Predict topsoil mercury concentration over time.
        
        Parameters
        ----------
        t : array-like
            Time points (days)
        params : dict, optional
            Parameter values for uncertainty propagation
        
        Returns
        -------
        array
            Topsoil mercury concentrations (mg/kg)
        """
        pass
    
    @abstractmethod
    def predict_subsoil(self, t: np.ndarray, params: Optional[Dict] = None) -> np.ndarray:
        """
        Predict subsoil mercury concentration over time.
        
        Parameters
        ----------
        t : array-like
            Time points (days)
        params : dict, optional
            Parameter values for uncertainty propagation
        
        Returns
        -------
        array
            Subsoil mercury concentrations (mg/kg)
        """
        pass
    
    def validate(self) -> Dict:
        """
        Validate model against observed data.
        
        Returns
        -------
        dict
            Dictionary with validation metrics (R², RMSE) for each compartment
        """
        results = {}
        
        for comp in ["water", "sediment", "topsoil", "subsoil"]:
            if comp == "water":
                times = self.obs.water_times
                observed = self.obs.water_conc
                predicted = self.predict_water(times)
            elif comp == "sediment":
                times = self.obs.sed_times
                observed = self.obs.sed_conc
                predicted = self.predict_sediment(times)
            elif comp == "topsoil":
                times = self.obs.topsoil_times
                observed = self.obs.topsoil_conc
                predicted = self.predict_topsoil(times)
            else:  # subsoil
                times = self.obs.subsoil_times
                observed = self.obs.subsoil_conc
                predicted = self.predict_subsoil(times)
            
            rmse = np.sqrt(np.mean((predicted - observed)**2))
            ss_res = np.sum((predicted - observed)**2)
            ss_tot = np.sum((observed - np.mean(observed))**2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
            
            results[comp] = {
                "times": times,
                "observed": observed,
                "predicted": predicted,
                "rmse": rmse,
                "r2": r2
            }
        
        return results
