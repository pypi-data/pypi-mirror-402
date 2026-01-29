"""
Transformers compatibility module for Calabi compression library.

This module provides utilities to compress popular transformer models
from Hugging Face Transformers library.
"""

import torch
import torch.nn as nn
from typing import Union, Dict, Any, Optional
from . import OptimizedCalabiYauLinear, OptimizedCYModelUtils


def replace_transformer_linear_layers(
    model: nn.Module,
    compression_ratio: float = 0.5,
    min_features: int = 128,
    layer_patterns: Optional[list] = None,
    verbose: bool = True
) -> int:
    """
    Replace linear layers in transformer models with Calabi compressed layers.
    
    Args:
        model: The transformer model to compress
        compression_ratio: Ratio of parameters to retain (0.0 to 1.0)
        min_features: Minimum number of features for a layer to be compressed
        layer_patterns: Specific layer name patterns to target (e.g., ['attn', 'mlp', 'ffn'])
        verbose: Whether to print compression progress
    
    Returns:
        Number of layers compressed
    """
    if layer_patterns is None:
        # Default patterns for common transformer layers
        layer_patterns = [
            'attn', 'attention', 'self_attn', 
            'mlp', 'ffn', 'feed_forward',
            'dense', 'linear'
        ]
    
    compressed_count = 0
    
    for name, module in model.named_modules():
        # Check if this is a linear layer and matches our patterns
        if (isinstance(module, nn.Linear) and 
            any(pattern.lower() in name.lower() for pattern in layer_patterns) and
            module.in_features >= min_features and 
            module.out_features >= min_features):
            
            # Skip tied embeddings if they exist
            tied = False
            if hasattr(model, "get_input_embeddings") and hasattr(model, "lm_head"):
                emb = model.get_input_embeddings()
                if (hasattr(emb, "weight") and 
                    hasattr(module, "weight") and 
                    emb.weight.data_ptr() == module.weight.data_ptr()):
                    tied = True
            
            if tied:
                if verbose:
                    print(f"Skipping tied embedding layer: {name}")
                continue
            
            try:
                if verbose:
                    print(f"Compressing {name}: {module.in_features}x{module.out_features} "
                          f"with ratio {compression_ratio}")
                
                # Replace with compressed layer
                compressed_layer = OptimizedCalabiYauLinear(
                    original_linear=module,
                    compression_ratio=compression_ratio
                )
                
                # Find parent module and replace the child
                name_parts = name.split('.')
                parent = model
                for part in name_parts[:-1]:
                    parent = getattr(parent, part)
                setattr(parent, name_parts[-1], compressed_layer)
                
                compressed_count += 1
                
            except Exception as e:
                if verbose:
                    print(f"Failed to compress {name}: {e}")
    
    return compressed_count


def compress_bert_model(
    bert_model: nn.Module,
    compression_ratio: float = 0.5,
    attention_compression_ratio: Optional[float] = None,
    mlp_compression_ratio: Optional[float] = None,
    verbose: bool = True
) -> int:
    """
    Compress a BERT-like model with specialized handling for attention and MLP components.
    
    Args:
        bert_model: The BERT model to compress
        compression_ratio: Default compression ratio for all layers
        attention_compression_ratio: Specific ratio for attention layers (optional)
        mlp_compression_ratio: Specific ratio for MLP/FFN layers (optional)
        verbose: Whether to print compression progress
    
    Returns:
        Number of layers compressed
    """
    total_compressed = 0
    
    # Handle attention layers specifically
    if attention_compression_ratio is None:
        attention_compression_ratio = compression_ratio
    
    # Compress attention-related linear layers
    for name, module in bert_model.named_modules():
        if isinstance(module, nn.Linear):
            if ('attention' in name.lower() or 'attn' in name.lower() or 
                'query' in name.lower() or 'key' in name.lower() or 
                'value' in name.lower() or 'output' in name.lower()):
                
                if verbose:
                    print(f"Compressing attention layer {name} with ratio {attention_compression_ratio}")
                
                try:
                    compressed_layer = OptimizedCalabiYauLinear(
                        original_linear=module,
                        compression_ratio=attention_compression_ratio
                    )
                    
                    name_parts = name.split('.')
                    parent = bert_model
                    for part in name_parts[:-1]:
                        parent = getattr(parent, part)
                    setattr(parent, name_parts[-1], compressed_layer)
                    
                    total_compressed += 1
                except Exception as e:
                    if verbose:
                        print(f"Failed to compress attention layer {name}: {e}")
    
    # Handle MLP/FFN layers specifically
    if mlp_compression_ratio is None:
        mlp_compression_ratio = compression_ratio
    
    for name, module in bert_model.named_modules():
        if isinstance(module, nn.Linear):
            if ('intermediate' in name.lower() or 'output.dense' in name.lower() or
                'ffn' in name.lower() or 'mlp' in name.lower()):
                
                if verbose:
                    print(f"Compressing MLP layer {name} with ratio {mlp_compression_ratio}")
                
                try:
                    compressed_layer = OptimizedCalabiYauLinear(
                        original_linear=module,
                        compression_ratio=mlp_compression_ratio
                    )
                    
                    name_parts = name.split('.')
                    parent = bert_model
                    for part in name_parts[:-1]:
                        parent = getattr(parent, part)
                    setattr(parent, name_parts[-1], compressed_layer)
                    
                    total_compressed += 1
                except Exception as e:
                    if verbose:
                        print(f"Failed to compress MLP layer {name}: {e}")
    
    return total_compressed


