"""
Calabi Model Deployment Package

Production-ready deployment infrastructure for Calabi compressed models.
"""

__version__ = "1.0.0"
__author__ = "Calabi Team"

# Import main components for easy access
from .optimized_inference import (
    BaseInferenceEngine,
    CPUOptimizedEngine,
    GPUOptimizedEngine,
    MobileOptimizedEngine,
    ONNXExporter,
    ONNXRuntimeEngine,
    ModelServer,
    create_optimized_engine,
    export_and_deploy
)

from .model_monitoring import (
    ModelMonitor,
    MetricsCollector,
    AnomalyDetector,
    PerformanceDashboard,
    quick_performance_check
)

from .model_serving import (
    ModelRegistry,
    BatchProcessor,
    InferenceService,
    APIServer,
    ProductionServer,
    quick_serve
)

__all__ = [
    # Inference engines
    'BaseInferenceEngine',
    'CPUOptimizedEngine',
    'GPUOptimizedEngine',
    'MobileOptimizedEngine',
    'ONNXExporter',
    'ONNXRuntimeEngine',
    'ModelServer',
    'create_optimized_engine',
    'export_and_deploy',
    
    # Monitoring
    'ModelMonitor',
    'MetricsCollector',
    'AnomalyDetector',
    'PerformanceDashboard',
    'quick_performance_check',
    
    # Serving
    'ModelRegistry',
    'BatchProcessor',
    'InferenceService',
    'APIServer',
    'ProductionServer',
    'quick_serve'
]