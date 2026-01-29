"""
Tests de carga para el sistema de auditoría.
Prueba el rendimiento y escalabilidad del sistema bajo carga.
"""

import pytest
import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import statistics
import psutil
import os
from typing import List, Dict, Any

from src.ailoos.auditing.audit_manager import AuditManager
from src.ailoos.auditing.security_monitor import SecurityMonitor
from src.ailoos.auditing.metrics_collector import MetricsCollector
from src.ailoos.auditing.dashboard import AuditDashboard
from src.ailoos.auditing.realtime_monitor import RealtimeMonitor
from src.ailoos.core.config import Config


class TestAuditManagerLoad:
    """Tests de carga para AuditManager."""

    @pytest.fixture
    def config(self):
        """Configuración optimizada para tests de carga."""
        config = Mock(spec=Config)
        config.audit_log_file = "/tmp/test_load_audit.log"
        config.audit_retention_days = 30
        config.security_alert_thresholds = {
            "max_failed_logins_per_hour": 100,  # Alto para tests de carga
            "max_config_changes_per_hour": 500
        }
        return config

    @pytest.fixture
    async def audit_manager(self, config):
        """AuditManager para tests de carga."""
        manager = AuditManager(config)
        await manager._setup_storage()
        yield manager
        # Cleanup
        if os.path.exists(manager.audit_log_file):
            os.remove(manager.audit_log_file)

    @pytest.mark.asyncio
    async def test_high_volume_event_logging(self, audit_manager):
        """Test logging de alto volumen de eventos."""
        num_events = 1000

        # Medir tiempo de logging
        start_time = time.time()

        # Loggear eventos concurrentemente
        tasks = []
        for i in range(num_events):
            task = audit_manager.log_event(
                event_type="API_REQUEST",
                resource="api",
                action="get",
                user_id=f"user_{i % 100}",
                details={"endpoint": f"/api/resource/{i}", "response_time": 50 + (i % 100)}
            )
            tasks.append(task)

        await asyncio.gather(*tasks)

        end_time = time.time()
        total_time = end_time - start_time

        # Verificar rendimiento
        events_per_second = num_events / total_time
        print(f"Event logging performance: {events_per_second:.2f} events/second")

        # Verificar que todos los eventos fueron registrados
        events = audit_manager.get_audit_events()
        assert len(events) == num_events

        # Verificar rendimiento mínimo aceptable (ajustar según hardware)
        assert events_per_second > 50  # Al menos 50 eventos por segundo

    def test_memory_usage_under_load(self, audit_manager):
        """Test uso de memoria bajo carga."""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        # Generar carga de memoria
        num_events = 5000
        for i in range(num_events):
            event = {
                "event_type": "API_REQUEST",
                "resource": "api",
                "action": "get",
                "user_id": f"user_{i % 200}",
                "timestamp": datetime.now(),
                "details": {
                    "endpoint": f"/api/resource/{i}",
                    "response_time": 50 + (i % 100),
                    "user_agent": "Mozilla/5.0 (compatible; test/1.0)",
                    "ip": f"192.168.1.{i % 255}"
                }
            }
            audit_manager.audit_events.append(event)

        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        print(f"Memory usage: {memory_increase:.2f} MB increase for {num_events} events")

        # Verificar que el aumento de memoria es razonable
        # Aproximadamente 1KB por evento (ajustar según implementación)
        expected_memory_kb = num_events * 1
        expected_memory_mb = expected_memory_kb / 1024

        assert memory_increase < expected_memory_mb * 2  # Máximo 2x lo esperado

    @pytest.mark.asyncio
    async def test_concurrent_security_alert_generation(self, audit_manager):
        """Test generación concurrente de alertas de seguridad."""
        num_threads = 10
        events_per_thread = 50

        async def generate_security_events(thread_id: int):
            """Generar eventos de seguridad en un thread."""
            for i in range(events_per_thread):
                await audit_manager.log_event(
                    event_type="USER_LOGIN",
                    resource="auth",
                    action="login_failed",
                    user_id=f"user_{thread_id}_{i}",
                    details={
                        "ip": f"192.168.{thread_id}.{i % 255}",
                        "reason": "invalid_password"
                    }
                )

        # Ejecutar threads concurrentemente
        start_time = time.time()

        tasks = []
        for thread_id in range(num_threads):
            task = generate_security_events(thread_id)
            tasks.append(task)

        await asyncio.gather(*tasks)

        end_time = time.time()
        total_time = end_time - start_time

        # Verificar que se generaron alertas
        alerts = audit_manager.get_security_alerts()
        print(f"Generated {len(alerts)} security alerts in {total_time:.2f} seconds")

        # Verificar rendimiento
        total_events = num_threads * events_per_thread
        events_per_second = total_events / total_time
        assert events_per_second > 100  # Al menos 100 eventos por segundo

    def test_large_audit_log_processing(self, audit_manager):
        """Test procesamiento de logs de auditoría grandes."""
        # Crear log grande
        num_events = 10000

        for i in range(num_events):
            event = {
                "event_type": "API_REQUEST",
                "resource": "api",
                "action": "get",
                "user_id": f"user_{i % 1000}",
                "timestamp": datetime.now() - timedelta(hours=i % 24),
                "details": {"endpoint": f"/api/resource/{i}"}
            }
            audit_manager.audit_events.append(event)

        # Medir tiempo de obtención de estadísticas
        start_time = time.time()
        stats = audit_manager.get_audit_statistics()
        end_time = time.time()

        processing_time = end_time - start_time

        print(f"Audit statistics processing time: {processing_time:.2f} seconds for {num_events} events")

        # Verificar que las estadísticas son correctas
        assert stats["total_events"] == num_events
        assert len(stats["events_by_type"]) > 0

        # Verificar rendimiento (menos de 1 segundo para 10k eventos)
        assert processing_time < 1.0