def compress_gpt_model(
    gpt_model: nn.Module,
    compression_ratio: float = 0.5,
    attention_compression_ratio: Optional[float] = None,
    mlp_compression_ratio: Optional[float] = None,
    verbose: bool = True
) -> int:
    """
    Compress a GPT-like model with specialized handling for attention and MLP components.
    
    Args:
        gpt_model: The GPT model to compress
        compression_ratio: Default compression ratio for all layers
        attention_compression_ratio: Specific ratio for attention layers (optional)
        mlp_compression_ratio: Specific ratio for MLP/FFN layers (optional)
        verbose: Whether to print compression progress
    
    Returns:
        Number of layers compressed
    """
    total_compressed = 0
    
    if attention_compression_ratio is None:
        attention_compression_ratio = compression_ratio
    
    if mlp_compression_ratio is None:
        mlp_compression_ratio = compression_ratio
    
    for name, module in gpt_model.named_modules():
        if isinstance(module, nn.Linear):
            # Attention layers in GPT typically have 'c_attn' or combinations of q,k,v in one layer
            # Or separate 'attn' components
            if ('attn' in name.lower() or 'attention' in name.lower() or 
                'c_attn' in name.lower() or 'c_proj' in name.lower()):
                
                compression_ratio_use = attention_compression_ratio
                if verbose:
                    print(f"Compressing GPT attention layer {name} with ratio {compression_ratio_use}")
                
                try:
                    compressed_layer = OptimizedCalabiYauLinear(
                        original_linear=module,
                        compression_ratio=compression_ratio_use
                    )
                    
                    name_parts = name.split('.')
                    parent = gpt_model
                    for part in name_parts[:-1]:
                        parent = getattr(parent, part)
                    setattr(parent, name_parts[-1], compressed_layer)
                    
                    total_compressed += 1
                except Exception as e:
                    if verbose:
                        print(f"Failed to compress attention layer {name}: {e}")
            
            # MLP layers in GPT
            elif ('mlp' in name.lower() or 'mlp.c_fc' in name.lower() or 
                  'mlp.c_proj' in name.lower() or 'ffn' in name.lower()):
                
                compression_ratio_use = mlp_compression_ratio
                if verbose:
                    print(f"Compressing GPT MLP layer {name} with ratio {compression_ratio_use}")
                
                try:
                    compressed_layer = OptimizedCalabiYauLinear(
                        original_linear=module,
                        compression_ratio=compression_ratio_use
                    )
                    
                    name_parts = name.split('.')
                    parent = gpt_model
                    for part in name_parts[:-1]:
                        parent = getattr(parent, part)
                    setattr(parent, name_parts[-1], compressed_layer)
                    
                    total_compressed += 1
                except Exception as e:
                    if verbose:
                        print(f"Failed to compress MLP layer {name}: {e}")
    
    return total_compressed


def create_conversion_utility(
    model: nn.Module,
    compression_config: Dict[str, Any],
    verbose: bool = True
) -> nn.Module:
    """
    Create a utility function to convert models based on a configuration.
    
    Args:
        model: The model to convert
        compression_config: Configuration dictionary specifying compression settings
        verbose: Whether to print conversion progress
    
    Example config:
    {
        'default_ratio': 0.5,
        'patterns': {
            'attention': 0.4,  # More aggressive for attention
            'mlp': 0.6,        # Less aggressive for MLP
            'output': 0.3      # Very aggressive for output layers
        }
    }
    """
    default_ratio = compression_config.get('default_ratio', 0.5)
    patterns = compression_config.get('patterns', {})
    
    compressed_count = 0
    
    for name, module in model.named_modules():
        if isinstance(module, nn.Linear):
            # Determine compression ratio based on layer name
            compression_ratio = default_ratio
            
            for pattern, ratio in patterns.items():
                if pattern.lower() in name.lower():
                    compression_ratio = ratio
                    break
            
            if verbose:
                print(f"Compressing {name} with ratio {compression_ratio}")
            
            try:
                compressed_layer = OptimizedCalabiYauLinear(
                    original_linear=module,
                    compression_ratio=compression_ratio
                )
                
                name_parts = name.split('.')
                parent = model
                for part in name_parts[:-1]:
                    parent = getattr(parent, part)
                setattr(parent, name_parts[-1], compressed_layer)
                
                compressed_count += 1
            except Exception as e:
                if verbose:
                    print(f"Failed to compress {name}: {e}")
    
    return model


# Update the main __init__.py to include these functions
def _extend_init():
    """Extend the main module with transformer support functions."""
    import sys
    if 'calabi' in sys.modules:
        calabi_module = sys.modules['calabi']
        calabi_module.replace_transformer_linear_layers = replace_transformer_linear_layers
        calabi_module.compress_bert_model = compress_bert_model
        calabi_module.compress_gpt_model = compress_gpt_model
        calabi_module.create_conversion_utility = create_conversion_utility


# Call this function to extend the main module
_extend_init()


__all__ = [
    'replace_transformer_linear_layers',
    'compress_bert_model', 
    'compress_gpt_model',
    'create_conversion_utility'
]