"""
Mercury transport models

This module provides multiple model implementations for mercury transport simulation:
- EmpiricalMercuryModel: Data-driven model fitted to observations (default, recommended)
- MechanisticMercuryModel: Physics-based model using transport equations
- CompartmentalMercuryModel: Multi-compartment box model
- SimplifiedMercuryModel: Simple exponential decay model for quick assessments
"""

from mercury_package.models.empirical_model import (
    EmpiricalMercuryModel,
    MonteCarloPraRiver,
    THRESHOLDS,
    calculate_risk_probabilities,
    sensitivity_analysis,
)
from mercury_package.models.observed_data import ObservedData
from mercury_package.models.base_model import BaseMercuryModel
from mercury_package.models.mechanistic_model import MechanisticMercuryModel
from mercury_package.models.compartmental_model import CompartmentalMercuryModel
from mercury_package.models.simplified_model import SimplifiedMercuryModel

__all__ = [
    "BaseMercuryModel",
    "EmpiricalMercuryModel",
    "MechanisticMercuryModel",
    "CompartmentalMercuryModel",
    "SimplifiedMercuryModel",
    "ObservedData",
    "MonteCarloPraRiver",
    "THRESHOLDS",
    "calculate_risk_probabilities",
    "sensitivity_analysis",
]