class TestSecurityMonitorLoad:
    """Tests de carga para SecurityMonitor."""

    @pytest.fixture
    def config(self):
        """Configuración para tests de carga de seguridad."""
        config = Mock(spec=Config)
        config.security_rules_file = "/tmp/test_security_load.json"
        config.threat_intelligence_file = "/tmp/test_threats_load.json"
        return config

    @pytest.fixture
    async def security_monitor(self, config):
        """SecurityMonitor para tests de carga."""
        monitor = SecurityMonitor(config)
        await monitor._load_default_rules()
        yield monitor

    @pytest.mark.asyncio
    async def test_high_frequency_event_processing(self, security_monitor):
        """Test procesamiento de eventos de alta frecuencia."""
        num_events = 5000

        # Crear eventos de prueba
        events = []
        for i in range(num_events):
            event = {
                "event_type": "USER_LOGIN",
                "resource": "auth",
                "action": "login_attempt",
                "user_id": f"user_{i % 500}",
                "details": {
                    "ip": f"192.168.{(i // 255) % 256}.{i % 255}",
                    "success": i % 10 != 0,  # 10% de fallos
                    "timestamp": datetime.now().isoformat()
                }
            }
            events.append(event)

        # Procesar eventos
        start_time = time.time()

        tasks = []
        for event in events:
            task = security_monitor.process_event(event)
            tasks.append(task)

        await asyncio.gather(*tasks)

        end_time = time.time()
        processing_time = end_time - start_time

        events_per_second = num_events / processing_time
        print(f"Security event processing: {events_per_second:.2f} events/second")

        # Verificar rendimiento mínimo
        assert events_per_second > 200  # Al menos 200 eventos por segundo

    def test_rule_engine_scalability(self, security_monitor):
        """Test escalabilidad del motor de reglas."""
        # Agregar muchas reglas
        num_rules = 100

        for i in range(num_rules):
            rule = {
                "rule_id": f"rule_{i}",
                "name": f"Test Rule {i}",
                "description": f"Rule for testing scalability {i}",
                "severity": "LOW",
                "conditions": [
                    {
                        "field": "event_type",
                        "operator": "equals",
                        "value": f"EVENT_TYPE_{i}"
                    }
                ],
                "action": "alert"
            }
            security_monitor.add_security_rule(rule)

        # Verificar que todas las reglas se agregaron
        assert len(security_monitor.security_rules) == num_rules

        # Probar procesamiento con muchas reglas
        event = {
            "event_type": "EVENT_TYPE_50",  # Coincide con regla_50
            "resource": "test",
            "action": "test",
            "user_id": "test_user"
        }

        start_time = time.time()

        # Procesar evento 100 veces
        for _ in range(100):
            asyncio.run(security_monitor.process_event(event))

        end_time = time.time()
        processing_time = end_time - start_time

        print(f"Rule engine processing time: {processing_time:.2f} seconds for 100 events with {num_rules} rules")

        # Verificar que el tiempo es razonable
        assert processing_time < 5.0  # Menos de 5 segundos


