"""
Mechanistic/Physical Transport Model for Mercury

Based on advection-dispersion-reaction equations and mass balance principles.
Uses physical parameters like flow rate, dispersion, settling velocity, etc.
"""

import numpy as np
from typing import Dict, Optional
from scipy.integrate import odeint
from mercury_package.models.base_model import BaseMercuryModel
from mercury_package.models.observed_data import ObservedData


class MechanisticMercuryModel(BaseMercuryModel):
    """
    Mechanistic model based on physical transport equations.
    
    Uses advection-dispersion-reaction equations with:
    - Advective transport (river flow)
    - Dispersion (mixing)
    - Settling to sediment
    - Flooding to soil
    - First-order decay
    
    Parameters
    ----------
    observed_data : ObservedData, optional
        Field observation data for calibration
    flow_rate : float, default=22.0
        River flow rate (m³/s)
    velocity : float, default=0.5
        Flow velocity (m/s)
    dispersion : float, default=50.0
        Dispersion coefficient (m²/s)
    settling_rate : float, default=0.001
        Settling velocity (m/s)
    flood_rate : float, default=0.0001
        Flooding deposition rate (1/day)
    decay_rate : float, default=0.001
        First-order decay rate (1/day)
    """
    
    def __init__(
        self,
        observed_data: Optional[ObservedData] = None,
        flow_rate: float = 22.0,
        velocity: float = 0.5,
        dispersion: float = 50.0,
        settling_rate: float = 0.001,
        flood_rate: float = 0.0001,
        decay_rate: float = 0.001,
    ):
        super().__init__(observed_data)
        
        # Physical parameters
        self.flow_rate = flow_rate  # m³/s
        self.velocity = velocity  # m/s
        self.dispersion = dispersion  # m²/s
        self.settling_rate = settling_rate  # m/s
        self.flood_rate = flood_rate  # 1/day
        self.decay_rate = decay_rate  # 1/day
        
        # Calibrate from observed data if available
        self._calibrate_from_observations()
    
    def _calibrate_from_observations(self):
        """Calibrate model parameters from observed data"""
        if len(self.obs.water_conc) > 1:
            # Estimate decay from water concentration decline
            water_peak_idx = np.argmax(self.obs.water_conc)
            if water_peak_idx < len(self.obs.water_conc) - 1:
                peak_time = self.obs.water_times[water_peak_idx]
                later_time = self.obs.water_times[water_peak_idx + 1]
                peak_conc = self.obs.water_conc[water_peak_idx]
                later_conc = self.obs.water_conc[water_peak_idx + 1]
                
                if later_conc > 0 and peak_conc > later_conc:
                    dt = (later_time - peak_time) / 365  # years
                    self.decay_rate = -np.log(later_conc / peak_conc) / dt / 365  # 1/day
        
        # Estimate settling from sediment accumulation
        if len(self.obs.sed_conc) > 1:
            initial_sed = self.obs.sed_conc[0]
            final_sed = self.obs.sed_conc[-1]
            final_time = self.obs.sed_times[-1] / 365  # years
            
            if final_time > 0 and final_sed > initial_sed:
                # Rough estimate of settling contribution
                self.settling_rate = min(0.01, (final_sed - initial_sed) / final_time / 1000)
    
    def _solve_ode_system(self, t: np.ndarray, release_rate: float = 0.1, release_duration: float = 180.0):
        """
        Solve ODE system for mercury transport.
        
        State variables:
        - C_water: Water concentration (mg/L)
        - C_sediment: Sediment concentration (mg/kg)
        - C_topsoil: Topsoil concentration (mg/kg)
        - C_subsoil: Subsoil concentration (mg/kg)
        """
        def dCdt(C, t):
            C_w, C_s, C_ts, C_ss = C
            
            # Source term (release)
            if t <= release_duration:
                source = release_rate * 1000 / (self.flow_rate * 86400)  # mg/L/day
            else:
                source = 0.0
            
            # Water: source - settling - decay - outflow
            dCw = source - self.settling_rate * C_w - self.decay_rate * C_w - self.velocity * C_w / 20000
            
            # Sediment: settling from water - burial
            dCs = self.settling_rate * C_w * 1000 - 0.0001 * C_s
            
            # Topsoil: flooding from water - leaching to subsoil
            dCts = self.flood_rate * C_w * 1000 - 0.00005 * C_ts
            
            # Subsoil: leaching from topsoil
            dCss = 0.00005 * C_ts - 0.00001 * C_ss
            
            return [dCw, dCs, dCts, dCss]
        
        # Initial conditions from observed data
        C0_water = self.obs.water_conc[0] if len(self.obs.water_conc) > 0 else 0.002
        C0_sed = self.obs.sed_conc[0] if len(self.obs.sed_conc) > 0 else 0.4
        C0_topsoil = self.obs.topsoil_conc[0] if len(self.obs.topsoil_conc) > 0 else 0.15
        C0_subsoil = self.obs.subsoil_conc[0] if len(self.obs.subsoil_conc) > 0 else 0.04
        
        C0 = [C0_water, C0_sed, C0_topsoil, C0_subsoil]
        
        # Solve ODE
        solution = odeint(dCdt, C0, t)
        
        return solution
    
    def predict_water(self, t: np.ndarray, params: Optional[Dict] = None) -> np.ndarray:
        """Predict water mercury concentration"""
        t = np.atleast_1d(t)
        
        # Adjust parameters if provided
        release_rate = 0.1
        release_duration = 180.0
        if params is not None:
            release_rate = params.get("release_rate", 1.0) * 0.1
            flow_factor = params.get("flow_rate", 1.0)
            self.flow_rate = 22.0 * flow_factor
        
        solution = self._solve_ode_system(t, release_rate, release_duration)
        return solution[:, 0]
    
    def predict_sediment(self, t: np.ndarray, params: Optional[Dict] = None) -> np.ndarray:
        """Predict sediment mercury concentration"""
        t = np.atleast_1d(t)
        
        release_rate = 0.1
        release_duration = 180.0
        if params is not None:
            release_rate = params.get("release_rate", 1.0) * 0.1
            kd_factor = params.get("sed_kd", 1.0)
            self.settling_rate = 0.001 * kd_factor
        
        solution = self._solve_ode_system(t, release_rate, release_duration)
        return solution[:, 1]
    
    def predict_topsoil(self, t: np.ndarray, params: Optional[Dict] = None) -> np.ndarray:
        """Predict topsoil mercury concentration"""
        t = np.atleast_1d(t)
        
        release_rate = 0.1
        release_duration = 180.0
        if params is not None:
            release_rate = params.get("release_rate", 1.0) * 0.1
            flood_factor = params.get("k_flood_dep", 1.0)
            self.flood_rate = 0.0001 * flood_factor
        
        solution = self._solve_ode_system(t, release_rate, release_duration)
        return solution[:, 2]
    
    def predict_subsoil(self, t: np.ndarray, params: Optional[Dict] = None) -> np.ndarray:
        """Predict subsoil mercury concentration"""
        t = np.atleast_1d(t)
        
        release_rate = 0.1
        release_duration = 180.0
        if params is not None:
            release_rate = params.get("release_rate", 1.0) * 0.1
        
        solution = self._solve_ode_system(t, release_rate, release_duration)
        return solution[:, 3]
