"""
Advanced usage example for the Calabi-Yau compression library.

This example demonstrates advanced features like fine-tuning,
gradient checking, and custom configurations.
"""

import torch
import torch.nn as nn
from calabi_yau_compression import OptimizedCalabiYauLinear
from calabi_yau_compression.utils import OptimizedCYModelUtils


def example_gradient_flow_check():
    """
    Example: Checking gradient flow in compressed layers
    """
    print("=== Gradient Flow Check Example ===")
    
    # Create a layer
    original = nn.Linear(256, 128)
    compressed = OptimizedCalabiYauLinear(original, compression_ratio=0.5)
    
    # Create input with gradients enabled
    x = torch.randn(4, 256, requires_grad=True)
    
    # Check gradient flow
    grad_stats = compressed.check_gradient_flow(x)
    
    print("Gradient flow statistics:")
    for name, stats in grad_stats.items():
        print(f"  {name}: valid={stats['valid']}, grad_norm={stats['grad_norm']:.6f}")
    
    print()


def example_spectral_analysis():
    """
    Example: Understanding spectral properties
    """
    print("=== Spectral Analysis Example ===")
    
    # Create a layer with specific properties
    original = nn.Linear(128, 64)
    
    # Set some specific weights for analysis
    with torch.no_grad():
        # Create weights with decaying singular values
        U = torch.randn(64, 64)
        U, _ = torch.linalg.qr(U)
        V = torch.randn(128, 64)
        V, _ = torch.linalg.qr(V)
        
        # Create singular values with power law decay
        S = torch.pow(torch.linspace(1.0, 0.01, 64), 1.5)
        
        original.weight.copy_(U @ torch.diag(S) @ V.t())
        original.bias.zero_()
    
    # Compress with different energy thresholds
    for threshold in [0.8, 0.9, 0.95]:
        compressed = OptimizedCalabiYauLinear(
            original_linear=original,
            energy_threshold=threshold
        )
        print(f"Energy threshold {threshold}: selected rank {compressed.rank}")
    
    print()


def example_fine_tuning_setup():
    """
    Example: Setting up for fine-tuning after compression
    """
    print("=== Fine-tuning Setup Example ===")
    
    # Create a simple model
    model = nn.Sequential(
        nn.Linear(512, 1024),
        nn.ReLU(),
        nn.Linear(1024, 256)
    )
    
    # Compress the model
    OptimizedCYModelUtils.replace_linear_layers(
        model, 
        compression_ratio=0.5,
        min_features=128
    )
    
    # Prepare for fine-tuning
    # Option 1: Fine-tune all parameters
    all_params = list(model.parameters())
    optimizer_all = torch.optim.Adam(all_params, lr=1e-4)
    
    # Option 2: Fine-tune only specific parameters (e.g., reconstruction bias)
    rec_bias_params = []
    for name, param in model.named_parameters():
        if 'reconstruction_bias' in name:
            rec_bias_params.append(param)
    
    optimizer_selective = torch.optim.Adam(rec_bias_params, lr=1e-3)
    
    print(f"Total parameters: {sum(p.numel() for p in model.parameters())}")
    print(f"Reconstruction bias parameters: {sum(p.numel() for p in rec_bias_params)}")
    print("Optimizers created for fine-tuning")
    print()


def example_error_handling():
    """
    Example: Handling edge cases and errors
    """
    print("=== Error Handling Example ===")
    
    try:
        # Create a problematic layer
        original = nn.Linear(10, 10)
        with torch.no_grad():
            original.weight.zero_()  # Zero weights
            original.bias.zero_()
        
        # This should handle the zero matrix gracefully
        compressed = OptimizedCalabiYauLinear(original, compression_ratio=0.5)
        print(f"Zero matrix handled, rank: {compressed.rank}")
        
        # Test with problematic input
        x = torch.randn(2, 10)
        output = compressed(x)
        print(f"Forward pass successful: {output.shape}")
        
    except Exception as e:
        print(f"Error occurred: {e}")
    
    print()


def main():
    """
    Run all advanced examples
    """
    print("Calabi-Yau Compression Library - Advanced Usage Examples")
    print("=" * 60)
    print()
    
    example_gradient_flow_check()
    example_spectral_analysis()
    example_fine_tuning_setup()
    example_error_handling()
    
    print("All advanced examples completed successfully!")
    print()
    print("Library is ready for production use with proper error handling and analysis tools.")


if __name__ == "__main__":
    main()