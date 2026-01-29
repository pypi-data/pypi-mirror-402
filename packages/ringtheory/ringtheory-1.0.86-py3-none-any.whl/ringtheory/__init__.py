"""
RingTheory 0.1 - Energy-Efficient Computing through Ring Patterns

Theory of Recursive Autopatterns (TRAP) implementation for GPU energy optimization.
"""

__version__ = "1.0.86"
__author__ = "RingTheory Team"
__license__ = "MIT"

# Импортируем только то, что реально существует
from .gpu_optimizer import (
    GPURingOptimizer,  
    gpu_energy_monitor,
    find_gpu_resonance,
    example_usage,
    get_gpu_power,
    EnergyMode,
    VortexTopology
)

from .core import (
    RingExecutor,
    find_optimal_grid_size,
    ring_resonance_score,
    is_resonant_size
)

from .monitor import (
    EnergyMonitor,
    CPUMonitor,
    GPUMonitor,
    get_energy_savings
)

__all__ = [
    'RingExecutor',
    'GPURingOptimizer',
    'EnergyMode',
    'VortexTopology',
    'EnergyMonitor',
    'CPUMonitor',
    'GPUMonitor',
    'find_optimal_grid_size',
    'ring_resonance_score',
    'is_resonant_size',
    'gpu_energy_monitor',
    'find_gpu_resonance',
    'get_gpu_power',
    'get_energy_savings',
    'example_usage'
]