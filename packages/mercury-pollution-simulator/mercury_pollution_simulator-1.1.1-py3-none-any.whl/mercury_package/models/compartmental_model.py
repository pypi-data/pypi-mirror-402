"""
Compartmental/Box Model for Mercury Transport

A simplified multi-compartment model treating each environmental
compartment as a well-mixed box with exchange between compartments.
"""

import numpy as np
from typing import Dict, Optional
from scipy.linalg import expm
from mercury_package.models.base_model import BaseMercuryModel
from mercury_package.models.observed_data import ObservedData


class CompartmentalMercuryModel(BaseMercuryModel):
    """
    Compartmental box model for mercury transport.
    
    Treats the system as interconnected well-mixed compartments:
    - Water compartment
    - Sediment compartment
    - Topsoil compartment
    - Subsoil compartment
    
    Mass transfer between compartments follows first-order kinetics.
    
    Parameters
    ----------
    observed_data : ObservedData, optional
        Field observation data for calibration
    k_water_sed : float, default=0.01
        Transfer rate from water to sediment (1/day)
    k_sed_water : float, default=0.001
        Transfer rate from sediment to water (1/day)
    k_water_soil : float, default=0.005
        Transfer rate from water to topsoil (1/day)
    k_soil_sub : float, default=0.0005
        Transfer rate from topsoil to subsoil (1/day)
    k_decay : float, default=0.001
        Decay rate in all compartments (1/day)
    """
    
    def __init__(
        self,
        observed_data: Optional[ObservedData] = None,
        k_water_sed: float = 0.01,
        k_sed_water: float = 0.001,
        k_water_soil: float = 0.005,
        k_soil_sub: float = 0.0005,
        k_decay: float = 0.001,
    ):
        super().__init__(observed_data)
        
        # Transfer rates (1/day)
        self.k_water_sed = k_water_sed
        self.k_sed_water = k_sed_water
        self.k_water_soil = k_water_soil
        self.k_soil_sub = k_soil_sub
        self.k_decay = k_decay
        
        # Compartment volumes (relative)
        self.V_water = 1.0
        self.V_sediment = 0.1
        self.V_topsoil = 0.05
        self.V_subsoil = 0.02
        
        # Calibrate from observations
        self._calibrate_from_observations()
    
    def _calibrate_from_observations(self):
        """Calibrate transfer rates from observed data"""
        if len(self.obs.water_conc) > 1 and len(self.obs.sed_conc) > 1:
            # Estimate water-to-sediment transfer
            water_peak = np.max(self.obs.water_conc)
            sed_increase = self.obs.sed_conc[-1] - self.obs.sed_conc[0]
            total_time = self.obs.sed_times[-1] / 365  # years
            
            if total_time > 0 and sed_increase > 0:
                # Rough calibration
                self.k_water_sed = min(0.1, sed_increase / (water_peak * total_time * 365) / 10)
    
    def _solve_compartmental(self, t: np.ndarray, release_rate: float = 0.1, release_duration: float = 180.0):
        """
        Solve compartmental model using matrix exponential approach.
        
        dC/dt = A*C + S
        where C = [C_water, C_sediment, C_topsoil, C_subsoil]^T
        """
        # Initial conditions
        C0_water = self.obs.water_conc[0] if len(self.obs.water_conc) > 0 else 0.002
        C0_sed = self.obs.sed_conc[0] if len(self.obs.sed_conc) > 0 else 0.4
        C0_topsoil = self.obs.topsoil_conc[0] if len(self.obs.topsoil_conc) > 0 else 0.15
        C0_subsoil = self.obs.subsoil_conc[0] if len(self.obs.subsoil_conc) > 0 else 0.04
        
        C0 = np.array([C0_water, C0_sed, C0_topsoil, C0_subsoil])
        
        # Transfer matrix A
        # Water: -outflows - decay
        # Sediment: +inflow from water - outflow to water - decay
        # Topsoil: +inflow from water - outflow to subsoil - decay
        # Subsoil: +inflow from topsoil - decay
        
        A = np.array([
            [-(self.k_water_sed + self.k_water_soil + self.k_decay), self.k_sed_water, 0, 0],
            [self.k_water_sed * self.V_water / self.V_sediment, -(self.k_sed_water + self.k_decay), 0, 0],
            [self.k_water_soil * self.V_water / self.V_topsoil, 0, -(self.k_soil_sub + self.k_decay), 0],
            [0, 0, self.k_soil_sub * self.V_topsoil / self.V_subsoil, -self.k_decay]
        ])
        
        # Source vector (release to water)
        results = np.zeros((len(t), 4))
        
        for i, ti in enumerate(t):
            # Source term
            if ti <= release_duration:
                S = np.array([release_rate * 1000 / (22.0 * 86400), 0, 0, 0])  # mg/L/day
            else:
                S = np.array([0, 0, 0, 0])
            
            # Solve: C(t) = exp(A*t)*C0 + integral(exp(A*(t-s))*S ds)
            # Simplified: use exponential matrix for homogeneous part
            from scipy.linalg import expm
            
            if ti == 0:
                results[i, :] = C0
            else:
                # Homogeneous solution
                try:
                    C_hom = expm(A * ti) @ C0
                except:
                    # Fallback if matrix exponential fails
                    C_hom = C0
                
                # Particular solution (simplified)
                if np.any(S > 0):
                    # Steady-state particular solution: -A^(-1)*S
                    try:
                        C_part = -np.linalg.solve(A, S)
                        # Apply decay over time
                        C_part = C_part * (1 - np.exp(-self.k_decay * ti))
                    except:
                        C_part = np.zeros(4)
                else:
                    C_part = np.zeros(4)
                
                results[i, :] = C_hom + C_part
        
        return results
    
    def predict_water(self, t: np.ndarray, params: Optional[Dict] = None) -> np.ndarray:
        """Predict water mercury concentration"""
        t = np.atleast_1d(t)
        
        release_rate = 0.1
        release_duration = 180.0
        if params is not None:
            release_rate = params.get("release_rate", 1.0) * 0.1
            flow_factor = params.get("flow_rate", 1.0)
            # Adjust transfer rates based on flow
            self.k_water_sed = 0.01 / np.sqrt(flow_factor)
        
        solution = self._solve_compartmental(t, release_rate, release_duration)
        return solution[:, 0]
    
    def predict_sediment(self, t: np.ndarray, params: Optional[Dict] = None) -> np.ndarray:
        """Predict sediment mercury concentration"""
        t = np.atleast_1d(t)
        
        release_rate = 0.1
        release_duration = 180.0
        if params is not None:
            release_rate = params.get("release_rate", 1.0) * 0.1
            kd_factor = params.get("sed_kd", 1.0)
            self.k_water_sed = 0.01 * kd_factor
        
        solution = self._solve_compartmental(t, release_rate, release_duration)
        return solution[:, 1]
    
    def predict_topsoil(self, t: np.ndarray, params: Optional[Dict] = None) -> np.ndarray:
        """Predict topsoil mercury concentration"""
        t = np.atleast_1d(t)
        
        release_rate = 0.1
        release_duration = 180.0
        if params is not None:
            release_rate = params.get("release_rate", 1.0) * 0.1
            flood_factor = params.get("k_flood_dep", 1.0)
            self.k_water_soil = 0.005 * flood_factor
        
        solution = self._solve_compartmental(t, release_rate, release_duration)
        return solution[:, 2]
    
    def predict_subsoil(self, t: np.ndarray, params: Optional[Dict] = None) -> np.ndarray:
        """Predict subsoil mercury concentration"""
        t = np.atleast_1d(t)
        
        release_rate = 0.1
        release_duration = 180.0
        if params is not None:
            release_rate = params.get("release_rate", 1.0) * 0.1
        
        solution = self._solve_compartmental(t, release_rate, release_duration)
        return solution[:, 3]
