"""
Deployment Example for Calabi Compressed Models

This example demonstrates how to deploy Calabi compressed models using
the optimized inference engines and serving infrastructure.
"""

import torch
import torch.nn as nn
import numpy as np
from pathlib import Path
import time
import json

# Import deployment components
from deployment.optimized_inference import (
    CPUOptimizedEngine, GPUOptimizedEngine, MobileOptimizedEngine,
    ONNXExporter, ONNXRuntimeEngine, ModelServer, export_and_deploy
)
from deployment.model_monitoring import (
    ModelMonitor, MetricsCollector, quick_performance_check
)
from deployment.model_serving import ProductionServer, quick_serve


def create_sample_model():
    """Create a sample model for demonstration."""
    model = nn.Sequential(
        nn.Linear(768, 1024),
        nn.ReLU(),
        nn.Linear(1024, 512),
        nn.ReLU(),
        nn.Linear(512, 256),
        nn.ReLU(),
        nn.Linear(256, 10)
    )
    return model


def demonstrate_inference_engines():
    """Demonstrate different inference engines."""
    print("=== Inference Engine Demonstration ===")
    
    # Create sample model and compress it
    model = create_sample_model()
    print(f"Original model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Compress the model (simulate compression)
    from calabi import OptimizedCYModelUtils
    OptimizedCYModelUtils.replace_linear_layers(model, compression_ratio=0.5)
    print(f"Compressed model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Create sample input
    sample_input = torch.randn(32, 768)
    
    # Test CPU engine
    print("\n1. CPU Optimized Engine:")
    cpu_engine = CPUOptimizedEngine(model, num_threads=4)
    cpu_stats = cpu_engine.benchmark(sample_input, num_runs=50)
    print(f"   Mean latency: {cpu_stats['mean_latency_ms']:.2f}ms")
    print(f"   Throughput: {cpu_stats['throughput_samples_per_second']:.2f} samples/sec")
    
    # Test GPU engine (if available)
    if torch.cuda.is_available():
        print("\n2. GPU Optimized Engine:")
        try:
            gpu_engine = GPUOptimizedEngine(model, use_fp16=True)
            gpu_stats = gpu_engine.benchmark(sample_input.cuda(), num_runs=50)
            print(f"   Mean latency: {gpu_stats['mean_latency_ms']:.2f}ms")
            print(f"   Throughput: {gpu_stats['throughput_samples_per_second']:.2f} samples/sec")
        except Exception as e:
            print(f"   GPU engine failed: {e}")
    
    # Test mobile engine
    print("\n3. Mobile Optimized Engine:")
    mobile_engine = MobileOptimizedEngine(model, quantize=True)
    mobile_stats = mobile_engine.benchmark(sample_input, num_runs=50)
    print(f"   Mean latency: {mobile_stats['mean_latency_ms']:.2f}ms")
    print(f"   Throughput: {mobile_stats['throughput_samples_per_second']:.2f} samples/sec")


def demonstrate_onnx_export():
    """Demonstrate ONNX export capabilities."""
    print("\n=== ONNX Export Demonstration ===")
    
    model = create_sample_model()
    
    # Export to ONNX
    export_path = "sample_model.onnx"
    success = ONNXExporter.export_model(model, (1, 768), export_path)
    
    if success:
        print(f"Model exported to {export_path}")
        
        # Test ONNX Runtime engine
        try:
            onnx_engine = ONNXRuntimeEngine(export_path)
            sample_input = torch.randn(16, 768)
            result = onnx_engine.infer(sample_input)
            print(f"ONNX inference successful, output shape: {result.shape}")
        except Exception as e:
            print(f"ONNX Runtime test failed: {e}")
    else:
        print("ONNX export failed")


def demonstrate_monitoring():
    """Demonstrate model monitoring capabilities."""
    print("\n=== Model Monitoring Demonstration ===")
    
    # Create monitor
    monitor = ModelMonitor(buffer_size=100)
    
    # Quick performance check
    model = create_sample_model()
    sample_input = torch.randn(16, 768)
    
    perf_stats = quick_performance_check(model, sample_input, num_iterations=20)
    print("Performance Statistics:")
    for key, value in perf_stats.items():
        print(f"  {key}: {value:.4f}")
    
    # Collect some metrics
    for i in range(10):
        latency = np.random.normal(50, 10)  # Simulate varying latency
        throughput = 1000 / latency * 16    # Calculate throughput
        monitor.metrics_collector.collect_performance(latency, throughput)
    
    # Generate report
    recent_perf = monitor.metrics_collector.get_recent_performance(5)
    print(f"\nCollected {len(recent_perf)} performance samples")
    if recent_perf:
        print(f"Average recent latency: {np.mean([m.latency_ms for m in recent_perf]):.2f}ms")


def demonstrate_serving():
    """Demonstrate model serving capabilities."""
    print("\n=== Model Serving Demonstration ===")
    
    try:
        # Create a simple model
        model = create_sample_model()
        
        # Create production server
        server = ProductionServer(model, engine_type="cpu", port=8001)
        
        print("Production server created successfully")
        print("Server configuration:")
        print(f"  - Port: {server.port}")
        print(f"  - Engine type: {type(server.engine).__name__}")
        print(f"  - Models registered: {len(server.registry.models)}")
        
        # Show service stats
        stats = server.get_service_stats()
        print(f"  - Request count: {stats['request_count']}")
        
    except ImportError as e:
        print(f"Server demonstration requires additional dependencies: {e}")
        print("Install with: pip install fastapi uvicorn")


def demonstrate_complete_workflow():
    """Demonstrate complete deployment workflow."""
    print("\n=== Complete Deployment Workflow ===")
    
    # 1. Create and compress model
    print("Step 1: Creating and compressing model...")
    model = create_sample_model()
    original_params = sum(p.numel() for p in model.parameters())
    
    from calabi import OptimizedCYModelUtils
    compressed_count = OptimizedCYModelUtils.replace_linear_layers(
        model, compression_ratio=0.5
    )
    compressed_params = sum(p.numel() for p in model.parameters())
    
    print(f"  - Original parameters: {original_params:,}")
    print(f"  - Compressed parameters: {compressed_params:,}")
    print(f"  - Compression ratio: {(1 - compressed_params/original_params)*100:.1f}%")
    print(f"  - Layers compressed: {compressed_count}")
    
    # 2. Export for deployment
    print("\nStep 2: Exporting for deployment...")
    export_path = "deployed_model.onnx"
    deployment_results = export_and_deploy(
        model, (1, 768), export_path, target_platform="cpu"
    )
    
    if 'engine' in deployment_results:
        print("  - Deployment engine created successfully")
    else:
        print("  - Deployment engine creation failed")
    
    # 3. Performance benchmarking
    print("\nStep 3: Performance benchmarking...")
    sample_input = torch.randn(32, 768)
    perf_stats = quick_performance_check(model, sample_input)
    
    print("  Performance metrics:")
    print(f"    Mean latency: {perf_stats['mean_latency_ms']:.2f}ms")
    print(f"    Throughput: {perf_stats['throughput_samples_per_sec']:.2f} samples/sec")
    print(f"    95th percentile: {perf_stats['p95_latency_ms']:.2f}ms")
    
    # 4. Create monitoring setup
    print("\nStep 4: Setting up monitoring...")
    monitor = ModelMonitor()
    print("  - Monitor created with default configuration")
    
    # 5. Save deployment configuration
    print("\nStep 5: Saving deployment configuration...")
    deployment_config = {
        "model_info": {
            "original_parameters": original_params,
            "compressed_parameters": compressed_params,
            "compression_ratio": (1 - compressed_params/original_params),
            "layers_compressed": compressed_count
        },
        "deployment": {
            "target_platform": "cpu",
            "export_path": export_path,
            "performance": perf_stats
        },
        "monitoring": {
            "enabled": True,
            "buffer_size": 1000
        }
    }
    
    config_path = "deployment_config.json"
    with open(config_path, 'w') as f:
        json.dump(deployment_config, f, indent=2)
    
    print(f"  - Configuration saved to {config_path}")
    
    print("\n✅ Complete deployment workflow finished successfully!")


def main():
    """Run all demonstrations."""
    print("Calabi Model Deployment Examples")
    print("=" * 40)
    
    try:
        demonstrate_inference_engines()
        demonstrate_onnx_export()
        demonstrate_monitoring()
        demonstrate_serving()
        demonstrate_complete_workflow()
        
        print("\n🎉 All demonstrations completed!")
        print("\nNext steps for production deployment:")
        print("1. Install production dependencies: pip install fastapi uvicorn")
        print("2. Choose appropriate inference engine for your hardware")
        print("3. Export model to ONNX for cross-platform compatibility")
        print("4. Set up monitoring for production metrics")
        print("5. Deploy using the ProductionServer class")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()