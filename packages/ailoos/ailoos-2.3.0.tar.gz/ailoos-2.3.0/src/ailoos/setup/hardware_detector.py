
"""
HardwareDetector wrapper for auto-setup system.
Adapts the functional hardware utils to the class-based expectations of auto_setup.
"""
from typing import Dict, Any
from ..utils.hardware import get_hardware_info, get_training_capability_score

class HardwareDetector:
    def __init__(self):
        pass

    def run(self) -> Dict[str, Any]:
        """
        Run hardware detection and return configuration.
        """
        info = get_hardware_info()
        score = get_training_capability_score()
        
        # Determine Role logic (Mirroring SDK logic for consistency)
        role = "EDGE"
        if score >= 0.7:
            role = "FORGE"
        elif score >= 0.4:
            role = "SCOUT"
            
        return {
            "node_role": role,
            "training_score": score,
            "cpu_cores": info['cpu']['logical_cores'],
            "memory_gb": info['memory']['total_gb'],
            "gpu_present": info['gpu']['available'],
            "platform": info['system']['platform']
        }
