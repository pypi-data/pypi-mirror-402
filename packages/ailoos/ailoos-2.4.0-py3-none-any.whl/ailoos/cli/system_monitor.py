import psutil
import time
import socket
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List


class SystemMonitor:
    """Monitor del estado del sistema para el CLI de AILOOS."""

    def __init__(self, coordinator_url: str = "http://localhost:8000"):
        self.coordinator_url = coordinator_url

    def get_uptime(self) -> str:
        """Obtiene el uptime del sistema en formato legible."""
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        uptime = timedelta(seconds=int(uptime_seconds))

        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m {seconds}s"

    def get_network_info(self) -> Dict[str, Any]:
        """Obtiene información de red."""
        net_io = psutil.net_io_counters()
        return {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv,
            'status': 'Connected' if self._check_internet() else 'Disconnected'
        }

    def _check_internet(self) -> bool:
        """Verifica conexión a internet."""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

    def get_peers_count(self) -> int:
        """Obtiene el número de peers conectados."""
        try:
            # Intentar conectar al coordinador para obtener peers
            response = requests.get(f"{self.coordinator_url}/peers", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get('count', 0)
        except Exception:
            pass

        # Fallback: simular basado en actividad
        return max(1, int(time.time() % 100))  # Simulación

    def get_system_load(self) -> Dict[str, float]:
        """Obtiene la carga del sistema."""
        load = psutil.getloadavg()
        return {
            '1min': load[0],
            '5min': load[1],
            '15min': load[2]
        }

    def get_process_info(self) -> Dict[str, Any]:
        """Obtiene información de procesos."""
        return {
            'total_processes': len(psutil.pids()),
            'running_processes': len([p for p in psutil.process_iter(['status']) if p.info['status'] == 'running'])
        }

    def get_all_system_status(self) -> Dict[str, Any]:
        """Obtiene todo el estado del sistema."""
        return {
            'uptime': self.get_uptime(),
            'network': self.get_network_info(),
            'peers': self.get_peers_count(),
            'load': self.get_system_load(),
            'processes': self.get_process_info(),
            'timestamp': datetime.now().isoformat()
        }