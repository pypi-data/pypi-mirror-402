"""
Empirically Calibrated Mercury Model for Pra River
Directly fits observed field data using regression-based approach
"""

import numpy as np
from scipy.interpolate import interp1d
from scipy.optimize import curve_fit
from typing import Dict, Tuple, Optional
from mercury_package.models.base_model import BaseMercuryModel
from mercury_package.models.observed_data import ObservedData


class EmpiricalMercuryModel(BaseMercuryModel):
    """
    Mercury transport model calibrated to field observations
    
    Uses empirical functions fitted to field data:
    - Water: pulse-decay kinetics (release then flushing)
    - Sediment: asymptotic accumulation (approaching equilibrium)
    - Soil: linear accumulation with depth attenuation
    
    This is the default model and typically provides the best fit
    when sufficient calibration data is available.
    
    Parameters
    ----------
    observed_data : ObservedData, optional
        Field observation data. If None, uses default Pra River data.
    """
    
    def __init__(self, observed_data: Optional[ObservedData] = None):
        super().__init__(observed_data)
        self._fit_empirical_models()
        
    def _fit_empirical_models(self):
        """Fit empirical models to observed data"""
        
        # Water: C(t) = C_bg + A * (t/t_peak) * exp(1 - t/t_peak) for t > 0
        # This gives a pulse that peaks at t_peak then decays
        def water_model(t, C_bg, A, t_peak, k_decay):
            result = np.zeros_like(t, dtype=float)
            result[t == 0] = C_bg
            mask = t > 0
            normalized_t = t[mask] / t_peak
            result[mask] = C_bg + A * normalized_t * np.exp(1 - normalized_t) * np.exp(-k_decay * t[mask] / 365)
            return result
            
        # Fit water model
        try:
            popt, _ = curve_fit(water_model, self.obs.water_times, self.obs.water_conc,
                               p0=[0.002, 0.15, 180, 0.5], 
                               bounds=([0, 0, 30, 0], [0.01, 1, 365, 5]))
            self.water_params = popt
        except:
            self.water_params = [0.002, 0.12, 180, 0.8]
            
        # Sediment: C(t) = C_bg + C_max * (1 - exp(-k*t))
        def sed_model(t, C_bg, C_max, k):
            return C_bg + C_max * (1 - np.exp(-k * t / 365))
            
        try:
            popt, _ = curve_fit(sed_model, self.obs.sed_times, self.obs.sed_conc,
                               p0=[0.4, 8, 0.8])
            self.sed_params = popt
        except:
            self.sed_params = [0.4, 8.0, 0.7]
            
        # Topsoil: linear accumulation
        def soil_model(t, C_bg, rate):
            return C_bg + rate * t / 365
            
        try:
            popt, _ = curve_fit(soil_model, self.obs.topsoil_times, self.obs.topsoil_conc,
                               p0=[0.15, 0.6])
            self.topsoil_params = popt
        except:
            self.topsoil_params = [0.15, 0.57]
            
        try:
            popt, _ = curve_fit(soil_model, self.obs.subsoil_times, self.obs.subsoil_conc,
                               p0=[0.04, 0.2])
            self.subsoil_params = popt
        except:
            self.subsoil_params = [0.04, 0.21]
    
    def predict_water(self, t: np.ndarray, params: Dict = None) -> np.ndarray:
        """Predict water mercury concentration"""
        C_bg, A, t_peak, k_decay = self.water_params
        
        # Apply parameter uncertainty if provided
        if params is not None:
            release_factor = params.get("release_rate", 1.0)
            flow_factor = params.get("flow_rate", 1.0)
            A = A * release_factor / np.sqrt(flow_factor)
            
        t = np.atleast_1d(t)
        result = np.zeros_like(t, dtype=float)
        result[t == 0] = C_bg
        mask = t > 0
        if np.any(mask):
            normalized_t = t[mask] / t_peak
            result[mask] = C_bg + A * normalized_t * np.exp(1 - normalized_t) * np.exp(-k_decay * t[mask] / 365)
        return result
    
    def predict_sediment(self, t: np.ndarray, params: Dict = None) -> np.ndarray:
        """Predict sediment mercury concentration"""
        C_bg, C_max, k = self.sed_params
        
        if params is not None:
            release_factor = params.get("release_rate", 1.0)
            kd_factor = params.get("sed_kd", 1.0)
            C_max = C_max * release_factor * (kd_factor ** 0.3)
            
        t = np.atleast_1d(t)
        return C_bg + C_max * (1 - np.exp(-k * t / 365))
    
    def predict_topsoil(self, t: np.ndarray, params: Dict = None) -> np.ndarray:
        """Predict topsoil mercury concentration"""
        C_bg, rate = self.topsoil_params
        
        if params is not None:
            release_factor = params.get("release_rate", 1.0)
            flood_factor = params.get("k_flood_dep", 1.0)
            rate = rate * release_factor * flood_factor
            
        t = np.atleast_1d(t)
        return C_bg + rate * t / 365
    
    def predict_subsoil(self, t: np.ndarray, params: Dict = None) -> np.ndarray:
        """Predict subsoil mercury concentration"""
        C_bg, rate = self.subsoil_params
        
        if params is not None:
            release_factor = params.get("release_rate", 1.0)
            rate = rate * release_factor * 0.5  # Attenuation factor
            
        t = np.atleast_1d(t)
        return C_bg + rate * t / 365
    
    # validate() method is inherited from BaseMercuryModel


