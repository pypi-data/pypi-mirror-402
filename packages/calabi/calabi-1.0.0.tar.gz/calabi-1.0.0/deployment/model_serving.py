"""
Model Serving Infrastructure for Calabi Compressed Models

This module provides production-ready model serving capabilities:
- REST API server for model inference
- Batch processing support
- Health checks and monitoring
- Load balancing and scaling
- Model version management
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List, Any, Optional, Union
import asyncio
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    import uvicorn
    UVICORN_AVAILABLE = True
except ImportError:
    UVICORN_AVAILABLE = False

from .optimized_inference import (
    BaseInferenceEngine, CPUOptimizedEngine, GPUOptimizedEngine,
    MobileOptimizedEngine, ONNXRuntimeEngine, ModelServer
)
from .model_monitoring import MetricsCollector, quick_performance_check


# Pydantic models for API
class InferenceRequest(BaseModel):
    """Request model for inference API."""
    inputs: List[List[float]]  # 2D array of input data
    request_id: Optional[str] = None
    priority: Optional[str] = "normal"  # normal, high, low


class InferenceResponse(BaseModel):
    """Response model for inference API."""
    request_id: str
    results: List[List[float]]
    processing_time_ms: float
    status: str
    timestamp: str


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    uptime_seconds: float
    model_loaded: bool
    requests_processed: int
    avg_latency_ms: Optional[float]


@dataclass
class ModelVersion:
    """Model version information."""
    version: str
    path: str
    loaded_at: datetime
    performance_stats: Dict[str, float]


class ModelRegistry:
    """Manage multiple model versions."""
    
    def __init__(self):
        self.models: Dict[str, ModelVersion] = {}
        self.active_version: Optional[str] = None
        self.loading_lock = asyncio.Lock()
    
    def register_model(self, version: str, model_path: str, 
                      model: Optional[nn.Module] = None) -> bool:
        """Register a new model version."""
        try:
            # Load model if not provided
            if model is None:
                model = torch.load(model_path, map_location='cpu')
            
            # Quick performance check
            sample_input = torch.randn(1, model.in_features if hasattr(model, 'in_features') else 768)
            perf_stats = quick_performance_check(model, sample_input)
            
            self.models[version] = ModelVersion(
                version=version,
                path=model_path,
                loaded_at=datetime.now(),
                performance_stats=perf_stats
            )
            
            print(f"Model version {version} registered successfully")
            return True
            
        except Exception as e:
            print(f"Failed to register model {version}: {e}")
            return False
    
    def set_active_version(self, version: str) -> bool:
        """Set active model version."""
        if version in self.models:
            self.active_version = version
            print(f"Active model version set to {version}")
            return True
        return False
    
    def get_active_model(self) -> Optional[ModelVersion]:
        """Get currently active model."""
        if self.active_version and self.active_version in self.models:
            return self.models[self.active_version]
        return None
    
    def list_versions(self) -> List[Dict[str, Any]]:
        """List all registered model versions."""
        return [
            {
                'version': mv.version,
                'path': mv.path,
                'loaded_at': mv.loaded_at.isoformat(),
                'is_active': mv.version == self.active_version,
                'performance': mv.performance_stats
            }
            for mv in self.models.values()
        ]


class BatchProcessor:
    """Handle batch processing of inference requests."""
    
    def __init__(self, max_batch_size: int = 32, batch_timeout_ms: float = 10.0):
        self.max_batch_size = max_batch_size
        self.batch_timeout_ms = batch_timeout_ms
        self.pending_requests = []
        self.batch_lock = asyncio.Lock()
        self.batch_event = asyncio.Event()
    
    async def add_request(self, request: InferenceRequest) -> asyncio.Future:
        """Add request to batch processing queue."""
        future = asyncio.Future()
        
        async with self.batch_lock:
            self.pending_requests.append((request, future))
            
            # Trigger batch processing if batch is full
            if len(self.pending_requests) >= self.max_batch_size:
                self.batch_event.set()
        
        return future
    
    async def get_batch(self) -> List[tuple]:
        """Get a batch of requests for processing."""
        # Wait for either batch timeout or batch full
        try:
            await asyncio.wait_for(self.batch_event.wait(), 
                                 timeout=self.batch_timeout_ms / 1000)
        except asyncio.TimeoutError:
            pass
        
        async with self.batch_lock:
            # Reset event and get batch
            self.batch_event.clear()
            batch = self.pending_requests[:self.max_batch_size]
            self.pending_requests = self.pending_requests[self.max_batch_size:]
            
            return batch


class InferenceService:
    """Main inference service orchestrator."""
    
    def __init__(self, engine: BaseInferenceEngine, model_registry: ModelRegistry):
        self.engine = engine
        self.registry = model_registry
        self.metrics_collector = MetricsCollector()
        self.batch_processor = BatchProcessor()
        self.request_count = 0
        self.start_time = time.time()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
    
    async def process_single_request(self, request: InferenceRequest) -> InferenceResponse:
        """Process a single inference request."""
        request_id = request.request_id or str(uuid.uuid4())
        
        try:
            start_time = time.time()
            
            # Convert inputs to tensor
            inputs_tensor = torch.tensor(request.inputs, dtype=torch.float32)
            
            # Perform inference
            result_tensor = await asyncio.get_event_loop().run_in_executor(
                self.executor, self.engine.infer, inputs_tensor
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            # Collect metrics
            self.metrics_collector.collect_performance(processing_time, 
                                                     len(request.inputs) / (processing_time / 1000))
            
            # Convert result back to list
            results_list = result_tensor.tolist()
            
            self.request_count += 1
            
            return InferenceResponse(
                request_id=request_id,
                results=results_list,
                processing_time_ms=processing_time,
                status="success",
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            self.logger.error(f"Error processing request {request_id}: {e}")
            return InferenceResponse(
                request_id=request_id,
                results=[],
                processing_time_ms=(time.time() - start_time) * 1000,
                status="error",
                timestamp=datetime.now().isoformat()
            )
    
    async def process_batch_request(self, requests: List[InferenceRequest]) -> List[InferenceResponse]:
        """Process a batch of requests."""
        if not requests:
            return []
        
        # Combine all inputs
        all_inputs = []
        request_mapping = {}  # Map batch index to original requests
        
        for i, req in enumerate(requests):
            inputs_tensor = torch.tensor(req.inputs, dtype=torch.float32)
            all_inputs.append(inputs_tensor)
            request_mapping[i] = req
        
        try:
            start_time = time.time()
            
            # Batch inference
            batched_input = torch.cat(all_inputs, dim=0)
            batched_result = await asyncio.get_event_loop().run_in_executor(
                self.executor, self.engine.infer, batched_input
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            # Split results back to individual requests
            responses = []
            split_results = torch.split(batched_result, [inp.shape[0] for inp in all_inputs])
            
            for i, (req, result) in enumerate(zip(requests, split_results)):
                response = InferenceResponse(
                    request_id=req.request_id or str(uuid.uuid4()),
                    results=result.tolist(),
                    processing_time_ms=processing_time / len(requests),  # Approximate per request
                    status="success",
                    timestamp=datetime.now().isoformat()
                )
                responses.append(response)
            
            # Collect metrics
            self.metrics_collector.collect_performance(
                processing_time, 
                sum(len(req.inputs) for req in requests) / (processing_time / 1000)
            )
            
            self.request_count += len(requests)
            return responses
            
        except Exception as e:
            self.logger.error(f"Batch processing error: {e}")
            # Return individual error responses
            return [
                InferenceResponse(
                    request_id=req.request_id or str(uuid.uuid4()),
                    results=[],
                    processing_time_ms=0,
                    status="error",
                    timestamp=datetime.now().isoformat()
                )
                for req in requests
            ]


class APIServer:
    """FastAPI-based REST server for model serving."""
    
    def __init__(self, inference_service: InferenceService):
        if not FASTAPI_AVAILABLE:
            raise ImportError("FastAPI is required for API server")
        
        self.app = FastAPI(title="Calabi Model Server", version="1.0.0")
        self.service = inference_service
        self.setup_routes()
    
    def setup_routes(self):
        """Setup API routes."""
        
        @self.app.post("/predict", response_model=InferenceResponse)
        async def predict(request: InferenceRequest):
            """Single prediction endpoint."""
            response = await self.service.process_single_request(request)
            if response.status == "error":
                raise HTTPException(status_code=500, detail="Prediction failed")
            return response
        
        @self.app.post("/predict/batch", response_model=List[InferenceResponse])
        async def predict_batch(requests: List[InferenceRequest]):
            """Batch prediction endpoint."""
            responses = await self.service.process_batch_request(requests)
            return responses
        
        @self.app.get("/health", response_model=HealthResponse)
        async def health_check():
            """Health check endpoint."""
            uptime = time.time() - self.service.start_time
            active_model = self.service.registry.get_active_model()
            
            recent_perf = self.service.metrics_collector.get_recent_performance(100)
            avg_latency = np.mean([m.latency_ms for m in recent_perf]) if recent_perf else None
            
            return HealthResponse(
                status="healthy",
                uptime_seconds=uptime,
                model_loaded=active_model is not None,
                requests_processed=self.service.request_count,
                avg_latency_ms=avg_latency
            )
        
        @self.app.get("/models", response_model=List[Dict[str, Any]])
        async def list_models():
            """List available model versions."""
            return self.service.registry.list_versions()
        
        @self.app.post("/models/activate/{version}")
        async def activate_model(version: str):
            """Activate a specific model version."""
            success = self.service.registry.set_active_version(version)
            if not success:
                raise HTTPException(status_code=404, detail=f"Model version {version} not found")
            return {"status": "success", "activated_version": version}
        
        @self.app.get("/metrics/recent")
        async def get_recent_metrics(limit: int = 100):
            """Get recent performance metrics."""
            perf_metrics = self.service.metrics_collector.get_recent_performance(limit)
            acc_metrics = self.service.metrics_collector.get_recent_accuracy(limit)
            
            return {
                "performance": [asdict(m) for m in perf_metrics],
                "accuracy": [asdict(m) for m in acc_metrics]
            }
    
    def run(self, host: str = "0.0.0.0", port: int = 8000, **kwargs):
        """Run the API server."""
        if not UVICORN_AVAILABLE:
            raise ImportError("Uvicorn is required to run the server")
        
        print(f"Starting model server on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port, **kwargs)


class ProductionServer:
    """Production-ready server with all components integrated."""
    
    def __init__(self, model: nn.Module, engine_type: str = "cpu", 
                 port: int = 8000, **engine_kwargs):
        # Initialize components
        self.registry = ModelRegistry()
        self.engine = self._create_engine(model, engine_type, **engine_kwargs)
        self.inference_service = InferenceService(self.engine, self.registry)
        self.api_server = APIServer(self.inference_service) if FASTAPI_AVAILABLE else None
        self.port = port
    
    def _create_engine(self, model: nn.Module, engine_type: str, **kwargs) -> BaseInferenceEngine:
        """Create appropriate inference engine."""
        engine_classes = {
            "cpu": CPUOptimizedEngine,
            "gpu": GPUOptimizedEngine,
            "mobile": MobileOptimizedEngine,
            "onnx": ONNXRuntimeEngine
        }
        
        if engine_type not in engine_classes:
            raise ValueError(f"Unknown engine type: {engine_type}")
        
        return engine_classes[engine_type](model, **kwargs)
    
    def register_model_version(self, version: str, model_path: str) -> bool:
        """Register a model version."""
        return self.registry.register_model(version, model_path)
    
    def start_server(self, host: str = "0.0.0.0", **kwargs):
        """Start the production server."""
        if not self.api_server:
            raise RuntimeError("API server not available. Install FastAPI and Uvicorn.")
        
        # Register initial model
        self.registry.register_model("v1.0", "model_path_placeholder", 
                                   self.engine.model)
        self.registry.set_active_version("v1.0")
        
        # Start server
        self.api_server.run(host=host, port=self.port, **kwargs)
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get comprehensive service statistics."""
        return {
            'server_info': {
                'port': self.port,
                'engine_type': type(self.engine).__name__,
                'models_registered': len(self.registry.models),
                'active_model': self.registry.active_version
            },
            'performance': self.inference_service.metrics_collector.get_recent_performance(10),
            'request_count': self.inference_service.request_count,
            'uptime_seconds': time.time() - self.inference_service.start_time
        }


# Convenience functions
def create_production_server(model: nn.Module, engine_type: str = "cpu", 
                           port: int = 8000, **engine_kwargs) -> ProductionServer:
    """Create and configure a production server."""
    return ProductionServer(model, engine_type, port, **engine_kwargs)


def quick_serve(model: nn.Module, port: int = 8000):
    """Quick start for serving a model."""
    try:
        server = create_production_server(model, port=port)
        server.start_server()
    except Exception as e:
        print(f"Failed to start server: {e}")
        print("Make sure to install required dependencies:")
        print("pip install fastapi uvicorn")


__all__ = [
    'ModelRegistry',
    'BatchProcessor',
    'InferenceService',
    'APIServer',
    'ProductionServer',
    'InferenceRequest',
    'InferenceResponse',
    'HealthResponse',
    'create_production_server',
    'quick_serve'
]