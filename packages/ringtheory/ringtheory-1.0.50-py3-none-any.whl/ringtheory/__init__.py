"""
RingTheory 0.1 - Energy-Efficient Computing through Ring Patterns

Theory of Recursive Autopatterns (TRAP) implementation for GPU energy optimization.
"""

__version__ = "1.0.50"
__author__ = "RingTheory Team"
__license__ = "MIT"

from .core import (
    RingExecutor,
    find_optimal_grid_size,
    ring_resonance_score,
    is_resonant_size
)

from .gpu_optimizer import (
    GPURingOptimizer,  
    gpu_energy_monitor,
    find_gpu_resonance
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
    'EnergyMonitor',
    'find_optimal_grid_size',
    'ring_resonance_score',
    'is_resonant_size',
    'optimize_cuda_kernel',
    'gpu_energy_monitor',
    'find_gpu_resonance',
    'get_energy_savings',
'example_usage' 
]