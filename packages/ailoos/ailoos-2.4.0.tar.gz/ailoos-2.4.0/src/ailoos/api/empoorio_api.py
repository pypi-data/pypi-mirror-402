"""EmpoorioLM API - API funcional para modelo de lenguaje EmpoorioLM.
Implementa generación de texto real con transformers y PyTorch.
NO contiene respuestas simuladas ni mocks.
"""

import torch
import json
import os
import time
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass
import re
import asyncio
from datetime import datetime
import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

# Real imports
from transformers import AutoTokenizer, AutoModelForCausalLM

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("empoorio_api")

# Configuration Defaults
DEFAULT_MODEL_ID = os.getenv("EMPOORIO_MODEL_ID", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
TORCH_DTYPE = torch.bfloat16 if torch.cuda.is_available() or torch.cuda.is_bf16_supported() else torch.float32

@dataclass
class GenerationConfig:
    """Configuración para generación de texto."""
    max_new_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    do_sample: bool = True
    repetition_penalty: float = 1.1
    pad_token_id: Optional[int] = None
    eos_token_id: Optional[int] = None

@dataclass
class EmpoorioLMApiConfig:
    """Configuración de la API EmpoorioLM."""
    model_path: str = DEFAULT_MODEL_ID
    device: str = DEVICE
    cache_dir: Optional[str] = None
    trust_remote_code: bool = False

# Pydantic models
class GenerateRequest(BaseModel):
    """Request model for text generation."""
    prompt: str = Field(..., description="The input prompt for text generation")
    max_length: Optional[int] = Field(512, description="Maximum length of generated text")
    temperature: Optional[float] = Field(0.7, description="Sampling temperature")
    model: Optional[str] = Field("empoorio-lm", description="Model to use for generation")
    stream: Optional[bool] = Field(False, description="Whether to stream the response")

class GenerateResponse(BaseModel):
    """Response model for text generation."""
    response: str
    usage: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    model_loaded: bool
    device: str
    model_id: str
    timestamp: str

class ModelsResponse(BaseModel):
    models: List[str]

class EmpoorioLMApi:
    """
    API funcional para modelo de lenguaje EmpoorioLM.
    Implementa generación de texto real con transformers y PyTorch.
    """

    def __init__(self, config: EmpoorioLMApiConfig = None):
        self.config = config or EmpoorioLMApiConfig()
        self.device = self.config.device
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
        
        logger.info(f"🦾 Inicializando EmpoorioLM API (Real) en {self.device}...")
        self._load_model()

    def _load_model(self):
        """Carga el modelo real usando Transformers."""
        try:
            logger.info(f"📥 Cargando modelo: {self.config.model_path}")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.model_path, 
                trust_remote_code=self.config.trust_remote_code
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.model_path,
                torch_dtype=TORCH_DTYPE,
                device_map=self.device,
                trust_remote_code=self.config.trust_remote_code,
                low_cpu_mem_usage=True
            )
            self.is_loaded = True
            logger.info("✅ Modelo cargado exitosamente.")
        except Exception as e:
            logger.error(f"❌ Error fatal cargando el modelo: {e}")
            self.is_loaded = False
            # No fallback to mock. If it fails, it fails.
            # user wants real system.

    def generate_text(self, prompt: str, generation_config: GenerationConfig = None, **kwargs) -> Dict[str, Any]:
        """Genera texto real."""
        if not self.is_loaded or not self.model:
            raise RuntimeError("El modelo no está cargado. Verifique logs del servidor.")

        generation_config = generation_config or GenerationConfig()
        
        try:
            start_time = time.time()
            
            # Simple chat formatting for TinyLlama/Generic
            formatted_prompt = f"<|user|>\n{prompt}</s>\n<|assistant|>\n"
            
            inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.device)
            input_len = inputs.input_ids.shape[1]

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=generation_config.max_new_tokens,
                    temperature=generation_config.temperature,
                    top_p=generation_config.top_p,
                    do_sample=generation_config.do_sample,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            generated_text = self.tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True)
            inference_time = time.time() - start_time
            
            return {
                "generated_text": generated_text.strip(),
                "metrics": {
                    "prompt_tokens": input_len,
                    "completion_tokens": len(outputs[0]) - input_len,
                    "total_tokens": len(outputs[0]),
                    "inference_time": inference_time
                },
                "success": True
            }

        except Exception as e:
            logger.error(f"Generation error: {e}")
            raise RuntimeError(f"Inference failed: {str(e)}")

    def unload_model(self):
        if self.model:
            del self.model
        if self.tokenizer:
            del self.tokenizer
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        self.is_loaded = False
        logger.info("Modelo descargado.")

# Clase compatible con la estructura anterior para facilitar integración
class EmpoorioLMAPI:
    def __init__(self):
        self.api = EmpoorioLMApi()
        self.app = FastAPI(title="EmpoorioLM API (Real)", version="2.0.0")
        self._setup_routes()

    def _setup_routes(self):
        @self.app.post("/generate", response_model=GenerateResponse)
        async def generate(request: GenerateRequest):
            try:
                gen_config = GenerationConfig(
                    max_new_tokens=request.max_length or 512,
                    temperature=request.temperature or 0.7
                )
                # Ejecutar en thread pool para no bloquear
                result = await asyncio.to_thread(
                    self.api.generate_text, request.prompt, gen_config
                )
                return GenerateResponse(
                    response=result["generated_text"],
                    usage=result["metrics"],
                    meta={"device": self.api.device, "model": self.api.config.model_path}
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/generate/stream")
        async def generate_stream(request: GenerateRequest):
            async def event_stream():
                try:
                    gen_config = GenerationConfig(
                        max_new_tokens=request.max_length or 512,
                        temperature=request.temperature or 0.7
                    )
                    result = await asyncio.to_thread(
                        self.api.generate_text, request.prompt, gen_config
                    )
                    payload = {
                        "content": result["generated_text"],
                        "usage": result["metrics"],
                        "done": True
                    }
                    yield f"data: {json.dumps(payload)}\n\n"
                except Exception as e:
                    error_payload = {"error": str(e), "done": True}
                    yield f"data: {json.dumps(error_payload)}\n\n"

            return StreamingResponse(event_stream(), media_type="text/event-stream")

        @self.app.get("/status", response_model=HealthResponse)
        async def status():
            return HealthResponse(
                status="healthy" if self.api.is_loaded else "error",
                model_loaded=self.api.is_loaded,
                device=self.api.device,
                model_id=self.api.config.model_path,
                timestamp=datetime.now().isoformat()
            )

        @self.app.get("/health", response_model=HealthResponse)
        async def health():
            return HealthResponse(
                status="healthy" if self.api.is_loaded else "error",
                model_loaded=self.api.is_loaded,
                device=self.api.device,
                model_id=self.api.config.model_path,
                timestamp=datetime.now().isoformat()
            )
            
        @self.app.get("/models", response_model=ModelsResponse)
        async def models():
            return ModelsResponse(models=[self.api.config.model_path])

    def create_app(self):
        return self.app

# Funciones globales para compatibilidad
def create_empoorio_app():
    api = EmpoorioLMAPI()
    return api.create_app()

def generate_text(prompt: str, **kwargs):
    # One-off generation
    api = EmpoorioLMApi()
    try:
        res = api.generate_text(prompt)
        return res["generated_text"]
    finally:
        api.unload_model()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        print("🚀 Starting Internal EmpoorioLM API Server...")
        uvicorn.run(create_empoorio_app(), host="0.0.0.0", port=8000)
    else:
        print("Use 'python -m src.ailoos.api.empoorio_api server' to start")
