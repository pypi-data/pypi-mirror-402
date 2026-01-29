"""
Esquemas JSON Schema para respuestas de Federated Learning en AILOOS.
Define estructuras para sesiones, nodos, métricas y actualizaciones de entrenamiento.
"""

from typing import Dict, Any, List
from .base import BaseLLMResponseSchema


class FederatedSessionResponseSchema(BaseLLMResponseSchema):
    """
    Esquema para respuestas de sesiones de Federated Learning.
    """

    SESSION_SCHEMA = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://ailoos.ai/schemas/federated-session-response",
        "title": "Federated Session Response",
        "description": "Respuesta estructurada para operaciones de sesión federada",
        "type": "object",
        "allOf": [
            {"$ref": "https://ailoos.ai/schemas/base-llm-response"},
            {
                "properties": {
                    "session": {
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "ID único de la sesión"
                            },
                            "model_name": {
                                "type": "string",
                                "description": "Nombre del modelo siendo entrenado"
                            },
                            "status": {
                                "type": "string",
                                "enum": ["created", "active", "paused", "completed", "cancelled", "failed"],
                                "description": "Estado actual de la sesión"
                            },
                            "current_round": {
                                "type": "integer",
                                "minimum": 0,
                                "description": "Ronda actual de entrenamiento"
                            },
                            "total_rounds": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "Total de rondas planificadas"
                            },
                            "min_nodes": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "Mínimo de nodos requeridos"
                            },
                            "max_nodes": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "Máximo de nodos permitidos"
                            },
                            "participants": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Lista de IDs de nodos participantes"
                            },
                            "privacy_budget": {
                                "type": "number",
                                "minimum": 0.1,
                                "maximum": 10.0,
                                "description": "Presupuesto de privacidad (epsilon)"
                            },
                            "created_at": {
                                "type": "string",
                                "format": "date-time",
                                "description": "Timestamp de creación"
                            },
                            "started_at": {
                                "type": "string",
                                "format": "date-time",
                                "description": "Timestamp de inicio del entrenamiento"
                            },
                            "end_time": {
                                "type": "string",
                                "format": "date-time",
                                "description": "Timestamp de finalización"
                            },
                            "total_rewards_distributed": {
                                "type": "number",
                                "minimum": 0,
                                "description": "Total de recompensas distribuidas"
                            },
                            "uptime_seconds": {
                                "type": "number",
                                "minimum": 0,
                                "description": "Tiempo de actividad en segundos"
                            }
                        },
                        "required": ["session_id", "model_name", "status", "current_round", "total_rounds"]
                    },
                    "trainer": {
                        "type": "object",
                        "properties": {
                            "model_name": {"type": "string"},
                            "dataset_name": {"type": "string"},
                            "current_round": {"type": "integer", "minimum": 0},
                            "total_parameters": {"type": "integer", "minimum": 0},
                            "privacy_budget_used": {"type": "number", "minimum": 0},
                            "model_accuracy": {"type": "number", "minimum": 0, "maximum": 1},
                            "training_loss": {"type": "number", "minimum": 0},
                            "validation_accuracy": {"type": "number", "minimum": 0, "maximum": 1}
                        }
                    },
                    "aggregator": {
                        "type": "object",
                        "properties": {
                            "total_weight_updates": {"type": "integer", "minimum": 0},
                            "successful_aggregations": {"type": "integer", "minimum": 0},
                            "failed_aggregations": {"type": "integer", "minimum": 0},
                            "average_aggregation_time": {"type": "number", "minimum": 0},
                            "last_aggregation_cid": {"type": "string"},
                            "fedavg_efficiency": {"type": "number", "minimum": 0, "maximum": 1}
                        }
                    }
                }
            }
        ]
    }

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return cls.SESSION_SCHEMA

    @classmethod
    def create_session_response(
        cls,
        session_id: str,
        model_name: str,
        status: str,
        current_round: int,
        total_rounds: int,
        participants: List[str],
        **kwargs
    ) -> Dict[str, Any]:
        """Crear respuesta estructurada para sesión federada."""
        return cls.create_base_response(
            response_id=f"session-{session_id}",
            model_name=model_name,
            model_version="federated-v1.0",
            total_tokens=0,  # No aplica para sesiones
            response_type="federated_session",
            session={
                "session_id": session_id,
                "model_name": model_name,
                "status": status,
                "current_round": current_round,
                "total_rounds": total_rounds,
                "participants": participants,
                **kwargs
            }
        )