class TestMetricsCollectorLoad:
    """Tests de carga para MetricsCollector."""

    @pytest.fixture
    def config(self):
        """Configuración para tests de carga de métricas."""
        config = Mock(spec=Config)
        config.metrics_collection_interval = 1  # Rápido para tests
        config.metrics_retention_hours = 24
        return config

    @pytest.fixture
    async def metrics_collector(self, config):
        """MetricsCollector para tests de carga."""
        collector = MetricsCollector(config)
        yield collector

    def test_high_frequency_metrics_recording(self, metrics_collector):
        """Test registro de métricas de alta frecuencia."""
        num_metrics = 10000

        # Registrar métricas de respuesta
        response_times = []
        start_time = time.time()

        for i in range(num_metrics):
            response_time = 50 + (i % 200)  # 50-250ms
            metrics_collector.record_response_time(response_time)
            response_times.append(response_time)

        end_time = time.time()
        recording_time = end_time - start_time

        metrics_per_second = num_metrics / recording_time
        print(f"Metrics recording performance: {metrics_per_second:.2f} metrics/second")

        # Verificar rendimiento
        assert metrics_per_second > 1000  # Al menos 1000 métricas por segundo

        # Verificar que se calcularon estadísticas correctamente
        latest_metrics = metrics_collector.get_latest_metrics()
        assert "performance" in latest_metrics

    def test_concurrent_metrics_access(self, metrics_collector):
        """Test acceso concurrente a métricas."""
        num_threads = 20
        operations_per_thread = 100

        def metrics_worker(thread_id: int):
            """Trabajador que accede a métricas."""
            for i in range(operations_per_thread):
                # Registrar métrica
                metrics_collector.record_response_time(100 + thread_id)

                # Registrar error
                if i % 10 == 0:
                    metrics_collector.record_error(f"/api/endpoint_{thread_id}", "timeout")

                # Obtener métricas
                metrics_collector.get_latest_metrics()

        # Ejecutar threads concurrentemente
        start_time = time.time()

        threads = []
        for thread_id in range(num_threads):
            thread = threading.Thread(target=metrics_worker, args=(thread_id,))
            threads.append(thread)
            thread.start()

        # Esperar que terminen todos los threads
        for thread in threads:
            thread.join()

        end_time = time.time()
        total_time = end_time - start_time

        total_operations = num_threads * operations_per_thread * 3  # 3 operaciones por iteración
        operations_per_second = total_operations / total_time

        print(f"Concurrent metrics operations: {operations_per_second:.2f} operations/second")

        # Verificar rendimiento
        assert operations_per_second > 500  # Al menos 500 operaciones por segundo


