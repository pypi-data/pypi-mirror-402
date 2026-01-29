import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass
from enum import Enum
import random
import numpy as np

logger = logging.getLogger(__name__)

class ModelType(Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    NLP = "nlp"
    COMPUTER_VISION = "computer_vision"
    RECOMMENDATION = "recommendation"

@dataclass
class EdgeLocation:
    id: str
    region: str
    latitude: float
    longitude: float
    capacity: int  # Max concurrent inferences
    current_load: int = 0

@dataclass
class ModelConfig:
    model_id: str
    model_type: ModelType
    version: str
    input_shape: List[int]
    output_shape: List[int]
    framework: str  # tensorflow, pytorch, onnx, etc.
    memory_mb: int
    latency_ms_target: int

@dataclass
class InferenceRequest:
    request_id: str
    model_id: str
    input_data: Union[List[float], Dict[str, Any]]
    priority: int = 1
    timeout_ms: int = 5000

@dataclass
class InferenceResult:
    request_id: str
    output_data: Any
    latency_ms: float
    edge_location: str
    confidence: Optional[float] = None
    error: Optional[str] = None

class EdgeComputing:
    """Edge computing system for model inference at CDN edge locations"""

    def __init__(self):
        self.edge_locations: Dict[str, EdgeLocation] = {}
        self.deployed_models: Dict[str, Dict[str, ModelConfig]] = {}  # location -> model_id -> config
        self.model_registry: Dict[str, ModelConfig] = {}
        self.inference_queue: asyncio.Queue = asyncio.Queue()
        self.results_cache: Dict[str, InferenceResult] = {}
        self._running = False
        self._workers: List[asyncio.Task] = []

    async def start(self) -> None:
        """Start the edge computing system"""
        self._running = True

        # Start inference workers
        for i in range(10):  # 10 concurrent workers
            worker = asyncio.create_task(self._inference_worker())
            self._workers.append(worker)

        logger.info("Edge computing system started")

    async def stop(self) -> None:
        """Stop the edge computing system"""
        self._running = False

        # Cancel workers
        for worker in self._workers:
            worker.cancel()

        await asyncio.gather(*self._workers, return_exceptions=True)
        logger.info("Edge computing system stopped")

    async def add_edge_location(self, location: EdgeLocation) -> bool:
        """Add an edge location"""
        if location.id in self.edge_locations:
            return False

        self.edge_locations[location.id] = location
        self.deployed_models[location.id] = {}
        logger.info(f"Added edge location: {location.id} in {location.region}")
        return True

    async def deploy_model(self, model_config: ModelConfig, locations: List[str]) -> bool:
        """Deploy model to specified edge locations"""
        if model_config.model_id in self.model_registry:
            logger.warning(f"Model {model_config.model_id} already registered")
            return False

        self.model_registry[model_config.model_id] = model_config

        success_count = 0
        for location_id in locations:
            if location_id in self.edge_locations:
                # Simulate deployment time
                await asyncio.sleep(0.1)
                self.deployed_models[location_id][model_config.model_id] = model_config
                success_count += 1
                logger.info(f"Deployed model {model_config.model_id} to {location_id}")

        return success_count > 0

    async def run_inference(self, request: InferenceRequest,
                          preferred_location: Optional[str] = None) -> Optional[InferenceResult]:
        """Run inference on the edge"""
        if not self._running:
            return None

        # Find optimal edge location
        location_id = self._select_edge_location(request.model_id, preferred_location)

        if not location_id:
            result = InferenceResult(
                request_id=request.request_id,
                output_data=None,
                latency_ms=0,
                edge_location="",
                error="No suitable edge location found"
            )
            return result

        # Check if location has capacity
        location = self.edge_locations[location_id]
        if location.current_load >= location.capacity:
            result = InferenceResult(
                request_id=request.request_id,
                output_data=None,
                latency_ms=0,
                edge_location=location_id,
                error="Edge location at capacity"
            )
            return result

        # Increment load
        location.current_load += 1

        try:
            # Queue the inference
            future = asyncio.Future()
            await self.inference_queue.put((request, location_id, future))

            # Wait for result with timeout
            try:
                result = await asyncio.wait_for(future, timeout=request.timeout_ms / 1000)
                return result
            except asyncio.TimeoutError:
                return InferenceResult(
                    request_id=request.request_id,
                    output_data=None,
                    latency_ms=request.timeout_ms,
                    edge_location=location_id,
                    error="Inference timeout"
                )

        finally:
            # Decrement load
            location.current_load -= 1

    async def get_inference_result(self, request_id: str) -> Optional[InferenceResult]:
        """Get cached inference result"""
        return self.results_cache.get(request_id)

    async def get_edge_metrics(self) -> Dict[str, Any]:
        """Get edge computing metrics"""
        total_locations = len(self.edge_locations)
        total_deployed_models = sum(len(models) for models in self.deployed_models.values())
        total_load = sum(loc.current_load for loc in self.edge_locations.values())
        total_capacity = sum(loc.capacity for loc in self.edge_locations.values())

        location_metrics = {}
        for loc_id, location in self.edge_locations.items():
            location_metrics[loc_id] = {
                'region': location.region,
                'current_load': location.current_load,
                'capacity': location.capacity,
                'utilization': location.current_load / location.capacity if location.capacity > 0 else 0,
                'deployed_models': list(self.deployed_models[loc_id].keys())
            }

        return {
            'total_edge_locations': total_locations,
            'total_deployed_models': total_deployed_models,
            'total_load': total_load,
            'total_capacity': total_capacity,
            'overall_utilization': total_load / total_capacity if total_capacity > 0 else 0,
            'location_metrics': location_metrics
        }

    def _select_edge_location(self, model_id: str, preferred_location: Optional[str] = None) -> Optional[str]:
        """Select optimal edge location for inference"""
        if preferred_location and preferred_location in self.edge_locations:
            if model_id in self.deployed_models.get(preferred_location, {}):
                return preferred_location

        # Find locations with the model deployed and available capacity
        available_locations = []
        for loc_id, models in self.deployed_models.items():
            if model_id in models:
                location = self.edge_locations[loc_id]
                if location.current_load < location.capacity:
                    available_locations.append((loc_id, location.current_load))

        if not available_locations:
            return None

        # Select location with lowest load
        available_locations.sort(key=lambda x: x[1])
        return available_locations[0][0]

    async def _inference_worker(self) -> None:
        """Background worker for processing inference requests"""
        while self._running:
            try:
                request, location_id, future = await self.inference_queue.get()

                start_time = time.time()
                result = await self._execute_inference(request, location_id)
                latency_ms = (time.time() - start_time) * 1000

                result.latency_ms = latency_ms
                result.edge_location = location_id

                # Cache result
                self.results_cache[request.request_id] = result

                # Set future result
                if not future.done():
                    future.set_result(result)

                self.inference_queue.task_done()

            except Exception as e:
                logger.error(f"Inference worker error: {e}")
                await asyncio.sleep(0.1)

    async def _execute_inference(self, request: InferenceRequest, location_id: str) -> InferenceResult:
        """Execute the actual inference (simulated)"""
        model_config = self.model_registry.get(request.model_id)

        if not model_config:
            return InferenceResult(
                request_id=request.request_id,
                output_data=None,
                latency_ms=0,
                edge_location=location_id,
                error=f"Model {request.model_id} not found"
            )

        try:
            # Simulate inference based on model type
            if model_config.model_type == ModelType.CLASSIFICATION:
                output = self._simulate_classification(request.input_data)
            elif model_config.model_type == ModelType.REGRESSION:
                output = self._simulate_regression(request.input_data)
            elif model_config.model_type == ModelType.NLP:
                output = self._simulate_nlp(request.input_data)
            elif model_config.model_type == ModelType.COMPUTER_VISION:
                output = self._simulate_cv(request.input_data)
            else:
                output = self._simulate_generic(request.input_data)

            # Simulate processing time
            await asyncio.sleep(random.uniform(0.01, 0.1))

            return InferenceResult(
                request_id=request.request_id,
                output_data=output,
                latency_ms=0,  # Will be set by worker
                edge_location=location_id,
                confidence=random.uniform(0.8, 0.99)
            )

        except Exception as e:
            return InferenceResult(
                request_id=request.request_id,
                output_data=None,
                latency_ms=0,
                edge_location=location_id,
                error=str(e)
            )

    def _simulate_classification(self, input_data: Any) -> Dict[str, Any]:
        """Simulate classification inference"""
        classes = ['class_a', 'class_b', 'class_c']
        probabilities = np.random.dirichlet(np.ones(len(classes)))
        return {
            'prediction': classes[np.argmax(probabilities)],
            'probabilities': dict(zip(classes, probabilities.tolist()))
        }

    def _simulate_regression(self, input_data: Any) -> float:
        """Simulate regression inference"""
        return float(np.random.normal(50, 10))

    def _simulate_nlp(self, input_data: Any) -> Dict[str, Any]:
        """Simulate NLP inference"""
        return {
            'sentiment': random.choice(['positive', 'negative', 'neutral']),
            'confidence': random.uniform(0.7, 0.95),
            'entities': ['entity1', 'entity2']
        }

    def _simulate_cv(self, input_data: Any) -> Dict[str, Any]:
        """Simulate computer vision inference"""
        return {
            'detections': [
                {'label': 'object1', 'confidence': 0.89, 'bbox': [10, 20, 100, 150]},
                {'label': 'object2', 'confidence': 0.76, 'bbox': [200, 50, 300, 120]}
            ]
        }

    def _simulate_generic(self, input_data: Any) -> Any:
        """Generic simulation"""
        return {"result": "inference_completed", "value": random.random()}