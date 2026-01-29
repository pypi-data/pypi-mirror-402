import psutil
import platform
import GPUtil
from typing import Dict, Any


class HardwareMonitor:
    """Monitor de hardware real para el CLI de AILOOS."""

    def __init__(self):
        self.system = platform.system()

    def get_cpu_info(self) -> Dict[str, Any]:
        """Obtiene información del CPU."""
        try:
            cpu_name = platform.processor()
            if not cpu_name:
                # Try to get more detailed CPU info
                try:
                    import cpuinfo
                    cpu_name = cpuinfo.get_cpu_info()['brand_raw']
                except ImportError:
                    cpu_name = "Unknown CPU"
        except:
            cpu_name = "Unknown CPU"

        freq = psutil.cpu_freq()
        return {
            'name': cpu_name,
            'cores': psutil.cpu_count(logical=True),
            'physical_cores': psutil.cpu_count(logical=False),
            'usage_percent': psutil.cpu_percent(interval=1),
            'frequency_mhz': freq.current if freq else None,
            'max_frequency_mhz': freq.max if freq else None
        }

    def get_memory_info(self) -> Dict[str, Any]:
        """Obtiene información de memoria RAM."""
        mem = psutil.virtual_memory()
        return {
            'total_gb': round(mem.total / (1024**3), 1),
            'available_gb': round(mem.available / (1024**3), 1),
            'used_gb': round(mem.used / (1024**3), 1),
            'usage_percent': mem.percent
        }

    def get_disk_info(self) -> Dict[str, Any]:
        """Obtiene información del disco."""
        disk = psutil.disk_usage('/')
        return {
            'total_gb': round(disk.total / (1024**3), 1),
            'used_gb': round(disk.used / (1024**3), 1),
            'free_gb': round(disk.free / (1024**3), 1),
            'usage_percent': disk.percent
        }

    def get_gpu_info(self) -> Dict[str, Any]:
        """Obtiene información de GPU."""
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]  # Primera GPU
                return {
                    'name': gpu.name,
                    'memory_total_mb': gpu.memoryTotal,
                    'memory_used_mb': gpu.memoryUsed,
                    'memory_free_mb': gpu.memoryFree,
                    'usage_percent': gpu.load * 100
                }
            else:
                return {'name': 'No GPU detected', 'memory_total_mb': 0, 'memory_used_mb': 0, 'memory_free_mb': 0, 'usage_percent': 0}
        except Exception as e:
            return {'name': f'Error detecting GPU: {str(e)}', 'memory_total_mb': 0, 'memory_used_mb': 0, 'memory_free_mb': 0, 'usage_percent': 0}

    def get_system_info(self) -> Dict[str, Any]:
        """Obtiene información general del sistema."""
        import time

        # Get detailed OS info
        system = platform.system()
        if system == "Darwin":
            os_name = "macOS"
            try:
                import subprocess
                result = subprocess.run(['sw_vers', '-productVersion'], capture_output=True, text=True)
                os_version = result.stdout.strip()
                result = subprocess.run(['sw_vers', '-buildVersion'], capture_output=True, text=True)
                build_version = result.stdout.strip()
                os_version = f"{os_version} (Build {build_version})"
            except:
                os_version = platform.mac_ver()[0]
        elif system == "Windows":
            os_name = "Windows"
            os_version = platform.version()
        elif system == "Linux":
            os_name = "Linux"
            try:
                with open('/etc/os-release', 'r') as f:
                    for line in f:
                        if line.startswith('PRETTY_NAME='):
                            os_version = line.split('=')[1].strip().strip('"')
                            break
                    else:
                        os_version = platform.version()
            except:
                os_version = platform.version()
        else:
            os_name = system
            os_version = platform.version()

        # Calculate uptime
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        uptime_hours = int(uptime_seconds // 3600)
        uptime_minutes = int((uptime_seconds % 3600) // 60)
        uptime_str = f"{uptime_hours}h {uptime_minutes}m"

        return {
            'os': os_name,
            'os_version': os_version,
            'hostname': platform.node(),
            'architecture': platform.machine(),
            'uptime_seconds': boot_time,
            'uptime_formatted': uptime_str
        }

    def get_all_hardware_info(self) -> Dict[str, Any]:
        """Obtiene toda la información de hardware."""
        return {
            'cpu': self.get_cpu_info(),
            'memory': self.get_memory_info(),
            'disk': self.get_disk_info(),
            'gpu': self.get_gpu_info(),
            'system': self.get_system_info()
        }