class TestDashboardLoad:
    """Tests de carga para AuditDashboard."""

    @pytest.fixture
    def config(self):
        """Configuración para tests de carga de dashboard."""
        config = Mock(spec=Config)
        config.audit_log_file = "/tmp/test_dashboard_load.log"
        return config

    @pytest.fixture
    async def dashboard_system(self, config):
        """Sistema de dashboard para tests de carga."""
        audit_manager = AuditManager(config)
        metrics_collector = MetricsCollector(config)
        dashboard = AuditDashboard(config, audit_manager, metrics_collector)

        # Agregar algunos datos de prueba
        for i in range(1000):
            await audit_manager.log_event(
                event_type="API_REQUEST",
                resource="api",
                action="get",
                user_id=f"user_{i % 50}",
                details={"endpoint": f"/api/resource/{i}"}
            )

        system = {
            'audit_manager': audit_manager,
            'metrics_collector': metrics_collector,
            'dashboard': dashboard
        }

        yield system

        if os.path.exists(audit_manager.audit_log_file):
            os.remove(audit_manager.audit_log_file)

    @pytest.mark.asyncio
    async def test_concurrent_dashboard_access(self, dashboard_system):
        """Test acceso concurrente al dashboard."""
        dashboard = dashboard_system['dashboard']

        num_requests = 100

        async def dashboard_request(request_id: int):
            """Simular request al dashboard."""
            return await dashboard.get_dashboard_data()

        # Ejecutar requests concurrentemente
        start_time = time.time()

        tasks = []
        for i in range(num_requests):
            task = dashboard_request(i)
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        end_time = time.time()
        total_time = end_time - start_time

        requests_per_second = num_requests / total_time
        print(f"Dashboard concurrent access: {requests_per_second:.2f} requests/second")

        # Verificar que todas las requests tuvieron éxito
        assert len(results) == num_requests
        for result in results:
            assert 'events' in result
            assert 'summary' in result

        # Verificar rendimiento
        assert requests_per_second > 20  # Al menos 20 requests por segundo

    @pytest.mark.asyncio
    async def test_dashboard_data_processing_scalability(self, dashboard_system):
        """Test escalabilidad del procesamiento de datos del dashboard."""
        audit_manager = dashboard_system['audit_manager']
        dashboard = dashboard_system['dashboard']

        # Agregar más eventos
        num_additional_events = 5000

        for i in range(num_additional_events):
            await audit_manager.log_event(
                event_type="API_REQUEST",
                resource="api",
                action="get",
                user_id=f"user_{i % 200}",
                details={"endpoint": f"/api/resource/{i}"}
            )

        # Medir tiempo de procesamiento del dashboard
        start_time = time.time()
        data = await dashboard.get_dashboard_data()
        end_time = time.time()

        processing_time = end_time - start_time

        print(f"Dashboard data processing time: {processing_time:.2f} seconds for {len(data['events'])} events")

        # Verificar que el procesamiento es razonable
        assert processing_time < 2.0  # Menos de 2 segundos
        assert len(data['events']) > 0


