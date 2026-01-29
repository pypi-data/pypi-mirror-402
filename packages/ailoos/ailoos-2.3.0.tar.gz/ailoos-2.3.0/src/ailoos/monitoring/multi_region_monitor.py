import time
import random
from typing import Dict, List, Tuple, Any
from collections import defaultdict
import json

class MultiRegionMonitor:
    """
    Monitoreo multi-region y global para el sistema Ailoos.
    Proporciona vista geográfica de distribución de nodos, monitoreo de latencia inter-region,
    y análisis de balanceo de carga federada.
    """

    def __init__(self):
        # Datos geográficos simulados para regiones principales
        self.regions = {
            'us-east': {'name': 'US East', 'lat': 40.7128, 'lon': -74.0060, 'nodes': 150},
            'us-west': {'name': 'US West', 'lat': 37.7749, 'lon': -122.4194, 'nodes': 120},
            'eu-west': {'name': 'Europe West', 'lat': 50.1109, 'lon': 8.6821, 'nodes': 180},
            'eu-east': {'name': 'Europe East', 'lat': 55.7558, 'lon': 37.6173, 'nodes': 90},
            'asia-pacific': {'name': 'Asia Pacific', 'lat': 35.6762, 'lon': 139.6503, 'nodes': 200},
            'south-america': {'name': 'South America', 'lat': -23.5505, 'lon': -46.6333, 'nodes': 80},
            'africa': {'name': 'Africa', 'lat': -26.2041, 'lon': 28.0473, 'nodes': 60}
        }

        # Simular distribución de nodos con coordenadas aleatorias cerca de la región
        self._initialize_node_distribution()

        # Cache para latencias medidas
        self.latency_cache = {}
        self.last_measurement = {}

    def _initialize_node_distribution(self):
        """Inicializa la distribución geográfica de nodos con coordenadas simuladas."""
        for region_id, region_data in self.regions.items():
            region_data['node_coords'] = []
            for _ in range(region_data['nodes']):
                # Variación aleatoria alrededor del centro de la región (±5 grados)
                lat_offset = random.uniform(-5, 5)
                lon_offset = random.uniform(-5, 5)
                lat = region_data['lat'] + lat_offset
                lon = region_data['lon'] + lon_offset
                region_data['node_coords'].append((lat, lon))

    def get_geographic_distribution(self) -> Dict[str, Dict[str, Any]]:
        """
        Devuelve la distribución geográfica de nodos por región.

        Returns:
            Dict con información geográfica por región incluyendo coordenadas de nodos.
        """
        distribution = {}
        for region_id, region_data in self.regions.items():
            distribution[region_id] = {
                'name': region_data['name'],
                'center_lat': region_data['lat'],
                'center_lon': region_data['lon'],
                'total_nodes': region_data['nodes'],
                'node_coordinates': region_data['node_coords']
            }
        return distribution

    def measure_inter_region_latency(self, region_a: str, region_b: str) -> float:
        """
        Mide la latencia inter-region entre dos regiones.
        Simula medición real con variación temporal.

        Args:
            region_a: ID de la primera región
            region_b: ID de la segunda región

        Returns:
            Latencia en milisegundos
        """
        if region_a not in self.regions or region_b not in self.regions:
            raise ValueError(f"Región desconocida: {region_a} o {region_b}")

        # Crear clave única para el par de regiones
        pair_key = tuple(sorted([region_a, region_b]))

        # Simular latencia basada en distancia geográfica aproximada
        lat_a, lon_a = self.regions[region_a]['lat'], self.regions[region_a]['lon']
        lat_b, lon_b = self.regions[region_b]['lat'], self.regions[region_b]['lon']

        # Distancia aproximada (fórmula simplificada de Haversine)
        dlat = abs(lat_a - lat_b)
        dlon = abs(lon_a - lon_b)
        distance = (dlat ** 2 + dlon ** 2) ** 0.5

        # Latencia base: 10ms por unidad de distancia + jitter
        base_latency = distance * 10
        jitter = random.uniform(-5, 5)
        latency = max(1, base_latency + jitter)

        # Cache con timestamp para simular mediciones recientes
        current_time = time.time()
        if pair_key not in self.last_measurement or current_time - self.last_measurement[pair_key] > 300:  # 5 minutos
            self.latency_cache[pair_key] = latency
            self.last_measurement[pair_key] = current_time
        else:
            # Usar cache con pequeña variación
            cached = self.latency_cache[pair_key]
            latency = cached + random.uniform(-2, 2)
            latency = max(1, latency)

        return round(latency, 2)

    def get_load_balancing_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Devuelve el estado actual del balanceo de carga federada por región.

        Returns:
            Dict con métricas de carga por región.
        """
        status = {}
        total_nodes = sum(region['nodes'] for region in self.regions.values())

        for region_id, region_data in self.regions.items():
            # Simular carga actual (0-100%)
            current_load = random.uniform(10, 90)
            # Simular capacidad máxima
            max_capacity = region_data['nodes'] * 100  # 100 unidades por nodo
            current_capacity_used = current_load / 100 * max_capacity

            # Calcular balance relativo
            expected_load = (region_data['nodes'] / total_nodes) * 100
            load_balance_ratio = current_load / expected_load if expected_load > 0 else 1.0

            status[region_id] = {
                'region_name': region_data['name'],
                'current_load_percent': round(current_load, 2),
                'capacity_used': round(current_capacity_used, 2),
                'max_capacity': max_capacity,
                'load_balance_ratio': round(load_balance_ratio, 2),
                'status': 'balanced' if 0.8 <= load_balance_ratio <= 1.2 else 'unbalanced'
            }

        return status

    def generate_region_report(self) -> str:
        """
        Genera un reporte completo del estado multi-region.

        Returns:
            String con el reporte en formato JSON.
        """
        report = {
            'timestamp': time.time(),
            'geographic_distribution': self.get_geographic_distribution(),
            'load_balancing_status': self.get_load_balancing_status(),
            'inter_region_latencies': {}
        }

        # Medir latencias entre todas las parejas de regiones
        region_ids = list(self.regions.keys())
        for i, region_a in enumerate(region_ids):
            for region_b in region_ids[i+1:]:
                pair_key = tuple(sorted([region_a, region_b]))
                latency = self.measure_inter_region_latency(region_a, region_b)
                report['inter_region_latencies'][f"{region_a}-{region_b}"] = latency

        # Resumen global
        total_nodes = sum(region['nodes'] for region in self.regions.values())
        total_regions = len(self.regions)
        avg_load = sum(status['current_load_percent'] for status in report['load_balancing_status'].values()) / total_regions

        report['global_summary'] = {
            'total_regions': total_regions,
            'total_nodes': total_nodes,
            'average_load_percent': round(avg_load, 2),
            'regions_with_unbalanced_load': [
                region_id for region_id, status in report['load_balancing_status'].items()
                if status['status'] == 'unbalanced'
            ]
        }

        return json.dumps(report, indent=2, ensure_ascii=False)

# Ejemplo de uso (para testing)
if __name__ == "__main__":
    monitor = MultiRegionMonitor()

    print("Distribución geográfica:")
    dist = monitor.get_geographic_distribution()
    for region, data in dist.items():
        print(f"{region}: {data['total_nodes']} nodos")

    print("\nLatencia US East -> Europe West:", monitor.measure_inter_region_latency('us-east', 'eu-west'), "ms")

    print("\nEstado de balanceo de carga:")
    load_status = monitor.get_load_balancing_status()
    for region, status in load_status.items():
        print(f"{region}: {status['current_load_percent']}% carga, estado: {status['status']}")

    print("\nGenerando reporte completo...")
    report = monitor.generate_region_report()
    print("Reporte generado (primeras 500 caracteres):")
    print(report[:500] + "...")