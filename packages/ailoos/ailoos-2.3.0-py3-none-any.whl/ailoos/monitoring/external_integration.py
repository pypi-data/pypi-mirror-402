import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException
from aiohttp import ClientSession, web
import uuid

# Simulación de Kafka/Redis streams usando diccionarios en memoria
class SimulatedKafkaStream:
    def __init__(self):
        self.streams: Dict[str, List[Dict[str, Any]]] = {}

    async def publish(self, topic: str, message: Dict[str, Any]):
        if topic not in self.streams:
            self.streams[topic] = []
        self.streams[topic].append(message)
        logging.info(f"Publicado en Kafka topic {topic}: {message}")

    async def consume(self, topic: str) -> List[Dict[str, Any]]:
        return self.streams.get(topic, [])

class SimulatedRedisStream:
    def __init__(self):
        self.streams: Dict[str, List[Dict[str, Any]]] = {}

    async def add(self, stream: str, data: Dict[str, Any]):
        if stream not in self.streams:
            self.streams[stream] = []
        self.streams[stream].append(data)
        logging.info(f"Agregado a Redis stream {stream}: {data}")

    async def read(self, stream: str) -> List[Dict[str, Any]]:
        return self.streams.get(stream, [])

class ExternalIntegrationAPI:
    def __init__(self):
        self.app = FastAPI(title="External Integration API")
        self.webhooks: Dict[str, str] = {}  # ID -> URL
        self.integrations: Dict[str, Dict[str, Any]] = {}  # ID -> config
        self.kafka = SimulatedKafkaStream()
        self.redis = SimulatedRedisStream()
        self.metrics: Dict[str, Any] = {
            "cpu_usage": 45.2,
            "memory_usage": 67.8,
            "active_nodes": 12,
            "total_requests": 15432
        }
        self._setup_routes()

    def _setup_routes(self):
        @self.app.post("/webhook/{webhook_id}")
        async def receive_webhook(webhook_id: str, data: Dict[str, Any]):
            if webhook_id not in self.webhooks:
                raise HTTPException(status_code=404, detail="Webhook not found")
            # Procesar webhook recibido (simulado)
            logging.info(f"Webhook recibido {webhook_id}: {data}")
            return {"status": "received"}

        @self.app.get("/metrics/public")
        async def get_public_metrics():
            return self.get_public_metrics()

        @self.app.post("/stream/{topic}")
        async def stream_data_endpoint(topic: str, data: Dict[str, Any]):
            await self.stream_data(topic, data)
            return {"status": "streamed"}

    async def register_webhook(self, url: str, tool: str) -> str:
        """Registra un webhook para una herramienta externa."""
        webhook_id = str(uuid.uuid4())
        self.webhooks[webhook_id] = url
        self.integrations[webhook_id] = {"tool": tool, "url": url, "type": "webhook"}
        logging.info(f"Webhook registrado: {webhook_id} para {tool} en {url}")
        return webhook_id

    def get_public_metrics(self) -> Dict[str, Any]:
        """Devuelve métricas públicas controladas."""
        return {
            "metrics": self.metrics,
            "timestamp": asyncio.get_event_loop().time()
        }

    async def stream_data(self, topic: str, data: Dict[str, Any]):
        """Envía datos a streams simulados de Kafka/Redis."""
        await self.kafka.publish(topic, data)
        await self.redis.add(topic, data)
        # Simular envío a herramientas externas vía webhook
        for webhook_id, url in self.webhooks.items():
            if self.integrations[webhook_id]["tool"] in ["grafana", "prometheus"]:
                async with ClientSession() as session:
                    try:
                        await session.post(url, json=data)
                        logging.info(f"Datos enviados a webhook {webhook_id}")
                    except Exception as e:
                        logging.error(f"Error enviando a webhook {webhook_id}: {e}")

    def manage_integrations(self) -> Dict[str, Dict[str, Any]]:
        """Gestiona y lista todas las integraciones."""
        return self.integrations

# Instancia global para uso
external_api = ExternalIntegrationAPI()

# Para ejecutar como servidor FastAPI
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(external_api.app, host="0.0.0.0", port=8001)