class TestRealtimeMonitorLoad:
    """Tests de carga para RealtimeMonitor."""

    @pytest.fixture
    def config(self):
        """Configuración para tests de carga de tiempo real."""
        config = Mock(spec=Config)
        config.websocket_timeout = 30
        config.max_websocket_connections = 1000  # Alto para tests
        return config

    @pytest.fixture
    async def realtime_monitor(self, config):
        """RealtimeMonitor para tests de carga."""
        monitor = RealtimeMonitor(config)
        yield monitor
        await monitor.stop_monitoring()

    @pytest.mark.asyncio
    async def test_massive_websocket_connections(self, realtime_monitor):
        """Test conexiones WebSocket masivas."""
        await realtime_monitor.start_monitoring()

        num_connections = 100

        # Crear conexiones mock
        websockets = []
        for i in range(num_connections):
            ws_mock = Mock()
            ws_mock.send_json = AsyncMock()
            websockets.append(ws_mock)

            # Agregar conexión
            await realtime_monitor.add_connection("dashboard", ws_mock)

        # Verificar conteos
        counts = realtime_monitor.get_connection_counts()
        assert counts["total"] == num_connections

        # Broadcast mensaje
        start_time = time.time()
        await realtime_monitor.broadcast_custom_event(
            "test_event",
            {"message": "massive_broadcast_test"}
        )
        end_time = time.time()

        broadcast_time = end_time - start_time
        print(f"Broadcast time for {num_connections} connections: {broadcast_time:.2f} seconds")

        # Verificar que todos los websockets recibieron el mensaje
        for ws in websockets:
            ws.send_json.assert_called_once()

        # Verificar rendimiento de broadcast
        assert broadcast_time < 1.0  # Menos de 1 segundo para 100 conexiones

        await realtime_monitor.stop_monitoring()

    @pytest.mark.asyncio
    async def test_high_frequency_broadcasts(self, realtime_monitor):
        """Test broadcasts de alta frecuencia."""
        await realtime_monitor.start_monitoring()

        # Agregar algunas conexiones
        num_connections = 10
        websockets = []

        for i in range(num_connections):
            ws_mock = Mock()
            ws_mock.send_json = AsyncMock()
            websockets.append(ws_mock)
            await realtime_monitor.add_connection("alerts", ws_mock)

        # Enviar broadcasts de alta frecuencia
        num_broadcasts = 100

        start_time = time.time()

        for i in range(num_broadcasts):
            await realtime_monitor.broadcast_custom_event(
                "performance_metric",
                {
                    "metric": "response_time",
                    "value": 100 + i,
                    "timestamp": datetime.now().isoformat()
                }
            )

        end_time = time.time()
        total_time = end_time - start_time

        broadcasts_per_second = num_broadcasts / total_time
        print(f"High frequency broadcasts: {broadcasts_per_second:.2f} broadcasts/second")

        # Verificar que todos los broadcasts se enviaron
        for ws in websockets:
            assert ws.send_json.call_count == num_broadcasts

        # Verificar rendimiento
        assert broadcasts_per_second > 50  # Al menos 50 broadcasts por segundo

        await realtime_monitor.stop_monitoring()


