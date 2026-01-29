from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from .physical_node_v2 import PhysicalNodeV2

logger = logging.getLogger(__name__)

app = FastAPI(title="Ailoos Node API", version="1.0.0")

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Dict[str, str]]
    max_tokens: int = 100
    temperature: float = 0.7

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]

@app.get("/v1/health")
async def health():
    return {"status": "ok"}

@app.get("/v1/models")
async def list_models(request: Request):
    """List available models."""
    node: "PhysicalNodeV2" = request.app.state.node
    if not node.model_manager:
        return {"data": []}
    
    # Use ModelManager to list models (local only for now?)
    models = await node.model_manager.list_models(include_local=True)
    return {"data": models}

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: Request, body: ChatCompletionRequest):
    """OpenAI-compatible chat completion endpoint."""
    node: "PhysicalNodeV2" = request.app.state.node
    
    # Ensure InferenceEngine is available
    if not hasattr(node, "inference_engine") or not node.inference_engine:
        raise HTTPException(status_code=503, detail="Inference engine not ready")
        
    try:
        # Simple prompt construction from messages
        prompt = ""
        for msg in body.messages:
            prompt += f"{msg['role']}: {msg['content']}\n"
        prompt += "assistant: "
        
        result = await node.inference_engine.generate(
            model_id=body.model,
            prompt=prompt,
            max_length=body.max_tokens,
            temperature=body.temperature
        )
        
        import time
        return {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": body.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": result.get("generated_text", "")
                    },
                    "finish_reason": "stop"
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Inference error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
