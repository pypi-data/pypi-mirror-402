import psutil
import time
import numpy as np
from typing import Dict, List, Optional, Tuple
import subprocess
import platform

class EnergyMonitor:
    """Monitor energy consumption for CPU and GPU."""
    
    def __init__(self):
        self.cpu_monitor = CPUMonitor()
        self.gpu_monitor = GPUMonitor()
        self.readings = []
        
    def start_monitoring(self):
        """Start energy monitoring."""
        self.readings = []
        self.start_time = time.time()
        
    def record_reading(self):
        """Record current energy reading."""
        reading = {
            'timestamp': time.time(),
            'cpu_power': self.cpu_monitor.get_current_power(),
            'gpu_power': self.gpu_monitor.get_current_power(),
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent
        }
        self.readings.append(reading)
        return reading
    
    def stop_monitoring(self) -> Dict[str, any]:
        """Stop monitoring and return statistics."""
        if not self.readings:
            return {}
        
        # Собираем статистику
        cpu_powers = [r['cpu_power'] for r in self.readings]
        gpu_powers = [r['gpu_power'] for r in self.readings]
        cpu_usages = [r['cpu_usage'] for r in self.readings]
        
        total_energy_cpu = np.trapz(cpu_powers, dx=1.0)  # Джоули (предполагая 1 сек интервал)
        total_energy_gpu = np.trapz(gpu_powers, dx=1.0)
        
        return {
            'duration': time.time() - self.start_time,
            'average_cpu_power': np.mean(cpu_powers),
            'average_gpu_power': np.mean(gpu_powers),
            'total_energy_cpu_j': total_energy_cpu,
            'total_energy_gpu_j': total_energy_gpu,
            'total_energy_j': total_energy_cpu + total_energy_gpu,
            'average_cpu_usage': np.mean(cpu_usages),
            'readings_count': len(self.readings)
        }
    
    def get_current_power(self) -> float:
        """Get total current power consumption."""
        return (self.cpu_monitor.get_current_power() + 
                self.gpu_monitor.get_current_power())


class CPUMonitor:
    """Monitor CPU energy consumption."""
    
    def __init__(self):
        self.system = platform.system()
        
    def get_current_power(self) -> float:
        """Estimate CPU power consumption in watts."""
        try:
            if self.system == "Linux":
                return self._get_linux_cpu_power()
            elif self.system == "Windows":
                return self._get_windows_cpu_power()
            else:
                return self._estimate_cpu_power()
        except:
            return self._estimate_cpu_power()
    
    def _get_linux_cpu_power(self) -> float:
        """Get CPU power on Linux."""
        try:
            # Попробуем прочитать из RAPL
            with open('/sys/class/powercap/intel-rapl:0/energy_uj', 'r') as f:
                energy1 = int(f.read().strip())
            
            time.sleep(0.1)
            
            with open('/sys/class/powercap/intel-rapl:0/energy_uj', 'r') as f:
                energy2 = int(f.read().strip())
            
            # Энергия в микроджоулях, преобразуем в ватты
            power = (energy2 - energy1) / 1000000.0 / 0.1  # Ватты
            return max(0.0, power)
        except:
            return self._estimate_cpu_power()
    
    def _get_windows_cpu_power(self) -> float:
        """Estimate CPU power on Windows."""
        # На Windows сложнее получить точные данные
        # Используем эмпирическую оценку
        return self._estimate_cpu_power()
    
    def _estimate_cpu_power(self) -> float:
        """Estimate CPU power based on usage."""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Простая модель: базовое потребление + пропорционально загрузке
        base_power = 5.0  # Ватт в idle
        max_power = 65.0  # Ватт при 100% загрузке
        
        return base_power + (max_power - base_power) * (cpu_percent / 100)


class GPUMonitor:
    """Monitor GPU energy consumption."""
    
    def __init__(self):
        self.has_nvidia_smi = self._check_nvidia_smi()
        
    def _check_nvidia_smi(self) -> bool:
        """Check if nvidia-smi is available."""
        try:
            result = subprocess.run(['nvidia-smi', '--version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def get_current_power(self) -> float:
        """Get current GPU power consumption in watts."""
        if self.has_nvidia_smi:
            try:
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=power.draw', '--format=csv,noheader,nounits'],
                    capture_output=True, text=True, timeout=2
                )
                
                if result.returncode == 0:
                    power_str = result.stdout.strip()
                    if power_str:
                        return float(power_str)
            except:
                pass
        
        # Fallback estimation
        return self._estimate_gpu_power()
    
    def _estimate_gpu_power(self) -> float:
        """Estimate GPU power when nvidia-smi is not available."""
        # Базовая оценка: 15W в idle, до 250W под нагрузкой
        # Без информации о GPU используем консервативную оценку
        return 50.0  # Среднее предположение


def get_energy_savings(baseline_power: float, 
                      optimized_power: float, 
                      duration_hours: float = 1.0) -> Dict[str, float]:
    """
    Calculate energy and cost savings.
    
    Args:
        baseline_power: Power consumption without optimization (watts)
        optimized_power: Power consumption with optimization (watts)
        duration_hours: Duration of operation in hours
        
    Returns:
        Dictionary with savings metrics
    """
    # Расчет экономии
    power_savings_w = baseline_power - optimized_power
    power_savings_percent = (power_savings_w / baseline_power * 100) if baseline_power > 0 else 0
    
    # Энергия за указанный период
    energy_savings_kwh = power_savings_w * duration_hours / 1000
    
    # Стоимость (предположим $0.15 за кВт·ч)
    cost_per_kwh = 0.15
    cost_savings = energy_savings_kwh * cost_per_kwh
    
    # CO2 savings (примерно 0.5 кг CO2 на кВт·ч)
    co2_savings_kg = energy_savings_kwh * 0.5
    
    return {
        'power_savings_w': max(0.0, power_savings_w),
        'power_savings_percent': max(0.0, power_savings_percent),
        'energy_savings_kwh': max(0.0, energy_savings_kwh),
        'cost_savings_usd': max(0.0, cost_savings),
        'co2_savings_kg': max(0.0, co2_savings_kg),
        'duration_hours': duration_hours
    }