class TestSystemWideLoad:
    """Tests de carga para todo el sistema de auditoría."""

    @pytest.fixture
    def config(self):
        """Configuración completa para tests de carga del sistema."""
        config = Mock(spec=Config)
        config.audit_log_file = "/tmp/test_system_load.log"
        config.audit_retention_days = 30
        config.security_alert_thresholds = {
            "max_failed_logins_per_hour": 500,
            "max_config_changes_per_hour": 1000
        }
        config.websocket_timeout = 30
        config.max_websocket_connections = 500
        config.metrics_collection_interval = 60
        config.metrics_retention_hours = 24
        return config

    @pytest.fixture
    async def complete_system(self, config):
        """Sistema completo de auditoría para tests de carga."""
        # Crear todos los componentes
        audit_manager = AuditManager(config)
        security_monitor = SecurityMonitor(config)
        metrics_collector = MetricsCollector(config)
        dashboard = AuditDashboard(config, audit_manager, metrics_collector)
        realtime_monitor = RealtimeMonitor(config)

        # Inicializar
        await audit_manager._setup_storage()
        await security_monitor._load_default_rules()
        await realtime_monitor.start_monitoring()

        system = {
            'audit_manager': audit_manager,
            'security_monitor': security_monitor,
            'metrics_collector': metrics_collector,
            'dashboard': dashboard,
            'realtime_monitor': realtime_monitor
        }

        yield system

        # Cleanup
        await realtime_monitor.stop_monitoring()
        if os.path.exists(audit_manager.audit_log_file):
            os.remove(audit_manager.audit_log_file)

    @pytest.mark.asyncio
    async def test_end_to_end_system_load(self, complete_system):
        """Test carga end-to-end del sistema completo."""
        audit_manager = complete_system['audit_manager']
        security_monitor = complete_system['security_monitor']
        metrics_collector = complete_system['metrics_collector']
        dashboard = complete_system['dashboard']
        realtime_monitor = complete_system['realtime_monitor']

        # Configurar conexiones WebSocket
        num_websockets = 20
        websockets = []

        for i in range(num_websockets):
            ws_mock = Mock()
            ws_mock.send_json = AsyncMock()
            websockets.append(ws_mock)
            await realtime_monitor.add_connection("dashboard", ws_mock)

        # Simular carga del sistema
        num_events = 2000

        start_time = time.time()

        # Generar eventos de diferentes tipos
        for i in range(num_events):
            # Evento de auditoría
            await audit_manager.log_event(
                event_type="API_REQUEST",
                resource="api",
                action="get",
                user_id=f"user_{i % 100}",
                details={
                    "endpoint": f"/api/resource/{i}",
                    "response_time": 50 + (i % 100),
                    "ip": f"192.168.{(i // 255) % 256}.{i % 255}"
                }
            )

            # Evento de seguridad (cada 10 eventos)
            if i % 10 == 0:
                event_data = {
                    "event_type": "USER_LOGIN",
                    "resource": "auth",
                    "action": "login_attempt",
                    "user_id": f"user_{i % 50}",
                    "details": {
                        "ip": f"10.0.{(i // 255) % 256}.{i % 255}",
                        "success": i % 20 != 0  # 5% de fallos
                    }
                }
                await security_monitor.process_event(event_data)

            # Métrica de rendimiento
            metrics_collector.record_response_time(50 + (i % 150))

        # Obtener datos del dashboard
        dashboard_data = await dashboard.get_dashboard_data()

        # Broadcast actualización
        await realtime_monitor.broadcast_custom_event(
            "load_test_complete",
            {"total_events": num_events, "timestamp": datetime.now().isoformat()}
        )

        end_time = time.time()
        total_time = end_time - start_time

        # Calcular métricas de rendimiento
        events_per_second = num_events / total_time
        print(f"End-to-end system load test: {events_per_second:.2f} events/second")
        print(f"Total processing time: {total_time:.2f} seconds")
        print(f"Dashboard events processed: {len(dashboard_data['events'])}")

        # Verificar que todos los WebSockets recibieron el broadcast
        for ws in websockets:
            ws.send_json.assert_called()

        # Verificar rendimiento mínimo
        assert events_per_second > 100  # Al menos 100 eventos por segundo
        assert total_time < 30  # Menos de 30 segundos para 2000 eventos
        assert len(dashboard_data['events']) > 0

        # Cleanup
        await realtime_monitor.stop_monitoring()

    def test_memory_leak_detection(self, complete_system):
        """Test detección de fugas de memoria."""
        # Este test monitorea el uso de memoria durante operaciones repetidas
        # para detectar posibles fugas

        audit_manager = complete_system['audit_manager']

        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        # Realizar operaciones repetidas
        num_iterations = 100
        events_per_iteration = 50

        for iteration in range(num_iterations):
            for i in range(events_per_iteration):
                event = {
                    "event_type": "API_REQUEST",
                    "resource": "api",
                    "action": "get",
                    "user_id": f"user_{i % 20}",
                    "timestamp": datetime.now(),
                    "details": {"endpoint": f"/api/test/{i}"}
                }
                audit_manager.audit_events.append(event)

            # Limpiar eventos antiguos para simular rotación de logs
            if len(audit_manager.audit_events) > 1000:
                audit_manager.audit_events = audit_manager.audit_events[-500:]

        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        print(f"Memory leak test: {memory_increase:.2f} MB increase after {num_iterations * events_per_iteration} operations")

        # Verificar que no hay fuga significativa de memoria
        # Permitir cierto aumento por crecimiento normal de estructuras de datos
        max_allowed_increase = 50  # MB
        assert memory_increase < max_allowed_increase