class MonteCarloPraRiver:
    """
    Monte Carlo simulation for mercury pollution assessment
    Using empirically calibrated model
    
    Parameters
    ----------
    seed : int, default=42
        Random seed for reproducibility
    observed_data : ObservedData, optional
        Field observation data. If None, uses default Pra River data.
    """
    
    def __init__(self, seed: int = 42, observed_data: Optional[ObservedData] = None):
        self.model = EmpiricalMercuryModel(observed_data=observed_data)
        self.rng = np.random.default_rng(seed)
        
    def run_simulation(self, n_iterations: int = 10000,
                       time_points: np.ndarray = None) -> Dict:
        """Run Monte Carlo simulation"""
        
        if time_points is None:
            time_points = np.array([0, 30, 90, 180, 365, 730, 1095, 1460, 1825])
            
        n_times = len(time_points)
        
        # Initialize results
        results = {
            "time": time_points,
            "water": np.zeros((n_times, n_iterations)),
            "sediment": np.zeros((n_times, n_iterations)),
            "topsoil": np.zeros((n_times, n_iterations)),
            "subsoil": np.zeros((n_times, n_iterations)),
            "methylmercury_water": np.zeros((n_times, n_iterations)),
            "methylmercury_fish": np.zeros((n_times, n_iterations)),
            "hazard_quotient": np.zeros((n_times, n_iterations)),
        }
        
        # Parameter distributions
        params_samples = {
            "release_rate": self.rng.lognormal(0, 0.3, n_iterations),  # relative factor
            "flow_rate": self.rng.lognormal(0, 0.25, n_iterations),  # relative factor
            "sed_kd": self.rng.lognormal(0, 0.2, n_iterations),  # relative factor
            "k_flood_dep": self.rng.lognormal(0, 0.4, n_iterations),  # relative factor
            "fish_intake": self.rng.lognormal(np.log(0.05), 0.5, n_iterations),  # kg/day
            "water_intake": np.clip(self.rng.normal(2.0, 0.5, n_iterations), 0.5, 5.0),  # L/day
            "body_weight": np.clip(self.rng.normal(70, 15, n_iterations), 30, 150),  # kg
            "methylation_rate": self.rng.uniform(0.01, 0.05, n_iterations),
            "baf": self.rng.lognormal(np.log(1e5), 0.5, n_iterations),  # bioaccumulation factor
        }
        
        results["parameters"] = params_samples
        
        # Run simulations
        for i in range(n_iterations):
            params = {k: v[i] for k, v in params_samples.items()}
            
            # Concentrations
            results["water"][:, i] = self.model.predict_water(time_points, params)
            results["sediment"][:, i] = self.model.predict_sediment(time_points, params)
            results["topsoil"][:, i] = self.model.predict_topsoil(time_points, params)
            results["subsoil"][:, i] = self.model.predict_subsoil(time_points, params)
            
            # Methylmercury and fish
            mehg_rate = params["methylation_rate"]
            baf = params["baf"]
            results["methylmercury_water"][:, i] = results["water"][:, i] * mehg_rate
            results["methylmercury_fish"][:, i] = results["methylmercury_water"][:, i] * baf / 1000
            
            # Human health risk
            fish_intake = params["fish_intake"]
            water_intake = params["water_intake"]
            body_weight = params["body_weight"]
            
            # Exposure (μg/kg-day)
            fish_exp = results["methylmercury_fish"][:, i] * fish_intake * 1000 / body_weight
            water_exp = results["water"][:, i] * water_intake * 1000 / body_weight
            total_exp = fish_exp + water_exp
            
            # Hazard Quotient (RfD = 0.1 μg/kg-day for MeHg)
            results["hazard_quotient"][:, i] = total_exp / 0.1
            
        return results
    
    def get_validation(self) -> Dict:
        """Get model validation results"""
        return self.model.validate()


