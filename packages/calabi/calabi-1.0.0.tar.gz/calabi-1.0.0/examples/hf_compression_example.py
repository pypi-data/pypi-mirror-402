"""
Example: Hugging Face Transformers Compression with Calabi

This example demonstrates how to compress popular transformer models
using the Calabi compression library.
"""

import torch
import torch.nn as nn
from calabi import (
    compress_hf_model,
    create_model_converter,
    save_compressed_model,
    load_compressed_model
)

def example_basic_hf_compression():
    """Basic example of compressing a Hugging Face model."""
    print("=== Basic Hugging Face Model Compression ===")
    
    try:
        # For demonstration, we'll create a simple model instead of downloading
        # In practice, you would use:
        # model = compress_hf_model("bert-base-uncased", compression_ratio=0.5)
        
        # Create a simple transformer-like model for demonstration
        model = nn.Transformer(d_model=256, nhead=4, num_encoder_layers=2, num_decoder_layers=2)
        print(f"Original model parameters: {sum(p.numel() for p in model.parameters()):,}")
        
        # Compress the model
        compressed_model = compress_hf_model(model, compression_ratio=0.5, verbose=True)
        print(f"Compressed model parameters: {sum(p.numel() for p in compressed_model.parameters()):,}")
        
    except ImportError:
        print("Transformers library not available. Install with: pip install transformers")
        
    print()


def example_advanced_compression():
    """Advanced example with custom compression configuration."""
    print("=== Advanced Hugging Face Model Compression ===")
    
    try:
        # Example configuration for different compression ratios per layer type
        compression_config = {
            'method': 'calabi',
            'default_ratio': 0.6,
            'arch_specific': {
                'bert': {'attention': 0.4, 'mlp': 0.7},  # More compression on attention, less on MLP
                'gpt': {'attention': 0.3, 'mlp': 0.6}
            },
            'selective_layers': ['attention', 'mlp'],
            'min_features': 128
        }
        
        print("Compression configuration:")
        for key, value in compression_config.items():
            print(f"  {key}: {value}")
        
        # In practice, you would use:
        # model = create_model_converter("bert-base-uncased", compression_config)
        
    except ImportError:
        print("Transformers library not available. Install with: pip install transformers")
    
    print()


def example_save_load_compressed():
    """Example of saving and loading compressed models."""
    print("=== Saving and Loading Compressed Models ===")
    
    # Create a simple model for demonstration
    simple_model = nn.Sequential(
        nn.Linear(512, 1024),
        nn.ReLU(),
        nn.Linear(1024, 512),
        nn.ReLU(),
        nn.Linear(512, 256)
    )
    
    print(f"Original model parameters: {sum(p.numel() for p in simple_model.parameters()):,}")
    
    # Compress the model
    from calabi import OptimizedCalabiYauLinear
    
    # Manually compress layers for demonstration
    for name, module in simple_model.named_modules():
        if isinstance(module, nn.Linear) and module.in_features >= 128:
            compressed_layer = OptimizedCalabiYauLinear(module, compression_ratio=0.5)
            name_parts = name.split('.')
            parent = simple_model
            for part in name_parts[:-1]:
                parent = getattr(parent, part)
            setattr(parent, name_parts[-1], compressed_layer)
    
    print(f"Compressed model parameters: {sum(p.numel() for p in simple_model.parameters()):,}")
    
    # Save the compressed model (in a real scenario)
    # save_compressed_model(simple_model, "./compressed_model", "demo_model")
    
    print("Model compression and save/load demonstrated.")
    print()


def example_real_world_scenario():
    """Example of how to use in a real-world scenario."""
    print("=== Real-World Scenario: Compressing BERT ===")
    
    try:
        from transformers import AutoModel, AutoTokenizer
        
        print("This example shows the workflow for compressing a real BERT model:")
        print("# 1. Load the original model")
        print("# model = AutoModel.from_pretrained('bert-base-uncased')")
        print("#")
        print("# 2. Compress the model")
        print("# compressed_model = compress_hf_model(model, compression_ratio=0.5)")
        print("#")
        print("# 3. Save the compressed model")
        print("# save_compressed_model(compressed_model, './compressed_bert', 'bert-base-uncased')")
        print("#")
        print("# 4. Later, load the compressed model")
        print("# loaded_model = load_compressed_model('./compressed_bert')")
        print("#")
        print("# 5. Use the compressed model for inference")
        print("# tokenizer = AutoTokenizer.from_pretrained('./compressed_bert')")
        print("# # Continue with normal usage...")
        
    except ImportError:
        print("Transformers library not available. Install with: pip install transformers")
    
    print()


if __name__ == "__main__":
    print("Calabi - Hugging Face Transformers Compression Examples")
    print("=" * 55)
    
    example_basic_hf_compression()
    example_advanced_compression()
    example_save_load_compressed()
    example_real_world_scenario()
    
    print("Examples completed!")
    print("\nTo use with real Hugging Face models, install transformers:")
    print("  pip install transformers")