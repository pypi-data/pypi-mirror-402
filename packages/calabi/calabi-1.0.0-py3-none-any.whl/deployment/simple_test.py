"""
Simple test for deployment components
"""

import torch
import torch.nn as nn

def test_deployment_components():
    print("Testing Calabi Deployment Components")
    print("=" * 40)
    
    # Test inference engines
    try:
        from deployment.optimized_inference import CPUOptimizedEngine
        print("✓ CPU Optimized Engine imported successfully")
        
        # Create test model
        model = nn.Linear(768, 10)
        engine = CPUOptimizedEngine(model)
        print("✓ CPU Engine instantiated successfully")
        
    except Exception as e:
        print(f"✗ CPU Engine test failed: {e}")
    
    # Test ONNX exporter
    try:
        from deployment.optimized_inference import ONNXExporter
        print("✓ ONNX Exporter imported successfully")
    except Exception as e:
        print(f"✗ ONNX Exporter test failed: {e}")
    
    # Test monitoring
    try:
        from deployment.model_monitoring import ModelMonitor, quick_performance_check
        print("✓ Monitoring components imported successfully")
        
        # Test quick performance check
        model = nn.Linear(768, 10)
        sample_input = torch.randn(16, 768)
        stats = quick_performance_check(model, sample_input, num_iterations=10)
        print(f"✓ Performance check completed: {stats['mean_latency_ms']:.2f}ms average")
        
        # Test monitor creation
        monitor = ModelMonitor()
        print("✓ Model Monitor created successfully")
        
    except Exception as e:
        print(f"✗ Monitoring test failed: {e}")
    
    # Test model serving components
    try:
        from deployment.model_serving import ModelRegistry, BatchProcessor
        print("✓ Model Serving components imported successfully")
        
        registry = ModelRegistry()
        processor = BatchProcessor()
        print("✓ Model Serving components instantiated successfully")
        
    except Exception as e:
        print(f"✗ Model Serving test failed: {e}")
    
    print("\n" + "=" * 40)
    print("Deployment component testing completed!")

if __name__ == "__main__":
    test_deployment_components()