class FederatedNodeResponseSchema(BaseLLMResponseSchema):
    """
    Esquema para respuestas de nodos en Federated Learning.
    """

    NODE_SCHEMA = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://ailoos.ai/schemas/federated-node-response",
        "title": "Federated Node Response",
        "description": "Respuesta estructurada para operaciones de nodos federados",
        "type": "object",
        "allOf": [
            {"$ref": "https://ailoos.ai/schemas/base-llm-response"},
            {
                "properties": {
                    "node": {
                        "type": "object",
                        "properties": {
                            "node_id": {
                                "type": "string",
                                "description": "ID único del nodo"
                            },
                            "session_id": {
                                "type": "string",
                                "description": "ID de la sesión a la que pertenece"
                            },
                            "status": {
                                "type": "string",
                                "enum": ["active", "inactive", "disconnected", "failed"],
                                "description": "Estado del nodo"
                            },
                            "hardware_info": {
                                "type": "object",
                                "properties": {
                                    "cpu_cores": {"type": "integer", "minimum": 1},
                                    "memory_gb": {"type": "number", "minimum": 0},
                                    "gpu_model": {"type": "string"},
                                    "gpu_memory_gb": {"type": "number", "minimum": 0},
                                    "network_bandwidth_mbps": {"type": "number", "minimum": 0}
                                }
                            },
                            "local_data_info": {
                                "type": "object",
                                "properties": {
                                    "dataset_size": {"type": "integer", "minimum": 0},
                                    "data_quality_score": {"type": "number", "minimum": 0, "maximum": 1},
                                    "privacy_level": {"type": "string", "enum": ["high", "medium", "low"]},
                                    "data_format": {"type": "string"}
                                }
                            },
                            "contributions": {
                                "type": "integer",
                                "minimum": 0,
                                "description": "Número de contribuciones realizadas"
                            },
                            "rewards_earned": {
                                "type": "number",
                                "minimum": 0,
                                "description": "Recompensas acumuladas"
                            },
                            "last_update": {
                                "type": "string",
                                "format": "date-time",
                                "description": "Última actualización del nodo"
                            },
                            "joined_at": {
                                "type": "string",
                                "format": "date-time",
                                "description": "Cuando se unió a la sesión"
                            },
                            "reputation_score": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Puntuación de reputación del nodo"
                            }
                        },
                        "required": ["node_id", "status"]
                    }
                }
            }
        ]
    }

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return cls.NODE_SCHEMA

    @classmethod
    def create_node_response(
        cls,
        node_id: str,
        status: str,
        session_id: str = None,
        hardware_info: Dict[str, Any] = None,
        contributions: int = 0,
        **kwargs
    ) -> Dict[str, Any]:
        """Crear respuesta estructurada para nodo federado."""
        return cls.create_base_response(
            response_id=f"node-{node_id}",
            model_name="federated-node",
            model_version="node-v1.0",
            total_tokens=0,
            response_type="federated_node",
            node={
                "node_id": node_id,
                "status": status,
                "session_id": session_id,
                "hardware_info": hardware_info or {},
                "contributions": contributions,
                **kwargs
            }
        )


class FederatedMetricsResponseSchema(BaseLLMResponseSchema):
    """
    Esquema para respuestas de métricas en Federated Learning.
    """

    METRICS_SCHEMA = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://ailoos.ai/schemas/federated-metrics-response",
        "title": "Federated Metrics Response",
        "description": "Respuesta estructurada para métricas de federated learning",
        "type": "object",
        "allOf": [
            {"$ref": "https://ailoos.ai/schemas/base-llm-response"},
            {
                "properties": {
                    "metrics": {
                        "type": "object",
                        "properties": {
                            "performance": {
                                "type": "object",
                                "properties": {
                                    "cpu_usage_percent": {"type": "number", "minimum": 0, "maximum": 100},
                                    "memory_usage_percent": {"type": "number", "minimum": 0, "maximum": 100},
                                    "network_latency_ms": {"type": "number", "minimum": 0},
                                    "performance_score": {"type": "number", "minimum": 0, "maximum": 1},
                                    "response_times_history": {
                                        "type": "array",
                                        "items": {"type": "number", "minimum": 0}
                                    },
                                    "performance_history": {
                                        "type": "array",
                                        "items": {"type": "number", "minimum": 0, "maximum": 1}
                                    }
                                }
                            },
                            "contributions": {
                                "type": "object",
                                "properties": {
                                    "total_contributions": {"type": "integer", "minimum": 0},
                                    "successful_contributions": {"type": "integer", "minimum": 0},
                                    "session_success_rate": {"type": "number", "minimum": 0, "maximum": 1},
                                    "contribution_score": {"type": "number", "minimum": 0, "maximum": 1},
                                    "average_contribution_time": {"type": "number", "minimum": 0}
                                }
                            },
                            "stability": {
                                "type": "object",
                                "properties": {
                                    "stability_score": {"type": "number", "minimum": 0, "maximum": 1},
                                    "error_rate": {"type": "number", "minimum": 0, "maximum": 1},
                                    "consecutive_failures": {"type": "integer", "minimum": 0},
                                    "crash_count": {"type": "integer", "minimum": 0}
                                }
                            },
                            "connectivity": {
                                "type": "object",
                                "properties": {
                                    "connectivity_score": {"type": "number", "minimum": 0, "maximum": 1},
                                    "uptime_ratio": {"type": "number", "minimum": 0, "maximum": 1},
                                    "last_seen": {"type": "string", "format": "date-time"},
                                    "response_time_ms": {"type": "number", "minimum": 0}
                                }
                            }
                        }
                    },
                    "node_id": {
                        "type": "string",
                        "description": "ID del nodo (opcional, para métricas específicas)"
                    },
                    "aggregation_level": {
                        "type": "string",
                        "enum": ["node", "session", "system"],
                        "description": "Nivel de agregación de las métricas"
                    }
                }
            }
        ]
    }

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return cls.METRICS_SCHEMA

    @classmethod
    def create_metrics_response(
        cls,
        metrics: Dict[str, Any],
        node_id: str = None,
        aggregation_level: str = "system",
        **kwargs
    ) -> Dict[str, Any]:
        """Crear respuesta estructurada para métricas federadas."""
        return cls.create_base_response(
            response_id=f"metrics-{node_id or 'system'}",
            model_name="federated-metrics",
            model_version="metrics-v1.0",
            total_tokens=0,
            response_type="federated_metrics",
            metrics=metrics,
            node_id=node_id,
            aggregation_level=aggregation_level,
            **kwargs
        )


