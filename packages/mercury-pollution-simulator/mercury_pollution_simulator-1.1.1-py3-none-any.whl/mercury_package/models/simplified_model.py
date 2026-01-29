"""
Simplified Exponential Decay Model for Mercury

A simple model using exponential decay functions for quick assessments.
Useful when detailed calibration data is not available.
"""

import numpy as np
from typing import Dict, Optional
from mercury_package.models.base_model import BaseMercuryModel
from mercury_package.models.observed_data import ObservedData


class SimplifiedMercuryModel(BaseMercuryModel):
    """
    Simplified exponential decay model.
    
    Uses simple exponential functions:
    - Water: Exponential decay after initial pulse
    - Sediment: Exponential approach to equilibrium
    - Soil: Linear accumulation with exponential decay
    
    This model is useful for quick assessments when limited data is available.
    
    Parameters
    ----------
    observed_data : ObservedData, optional
        Field observation data for calibration
    water_half_life : float, default=180.0
        Water concentration half-life (days)
    sediment_equilibrium : float, default=8.0
        Sediment equilibrium concentration (mg/kg)
    soil_accumulation_rate : float, default=0.6
        Soil accumulation rate (mg/kg/year)
    """
    
    def __init__(
        self,
        observed_data: Optional[ObservedData] = None,
        water_half_life: float = 180.0,
        sediment_equilibrium: float = 8.0,
        soil_accumulation_rate: float = 0.6,
    ):
        super().__init__(observed_data)
        
        # Model parameters
        self.water_half_life = water_half_life  # days
        self.sediment_equilibrium = sediment_equilibrium  # mg/kg
        self.soil_accumulation_rate = soil_accumulation_rate  # mg/kg/year
        
        # Calculate decay rates
        self.k_water = np.log(2) / water_half_life  # 1/day
        
        # Calibrate from observations if available
        self._calibrate_from_observations()
    
    def _calibrate_from_observations(self):
        """Calibrate parameters from observed data"""
        # Water half-life from decline
        if len(self.obs.water_conc) > 1:
            peak_idx = np.argmax(self.obs.water_conc)
            if peak_idx < len(self.obs.water_conc) - 1:
                peak_conc = self.obs.water_conc[peak_idx]
                later_conc = self.obs.water_conc[peak_idx + 1]
                dt = self.obs.water_times[peak_idx + 1] - self.obs.water_times[peak_idx]
                
                if later_conc > 0 and peak_conc > later_conc and dt > 0:
                    k = -np.log(later_conc / peak_conc) / dt
                    self.k_water = k
                    self.water_half_life = np.log(2) / k if k > 0 else 180.0
        
        # Sediment equilibrium
        if len(self.obs.sed_conc) > 0:
            self.sediment_equilibrium = np.max(self.obs.sed_conc) * 1.1
        
        # Soil accumulation rate
        if len(self.obs.topsoil_conc) > 1:
            initial = self.obs.topsoil_conc[0]
            final = self.obs.topsoil_conc[-1]
            time_years = self.obs.topsoil_times[-1] / 365
            
            if time_years > 0:
                self.soil_accumulation_rate = (final - initial) / time_years
    
    def predict_water(self, t: np.ndarray, params: Optional[Dict] = None) -> np.ndarray:
        """Predict water mercury concentration"""
        t = np.atleast_1d(t)
        
        # Initial concentration
        C0 = self.obs.water_conc[0] if len(self.obs.water_conc) > 0 else 0.002
        
        # Peak concentration (from observations or default)
        if len(self.obs.water_conc) > 1:
            C_peak = np.max(self.obs.water_conc)
            t_peak = self.obs.water_times[np.argmax(self.obs.water_conc)]
        else:
            C_peak = 0.072
            t_peak = 180.0
        
        # Adjust for parameter uncertainty
        if params is not None:
            release_factor = params.get("release_rate", 1.0)
            flow_factor = params.get("flow_rate", 1.0)
            C_peak = C_peak * release_factor / np.sqrt(flow_factor)
            k = self.k_water / flow_factor
        else:
            k = self.k_water
        
        result = np.zeros_like(t, dtype=float)
        
        for i, ti in enumerate(t):
            if ti <= t_peak:
                # Rising phase (linear to peak)
                result[i] = C0 + (C_peak - C0) * (ti / t_peak)
            else:
                # Decay phase
                result[i] = C_peak * np.exp(-k * (ti - t_peak))
        
        return result
    
    def predict_sediment(self, t: np.ndarray, params: Optional[Dict] = None) -> np.ndarray:
        """Predict sediment mercury concentration"""
        t = np.atleast_1d(t)
        
        # Initial concentration
        C0 = self.obs.sed_conc[0] if len(self.obs.sed_conc) > 0 else 0.4
        
        # Equilibrium concentration
        C_eq = self.sediment_equilibrium
        
        # Approach rate (fitted or default)
        k_approach = 0.7 / 365  # 1/day
        
        # Adjust for parameter uncertainty
        if params is not None:
            release_factor = params.get("release_rate", 1.0)
            kd_factor = params.get("sed_kd", 1.0)
            C_eq = C0 + (C_eq - C0) * release_factor * (kd_factor ** 0.3)
            k_approach = k_approach * kd_factor
        
        # Exponential approach to equilibrium
        result = C_eq - (C_eq - C0) * np.exp(-k_approach * t)
        
        return result
    
    def predict_topsoil(self, t: np.ndarray, params: Optional[Dict] = None) -> np.ndarray:
        """Predict topsoil mercury concentration"""
        t = np.atleast_1d(t)
        
        # Initial concentration
        C0 = self.obs.topsoil_conc[0] if len(self.obs.topsoil_conc) > 0 else 0.15
        
        # Accumulation rate
        rate = self.soil_accumulation_rate  # mg/kg/year
        
        # Adjust for parameter uncertainty
        if params is not None:
            release_factor = params.get("release_rate", 1.0)
            flood_factor = params.get("k_flood_dep", 1.0)
            rate = rate * release_factor * flood_factor
        
        # Linear accumulation
        result = C0 + rate * t / 365
        
        return result
    
    def predict_subsoil(self, t: np.ndarray, params: Optional[Dict] = None) -> np.ndarray:
        """Predict subsoil mercury concentration"""
        t = np.atleast_1d(t)
        
        # Initial concentration
        C0 = self.obs.subsoil_conc[0] if len(self.obs.subsoil_conc) > 0 else 0.04
        
        # Accumulation rate (lower than topsoil)
        rate = self.soil_accumulation_rate * 0.35  # mg/kg/year
        
        # Adjust for parameter uncertainty
        if params is not None:
            release_factor = params.get("release_rate", 1.0)
            rate = rate * release_factor * 0.5  # Attenuation factor
        
        # Linear accumulation
        result = C0 + rate * t / 365
        
        return result
