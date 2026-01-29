"""
Observed field data used by models for calibration/validation.

This lives in its own module to avoid circular imports between:
- `base_model.py` (defines BaseMercuryModel)
- `empirical_model.py` (implements EmpiricalMercuryModel)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ObservedData:
    """Field observations from Pra River mercury monitoring."""

    # Water column (mg/L)
    water_times = np.array([0, 180, 365, 1095, 1825])  # days
    water_conc = np.array([0.002, 0.072, 0.054, 0.031, 0.018])

    # Sediment (mg/kg)
    sed_times = np.array([0, 180, 365, 1095, 1825])
    sed_conc = np.array([0.4, 3.2, 5.1, 6.8, 7.6])

    # Topsoil (mg/kg)
    topsoil_times = np.array([0, 365, 1825])
    topsoil_conc = np.array([0.15, 2.1, 3.0])

    # Subsoil (mg/kg)
    subsoil_times = np.array([0, 365, 1825])
    subsoil_conc = np.array([0.04, 0.5, 1.1])

