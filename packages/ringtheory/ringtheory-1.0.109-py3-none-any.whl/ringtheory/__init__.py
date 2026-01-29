"""
RingTheory 1.0 - High-Precision Energy-Efficient Computing
Implementation of Recursive Autopattern Theory for GPU optimization
"""

__version__ = "1.0.109"
__author__ = "RingTheory Team"
__license__ = "MIT"

from .gpu_optimizer import (
    GPURingOptimizer,
    EnergyMode,
    gpu_energy_monitor,
    get_gpu_power,
    verify_precision_thorough,
    calculate_ring_parameters,
    create_ring_pattern,
    calculate_informational_distance
)

__all__ = [
    'GPURingOptimizer',
    'EnergyMode',
    'gpu_energy_monitor',
    'get_gpu_power',
    'verify_precision_thorough',
    'calculate_ring_parameters',
    'create_ring_pattern',
    'calculate_informational_distance'
]