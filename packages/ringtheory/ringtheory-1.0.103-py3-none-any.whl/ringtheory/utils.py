import numpy as np
import time
from typing import Callable, List, Dict, Any

def benchmark_operation(operation: Callable, 
                       *args, 
                       repetitions: int = 100,
                       warmup: int = 10) -> Dict[str, Any]:
    """
    Benchmark an operation for performance and energy efficiency.
    
    Args:
        operation: Function to benchmark
        *args: Arguments to pass to operation
        repetitions: Number of repetitions
        warmup: Warmup iterations
        
    Returns:
        Benchmark results
    """
    # Warmup
    for _ in range(warmup):
        operation(*args)
    
    # Actual benchmark
    start_time = time.time()
    start_memory = _get_memory_usage()
    
    for _ in range(repetitions):
        result = operation(*args)
    
    end_time = time.time()
    end_memory = _get_memory_usage()
    
    duration = end_time - start_time
    ops_per_second = repetitions / duration
    
    return {
        'duration': duration,
        'operations_per_second': ops_per_second,
        'memory_used_mb': end_memory - start_memory,
        'result': result
    }


def _get_memory_usage() -> float:
    """Get current memory usage in MB."""
    import psutil
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024


def find_optimal_chunk_size(data_size: int, 
                           memory_limit_mb: int = 1024,
                           dtype=np.float32) -> int:
    """
    Find optimal chunk size for ring computations.
    
    Args:
        data_size: Total data size
        memory_limit_mb: Available memory in MB
        dtype: Data type
        
    Returns:
        Optimal chunk size
    """
    # Размер элемента в байтах
    element_size = np.dtype(dtype).itemsize
    
    # Максимальное количество элементов в памяти
    max_elements = (memory_limit_mb * 1024 * 1024) // element_size
    
    # Находим ближайший резонансный размер, меньший max_elements
    resonant_sizes = [25, 50, 100, 150, 200, 300, 400, 600, 800, 1024, 2048]
    
    optimal = 200  # По умолчанию
    
    for size in resonant_sizes:
        if size <= min(data_size, max_elements):
            optimal = size
        else:
            break
    
    return optimal


def calculate_energy_score(performance: float, 
                          power_usage: float,
                          memory_efficiency: float = 1.0) -> float:
    """
    Calculate energy efficiency score.
    
    Args:
        performance: Operations per second
        power_usage: Power consumption in watts
        memory_efficiency: Memory efficiency factor (0.0 to 1.0)
        
    Returns:
        Energy score (higher is better)
    """
    if power_usage <= 0:
        return 0.0
    
    # Базовый score: производительность на ватт
    base_score = performance / power_usage
    
    # Корректируем с учетом эффективности памяти
    adjusted_score = base_score * memory_efficiency
    
    return adjusted_score


def validate_resonant_size(size: int) -> bool:
    """
    Validate if size follows ring theory patterns.
    
    Args:
        size: Size to validate
        
    Returns:
        True if size is valid according to ring theory
    """
    # Проверяем делители и простоту
    if size <= 0:
        return False
    
    # Предпочитаем размеры, которые делятся на малые простые числа
    preferred_factors = [2, 3, 5, 7]
    
    temp = size
    for factor in preferred_factors:
        while temp % factor == 0:
            temp //= factor
    
    # Если остался 1, значит размер состоит только из предпочитаемых множителей
    if temp == 1:
        return True
    
    # Также принимаем размеры близкие к резонансным
    resonant_sizes = [25, 50, 100, 150, 200, 300, 400, 600, 800]
    distances = [abs(size - rs) for rs in resonant_sizes]
    
    # Если ближе чем на 10% к резонансному размеру
    min_distance = min(distances)
    closest_size = resonant_sizes[distances.index(min_distance)]
    
    if min_distance / closest_size < 0.1:
        return True
    
    return False