# Regulatory thresholds
THRESHOLDS = {
    "water_who": 0.001,  # mg/L
    "water_epa": 0.002,  # mg/L
    "water_ghana": 0.001,  # mg/L
    "sediment_tec": 0.18,  # mg/kg
    "sediment_pec": 1.06,  # mg/kg
    "sediment_sec": 2.0,  # mg/kg
    "soil_agri": 1.0,  # mg/kg
    "soil_residential": 23,  # mg/kg
    "fish_epa": 0.3,  # mg/kg
    "fish_fda": 1.0,  # mg/kg
    "hq_safe": 1.0,
    "hq_concern": 10.0
}


def calculate_risk_probabilities(results: Dict, time_idx: int = -1) -> Dict:
    """Calculate exceedance probabilities"""
    probs = {}
    
    water = results["water"][time_idx, :]
    sed = results["sediment"][time_idx, :]
    topsoil = results["topsoil"][time_idx, :]
    fish = results["methylmercury_fish"][time_idx, :]
    hq = results["hazard_quotient"][time_idx, :]
    
    probs["Water > WHO (0.001 mg/L)"] = np.mean(water > THRESHOLDS["water_who"]) * 100
    probs["Water > EPA (0.002 mg/L)"] = np.mean(water > THRESHOLDS["water_epa"]) * 100
    probs["Sediment > TEC (0.18 mg/kg)"] = np.mean(sed > THRESHOLDS["sediment_tec"]) * 100
    probs["Sediment > PEC (1.06 mg/kg)"] = np.mean(sed > THRESHOLDS["sediment_pec"]) * 100
    probs["Sediment > SEC (2.0 mg/kg)"] = np.mean(sed > THRESHOLDS["sediment_sec"]) * 100
    probs["Topsoil > Agricultural (1.0 mg/kg)"] = np.mean(topsoil > THRESHOLDS["soil_agri"]) * 100
    probs["Fish > EPA (0.3 mg/kg)"] = np.mean(fish > THRESHOLDS["fish_epa"]) * 100
    probs["Fish > FDA (1.0 mg/kg)"] = np.mean(fish > THRESHOLDS["fish_fda"]) * 100
    probs["HQ > 1 (health risk)"] = np.mean(hq > THRESHOLDS["hq_safe"]) * 100
    probs["HQ > 10 (severe risk)"] = np.mean(hq > THRESHOLDS["hq_concern"]) * 100
    
    return probs


def sensitivity_analysis(results: Dict, output_key: str, time_idx: int = -1) -> Dict:
    """Spearman correlation sensitivity analysis"""
    from scipy import stats
    
    output = results[output_key][time_idx, :]
    sensitivities = {}
    
    for param, data in results["parameters"].items():
        corr, _ = stats.spearmanr(data, output)
        sensitivities[param] = corr if not np.isnan(corr) else 0.0
        
    return dict(sorted(sensitivities.items(), key=lambda x: abs(x[1]), reverse=True))
