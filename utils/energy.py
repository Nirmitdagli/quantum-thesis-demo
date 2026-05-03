"""Energy estimation model for thesis experiments.

Model: Energy = Runtime x Power x PUE
Returns a (low, high) range in joules.
"""

import os
import sys
from typing import Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def estimate_energy(runtime_seconds: float) -> Tuple[float, float]:
    """Estimate energy consumption range using thesis cloud energy model.

    Returns:
        (energy_low, energy_high) in joules.
    """
    energy_low = runtime_seconds * config.POWER_LOW_W * config.PUE
    energy_high = runtime_seconds * config.POWER_HIGH_W * config.PUE
    return energy_low, energy_high