class FederatedTrainingUpdateSchema(BaseLLMResponseSchema):
    """
    Esquema para actualizaciones de entrenamiento en Federated Learning.
    """

    UPDATE_SCHEMA = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://ailoos.ai/schemas/federated-training-update",
        "title": "Federated Training Update",
        "description": "Actualización estructurada de pesos de entrenamiento federado",
        "type": "object",
        "allOf": [
            {"$ref": "https://ailoos.ai/schemas/base-llm-response"},
            {
                "properties": {
                    "update": {
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "ID de la sesión"
                            },
                            "node_id": {
                                "type": "string",
                                "description": "ID del nodo que envía la actualización"
                            },
                            "round_num": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "Número de ronda"
                            },
                            "weights_hash": {
                                "type": "string",
                                "description": "Hash SHA256 de los pesos"
                            },
                            "ipfs_cid": {
                                "type": "string",
                                "description": "CID IPFS donde están almacenados los pesos"
                            },
                            "num_samples": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "Número de muestras utilizadas para el entrenamiento local"
                            },
                            "metrics": {
                                "type": "object",
                                "properties": {
                                    "local_accuracy": {"type": "number", "minimum": 0, "maximum": 1},
                                    "local_loss": {"type": "number", "minimum": 0},
                                    "training_time_seconds": {"type": "number", "minimum": 0},
                                    "privacy_budget_used": {"type": "number", "minimum": 0}
                                },
                                "additionalProperties": True
                            },
                            "timestamp": {
                                "type": "string",
                                "format": "date-time",
                                "description": "Cuando se generó la actualización"
                            },
                            "compression_info": {
                                "type": "object",
                                "properties": {
                                    "algorithm": {"type": "string"},
                                    "compression_ratio": {"type": "number", "minimum": 0},
                                    "original_size_bytes": {"type": "integer", "minimum": 0},
                                    "compressed_size_bytes": {"type": "integer", "minimum": 0},
                                    "sparsification_enabled": {"type": "boolean"},
                                    "sparsity_ratio": {"type": "number", "minimum": 0, "maximum": 1},
                                    "bandwidth_reduction": {"type": "number", "minimum": 0, "maximum": 1}
                                }
                            }
                        },
                        "required": ["session_id", "node_id", "round_num", "weights_hash", "ipfs_cid", "num_samples"]
                    }
                }
            }
        ]
    }

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return cls.UPDATE_SCHEMA

    @classmethod
    def create_training_update(
        cls,
        session_id: str,
        node_id: str,
        round_num: int,
        weights_hash: str,
        ipfs_cid: str,
        num_samples: int,
        metrics: Dict[str, Any] = None,
        compression_info: Dict[str, Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Crear actualización estructurada de entrenamiento."""
        update_data = {
            "session_id": session_id,
            "node_id": node_id,
            "round_num": round_num,
            "weights_hash": weights_hash,
            "ipfs_cid": ipfs_cid,
            "num_samples": num_samples,
            "metrics": metrics or {},
            **kwargs
        }

        if compression_info:
            update_data["compression_info"] = compression_info

        return cls.create_base_response(
            response_id=f"update-{session_id}-{node_id}-{round_num}",
            model_name="federated-training",
            model_version="training-v1.0",
            total_tokens=0,
            response_type="federated_training_update",
            update=update_data
        )