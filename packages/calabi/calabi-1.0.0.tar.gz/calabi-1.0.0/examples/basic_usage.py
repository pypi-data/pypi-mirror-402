"""
Basic usage example for the Calabi-Yau compression library.

This example demonstrates how to use the library to compress
individual layers and entire models.
"""

import torch
import torch.nn as nn
from calabi_yau_compression import OptimizedCalabiYauLinear
from calabi_yau_compression.utils import OptimizedCYModelUtils, print_model_stats


def example_single_layer_compression():
    """
    Example: Compressing a single linear layer
    """
    print("=== Single Layer Compression Example ===")
    
    # Create an original linear layer
    original_layer = nn.Linear(1024, 512)
    
    # Compress it using Calabi-Yau compression
    compressed_layer = OptimizedCalabiYauLinear(
        original_linear=original_layer,
        compression_ratio=0.5  # Keep 50% of parameters
    )
    
    # Test the compressed layer
    x = torch.randn(16, 1024)
    with torch.no_grad():
        original_output = original_layer(x)
        compressed_output = compressed_layer(x)
    
    print(f"Original layer parameters: {sum(p.numel() for p in original_layer.parameters())}")
    print(f"Compressed layer parameters: {sum(p.numel() for p in compressed_layer.parameters())}")
    print(f"Input shape: {x.shape}")
    print(f"Output shape: {original_output.shape}")
    print(f"Outputs close: {torch.allclose(original_output, compressed_output, atol=1e-3)}")
    print()


def example_model_compression():
    """
    Example: Compressing an entire model
    """
    print("=== Model Compression Example ===")
    
    # Create a simple feedforward model
    model = nn.Sequential(
        nn.Linear(768, 2048),
        nn.ReLU(),
        nn.Linear(2048, 1024),
        nn.ReLU(),
        nn.Linear(1024, 512)
    )
    
    print("Original model:")
    print_model_stats(model, "Original")
    
    # Compress all linear layers in the model
    num_compressed = OptimizedCYModelUtils.replace_linear_layers(
        model=model,
        compression_ratio=0.5,  # 50% compression
        min_features=128,       # Only compress layers with at least 128 features
        verbose=True
    )
    
    print(f"\nCompressed {num_compressed} layers")
    print("\nCompressed model:")
    print_model_stats(model, "Compressed")
    
    # Test the compressed model
    x = torch.randn(8, 768)
    with torch.no_grad():
        output = model(x)
    
    print(f"Model input: {x.shape}")
    print(f"Model output: {output.shape}")
    print()


def example_custom_compression():
    """
    Example: Custom compression settings
    """
    print("=== Custom Compression Settings Example ===")
    
    # Create a layer to compress
    original = nn.Linear(512, 512)
    
    # Compress with energy threshold instead of ratio
    compressed = OptimizedCalabiYauLinear(
        original_linear=original,
        energy_threshold=0.95  # Keep 95% of energy
    )
    
    print(f"Original parameters: {sum(p.numel() for p in original.parameters())}")
    print(f"Compressed parameters: {sum(p.numel() for p in compressed.parameters())}")
    print(f"Selected rank: {compressed.rank}")
    print()


def main():
    """
    Run all examples
    """
    print("Calabi-Yau Compression Library - Basic Usage Examples")
    print("=" * 60)
    print()
    
    example_single_layer_compression()
    example_model_compression()
    example_custom_compression()
    
    print("All examples completed successfully!")
    print()
    print("For more advanced usage, see:")
    print("- examples/advanced_usage.py")
    print("- examples/transformer_compression.py")


if __name__ == "__main__":
    main()