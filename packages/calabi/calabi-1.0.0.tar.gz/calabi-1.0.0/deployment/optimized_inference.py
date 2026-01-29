"""
Optimized Inference Engines for Calabi Compressed Models

This module provides optimized inference engines for different hardware platforms:
- CPU-optimized inference with threading
- GPU-accelerated inference with CUDA
- Mobile-friendly inference with quantization
- ONNX export and runtime support
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Union, Dict, Any, Optional, Tuple
import time
from concurrent.futures import ThreadPoolExecutor
import threading
from abc import ABC, abstractmethod

try:
    import onnx
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

from calabi import OptimizedCalabiYauLinear


class BaseInferenceEngine(ABC):
    """Abstract base class for inference engines."""
    
    def __init__(self, model: nn.Module, device: str = "cpu"):
        self.model = model
        self.device = torch.device(device)
        self.model.to(self.device)
        self.model.eval()
        
        # Performance tracking
        self.latency_history = []
        self.throughput_history = []
        
    @abstractmethod
    def infer(self, inputs: torch.Tensor) -> torch.Tensor:
        """Perform inference on inputs."""
        pass
    
    def benchmark(self, inputs: torch.Tensor, num_runs: int = 100) -> Dict[str, float]:
        """Benchmark the inference engine performance."""
        latencies = []
        
        # Warmup
        for _ in range(10):
            _ = self.infer(inputs)
        
        # Actual benchmarking
        for _ in range(num_runs):
            start_time = time.perf_counter()
            _ = self.infer(inputs)
            end_time = time.perf_counter()
            latencies.append((end_time - start_time) * 1000)  # Convert to milliseconds
        
        self.latency_history.extend(latencies)
        
        return {
            'mean_latency_ms': np.mean(latencies),
            'std_latency_ms': np.std(latencies),
            'min_latency_ms': np.min(latencies),
            'max_latency_ms': np.max(latencies),
            'p95_latency_ms': np.percentile(latencies, 95),
            'p99_latency_ms': np.percentile(latencies, 99),
            'throughput_samples_per_second': 1000 / np.mean(latencies) * inputs.shape[0]
        }


class CPUOptimizedEngine(BaseInferenceEngine):
    """CPU-optimized inference engine with threading support."""
    
    def __init__(self, model: nn.Module, num_threads: Optional[int] = None, 
                 use_openmp: bool = True):
        super().__init__(model, "cpu")
        
        # Configure CPU threading
        if num_threads is None:
            num_threads = torch.get_num_threads()
        
        torch.set_num_threads(num_threads)
        self.num_threads = num_threads
        
        if use_openmp and hasattr(torch.backends, 'openmp'):
            torch.backends.openmp.enabled = True
        
        # Thread pool for batch processing
        self.executor = ThreadPoolExecutor(max_workers=num_threads)
        
        print(f"CPU Engine initialized with {num_threads} threads")
    
    def infer(self, inputs: torch.Tensor) -> torch.Tensor:
        """Perform CPU-optimized inference."""
        with torch.no_grad():
            inputs = inputs.to(self.device)
            return self.model(inputs)
    
    def infer_batch_async(self, batch_inputs: list) -> list:
        """Process multiple inputs asynchronously."""
        futures = [self.executor.submit(self.infer, inp) for inp in batch_inputs]
        return [future.result() for future in futures]


class GPUOptimizedEngine(BaseInferenceEngine):
    """GPU-optimized inference engine with CUDA acceleration."""
    
    def __init__(self, model: nn.Module, device_id: int = 0, 
                 use_fp16: bool = False, use_graphs: bool = True):
        # Check CUDA availability
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is not available")
        
        device = f"cuda:{device_id}"
        super().__init__(model, device)
        
        self.use_fp16 = use_fp16
        self.use_graphs = use_graphs and torch.cuda.is_available()
        
        # Enable mixed precision if requested
        if use_fp16:
            self.model = self.model.half()
        
        # CUDA graph optimization for static shapes
        self.graph = None
        self.static_inputs = None
        self.static_outputs = None
        
        print(f"GPU Engine initialized on {device}")
        if use_fp16:
            print("Using FP16 precision")
        if use_graphs:
            print("CUDA graphs enabled for optimization")
    
    def infer(self, inputs: torch.Tensor) -> torch.Tensor:
        """Perform GPU-optimized inference."""
        with torch.no_grad():
            inputs = inputs.to(self.device)
            if self.use_fp16:
                inputs = inputs.half()
            
            # Use CUDA graphs for static shapes
            if self.use_graphs and self._can_use_graphs(inputs):
                return self._infer_with_graph(inputs)
            else:
                return self.model(inputs)
    
    def _can_use_graphs(self, inputs: torch.Tensor) -> bool:
        """Check if CUDA graphs can be used for these inputs."""
        if self.static_inputs is None:
            return False
        
        # Check if shape matches
        return inputs.shape == self.static_inputs.shape
    
    def _infer_with_graph(self, inputs: torch.Tensor) -> torch.Tensor:
        """Perform inference using CUDA graphs."""
        self.static_inputs.copy_(inputs)
        self.graph.replay()
        return self.static_outputs.clone()
    
    def warmup_graphs(self, input_shape: tuple):
        """Warm up CUDA graphs with a sample input shape."""
        if not self.use_graphs:
            return
        
        # Create static tensors
        sample_input = torch.randn(input_shape, device=self.device, 
                                 dtype=torch.half if self.use_fp16 else torch.float)
        
        # Capture graph
        s = torch.cuda.Stream()
        s.wait_stream(torch.cuda.current_stream())
        
        with torch.cuda.stream(s):
            for _ in range(3):  # Warmup iterations
                _ = self.model(sample_input)
        
        s.synchronize()
        torch.cuda.current_stream().wait_stream(s)
        
        # Capture the graph
        self.static_inputs = torch.empty_like(sample_input)
        self.static_outputs = torch.empty(sample_input.shape[0], 
                                        self.model(sample_input).shape[-1],
                                        device=self.device,
                                        dtype=torch.half if self.use_fp16 else torch.float)
        
        self.graph = torch.cuda.CUDAGraph()
        
        with torch.cuda.graph(self.graph):
            self.static_outputs = self.model(self.static_inputs)
        
        print(f"CUDA graphs captured for input shape {input_shape}")


class MobileOptimizedEngine(BaseInferenceEngine):
    """Mobile-optimized inference engine with quantization support."""
    
    def __init__(self, model: nn.Module, quantize: bool = True, 
                 use_dynamic_quant: bool = True):
        super().__init__(model, "cpu")
        
        self.quantize = quantize
        self.use_dynamic_quant = use_dynamic_quant
        self.quantized_model = None
        
        if quantize:
            self._apply_quantization()
        
        print("Mobile Engine initialized")
        if quantize:
            print("Quantization enabled")
    
    def _apply_quantization(self):
        """Apply quantization to the model."""
        try:
            if self.use_dynamic_quant:
                # Dynamic quantization
                self.quantized_model = torch.quantization.quantize_dynamic(
                    self.model, {nn.Linear}, dtype=torch.qint8
                )
            else:
                # Static quantization preparation
                self.model.qconfig = torch.quantization.get_default_qconfig('fbgemm')
                torch.quantization.prepare(self.model, inplace=True)
                # Calibration would happen here in practice
                torch.quantization.convert(self.model, inplace=True)
                self.quantized_model = self.model
            
            print("Model quantization completed")
        except Exception as e:
            print(f"Quantization failed: {e}")
            self.quantized_model = self.model
    
    def infer(self, inputs: torch.Tensor) -> torch.Tensor:
        """Perform quantized inference."""
        with torch.no_grad():
            inputs = inputs.to(self.device)
            model_to_use = self.quantized_model if self.quantize else self.model
            return model_to_use(inputs)


class ONNXExporter:
    """Export Calabi compressed models to ONNX format."""
    
    @staticmethod
    def export_model(model: nn.Module, input_shape: tuple, 
                    export_path: str, opset_version: int = 13,
                    dynamic_axes: Optional[Dict] = None) -> bool:
        """Export model to ONNX format."""
        if not ONNX_AVAILABLE:
            raise ImportError("ONNX is not available. Install with: pip install onnx onnxruntime")
        
        try:
            model.eval()
            dummy_input = torch.randn(input_shape)
            
            # Define dynamic axes if not provided
            if dynamic_axes is None:
                dynamic_axes = {
                    'input': {0: 'batch_size'},
                    'output': {0: 'batch_size'}
                }
            
            torch.onnx.export(
                model,
                dummy_input,
                export_path,
                export_params=True,
                opset_version=opset_version,
                do_constant_folding=True,
                input_names=['input'],
                output_names=['output'],
                dynamic_axes=dynamic_axes
            )
            
            # Validate the exported model
            onnx_model = onnx.load(export_path)
            onnx.checker.check_model(onnx_model)
            
            print(f"Model successfully exported to {export_path}")
            return True
            
        except Exception as e:
            print(f"ONNX export failed: {e}")
            return False
    
    @staticmethod
    def optimize_onnx_model(onnx_path: str, optimized_path: str) -> bool:
        """Optimize ONNX model for inference."""
        if not ONNX_AVAILABLE:
            return False
        
        try:
            # Load model
            model = onnx.load(onnx_path)
            
            # Apply optimizations
            from onnx import optimizer
            passes = ['eliminate_nop_transpose', 'eliminate_nop_pad', 
                     'fuse_consecutive_transposes', 'fuse_matmul_add_bias_into_gemm']
            
            optimized_model = optimizer.optimize(model, passes)
            onnx.save(optimized_model, optimized_path)
            
            print(f"ONNX model optimized and saved to {optimized_path}")
            return True
            
        except Exception as e:
            print(f"ONNX optimization failed: {e}")
            return False


class ONNXRuntimeEngine(BaseInferenceEngine):
    """High-performance inference using ONNX Runtime."""
    
    def __init__(self, onnx_path: str, providers: Optional[list] = None):
        if not ONNX_AVAILABLE:
            raise ImportError("ONNX Runtime is not available")
        
        # Initialize ONNX Runtime session
        if providers is None:
            providers = ['CPUExecutionProvider']
        
        self.session = ort.InferenceSession(onnx_path, providers=providers)
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        
        print(f"ONNX Runtime Engine initialized with providers: {providers}")
    
    def infer(self, inputs: Union[torch.Tensor, np.ndarray]) -> torch.Tensor:
        """Perform inference using ONNX Runtime."""
        # Convert to numpy if needed
        if isinstance(inputs, torch.Tensor):
            inputs_np = inputs.cpu().numpy()
        else:
            inputs_np = inputs
        
        # Run inference
        outputs_np = self.session.run([self.output_name], {self.input_name: inputs_np})[0]
        
        return torch.from_numpy(outputs_np)


class ModelServer:
    """Simple model serving infrastructure for compressed models."""
    
    def __init__(self, model: nn.Module, engine_type: str = "cpu", 
                 **engine_kwargs):
        # Initialize appropriate inference engine
        engine_map = {
            "cpu": CPUOptimizedEngine,
            "gpu": GPUOptimizedEngine,
            "mobile": MobileOptimizedEngine,
            "onnx": lambda m, **kw: ONNXRuntimeEngine(**kw)  # Special handling needed
        }
        
        if engine_type not in engine_map:
            raise ValueError(f"Unsupported engine type: {engine_type}")
        
        self.engine = engine_map[engine_type](model, **engine_kwargs)
        self.request_count = 0
        self.total_processing_time = 0.0
    
    def serve(self, inputs: torch.Tensor) -> Dict[str, Any]:
        """Serve inference requests with performance monitoring."""
        start_time = time.time()
        
        try:
            result = self.engine.infer(inputs)
            processing_time = time.time() - start_time
            
            self.request_count += 1
            self.total_processing_time += processing_time
            
            return {
                'result': result,
                'processing_time_ms': processing_time * 1000,
                'request_id': self.request_count,
                'status': 'success'
            }
        except Exception as e:
            return {
                'error': str(e),
                'processing_time_ms': (time.time() - start_time) * 1000,
                'request_id': self.request_count,
                'status': 'error'
            }
    
    def get_server_stats(self) -> Dict[str, Any]:
        """Get server performance statistics."""
        if self.request_count == 0:
            return {'requests_processed': 0}
        
        avg_processing_time = self.total_processing_time / self.request_count
        
        return {
            'requests_processed': self.request_count,
            'avg_processing_time_ms': avg_processing_time * 1000,
            'total_processing_time_s': self.total_processing_time,
            'current_throughput_requests_per_second': 1.0 / avg_processing_time if avg_processing_time > 0 else 0
        }


# Convenience functions for easy usage
def create_optimized_engine(model: nn.Module, target_platform: str, 
                          **kwargs) -> BaseInferenceEngine:
    """Factory function to create optimized inference engines."""
    platform_engines = {
        'cpu': CPUOptimizedEngine,
        'gpu': GPUOptimizedEngine,
        'mobile': MobileOptimizedEngine,
        'onnx_runtime': ONNXRuntimeEngine
    }
    
    if target_platform not in platform_engines:
        raise ValueError(f"Unknown platform: {target_platform}")
    
    return platform_engines[target_platform](model, **kwargs)


def export_and_deploy(model: nn.Module, input_shape: tuple, 
                     export_path: str, target_platform: str = "cpu") -> Dict[str, Any]:
    """Complete workflow: export model and create deployment engine."""
    results = {}
    
    # Export to ONNX if requested
    if target_platform == "onnx" or target_platform == "onnx_runtime":
        onnx_success = ONNXExporter.export_model(model, input_shape, export_path)
        results['onnx_export_success'] = onnx_success
        
        if onnx_success and target_platform == "onnx_runtime":
            try:
                engine = ONNXRuntimeEngine(export_path)
                results['engine'] = engine
            except Exception as e:
                results['engine_error'] = str(e)
    
    # Create native engine for other platforms
    elif target_platform in ["cpu", "gpu", "mobile"]:
        try:
            engine = create_optimized_engine(model, target_platform)
            results['engine'] = engine
        except Exception as e:
            results['engine_error'] = str(e)
    
    return results


__all__ = [
    'BaseInferenceEngine',
    'CPUOptimizedEngine',
    'GPUOptimizedEngine', 
    'MobileOptimizedEngine',
    'ONNXExporter',
    'ONNXRuntimeEngine',
    'ModelServer',
    'create_optimized_engine',
    'export_and_deploy'
]