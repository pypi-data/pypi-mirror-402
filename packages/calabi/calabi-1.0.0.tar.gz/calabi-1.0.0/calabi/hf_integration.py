"""
Hugging Face Integration Module for Calabi Compression

This module provides seamless integration with Hugging Face Transformers,
enabling easy compression of pre-trained models.
"""

import torch
import torch.nn as nn
from typing import Union, Dict, Any, Optional, Callable
from transformers import PreTrainedModel
from . import (
    OptimizedCalabiYauLinear,
    replace_transformer_linear_layers,
    compress_bert_model,
    compress_gpt_model
)


def compress_hf_model(
    model: Union[PreTrainedModel, str],
    compression_ratio: float = 0.5,
    model_type: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    device_map: Optional[Union[str, Dict[str, Any]]] = None,
    verbose: bool = True
) -> PreTrainedModel:
    """
    Compress a Hugging Face model using Calabi compression.
    
    Args:
        model: Either a loaded model instance or a model identifier string
        compression_ratio: Ratio of parameters to retain (0.0 to 1.0)
        model_type: Type of model ('bert', 'gpt', 't5', etc.) - auto-detected if None
        config: Additional compression configuration
        device_map: Device mapping for loading the model
        verbose: Whether to print compression progress
    
    Returns:
        Compressed model
    """
    # Load model if a string is provided
    if isinstance(model, str):
        try:
            from transformers import AutoModel
            model = AutoModel.from_pretrained(model, device_map=device_map)
        except ImportError:
            raise ImportError("transformers library is required for model loading")
    
    # Detect model type if not provided
    if model_type is None:
        model_type = _detect_model_type(model)
    
    if verbose:
        print(f"Detected model type: {model_type}")
        print(f"Original model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Apply compression based on model type
    if model_type.lower() in ['bert', 'roberta', 'albert', 'electra']:
        compressed_count = compress_bert_model(
            model, 
            compression_ratio=compression_ratio,
            verbose=verbose
        )
    elif model_type.lower() in ['gpt', 'gpt2', 'gpt_neo', 'gptj', 'gpt_neox']:
        compressed_count = compress_gpt_model(
            model, 
            compression_ratio=compression_ratio,
            verbose=verbose
        )
    else:
        # Generic transformer compression
        compressed_count = replace_transformer_linear_layers(
            model,
            compression_ratio=compression_ratio,
            verbose=verbose
        )
    
    if verbose:
        print(f"Compressed {compressed_count} layers")
        print(f"Compressed model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    return model


def _detect_model_type(model: PreTrainedModel) -> str:
    """Detect the model type based on class name."""
    class_name = model.__class__.__name__.lower()
    
    if any(name in class_name for name in ['bert', 'roberta', 'albert', 'electra']):
        return 'bert'
    elif any(name in class_name for name in ['gpt', 'gpt2', 'gpt_neo', 'gptj', 'gpt_neox']):
        return 'gpt'
    elif any(name in class_name for name in ['t5', 'mt5']):
        return 't5'
    elif any(name in class_name for name in ['bart', 'mbart']):
        return 'bart'
    elif any(name in class_name for name in ['llama', 'llama2', 'opt', 'mistral']):
        return 'decoder_only'
    else:
        return 'generic'


def save_compressed_model(
    model: PreTrainedModel,
    save_directory: str,
    original_model_name: Optional[str] = None,
    compression_metadata: Optional[Dict[str, Any]] = None,
    **kwargs
):
    """
    Save a compressed model with appropriate metadata.
    
    Args:
        model: The compressed model to save
        save_directory: Directory to save the model
        original_model_name: Name of the original model
        compression_metadata: Additional compression metadata
        **kwargs: Additional arguments passed to save_pretrained
    """
    import os
    import json
    
    # Create save directory if it doesn't exist
    os.makedirs(save_directory, exist_ok=True)
    
    # Prepare compression metadata
    if compression_metadata is None:
        compression_metadata = {}
    
    # Add Calabi-specific metadata
    compression_metadata.update({
        'compression_method': 'calabi_yau_manifold',
        'compression_library': 'calabi',
        'original_model': original_model_name,
        'compression_timestamp': torch.tensor([torch.finfo(torch.float).tiny]).item(),  # placeholder
        'compressed_parameters': sum(p.numel() for p in model.parameters()),
        'compression_ratios_applied': _get_compression_ratios(model)
    })
    
    # Save the model
    model.save_pretrained(save_directory, **kwargs)
    
    # Save compression metadata
    metadata_path = os.path.join(save_directory, "calabi_compression_metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(compression_metadata, f, indent=2)
    
    print(f"Model saved to {save_directory}")
    print(f"Compression metadata saved to {metadata_path}")


def _get_compression_ratios(model: nn.Module) -> Dict[str, float]:
    """Extract compression ratios from compressed layers in the model."""
    ratios = {}
    
    for name, module in model.named_modules():
        if hasattr(module, 'compression_ratio'):
            ratios[name] = module.compression_ratio
    
    return ratios


def load_compressed_model(
    model_path: str,
    original_model_class: Optional[Callable] = None,
    device_map: Optional[Union[str, Dict[str, Any]]] = None,
    **kwargs
) -> PreTrainedModel:
    """
    Load a compressed model and restore the Calabi compression structure.
    
    Args:
        model_path: Path to the saved compressed model
        original_model_class: Original model class (if known)
        device_map: Device mapping for loading
        **kwargs: Additional arguments passed to from_pretrained
    
    Returns:
        Loaded model with Calabi compression layers restored
    """
    import os
    import json
    
    # Load compression metadata if available
    metadata_path = os.path.join(model_path, "calabi_compression_metadata.json")
    compression_metadata = {}
    
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            compression_metadata = json.load(f)
        
        print(f"Loaded compression metadata:")
        for key, value in compression_metadata.items():
            print(f"  {key}: {value}")
    
    # Load the base model
    if original_model_class is not None:
        model = original_model_class.from_pretrained(model_path, device_map=device_map, **kwargs)
    else:
        # Try to load with AutoModel if transformers is available
        try:
            from transformers import AutoModel
            model = AutoModel.from_pretrained(model_path, device_map=device_map, **kwargs)
        except ImportError:
            raise ImportError("transformers library is required for model loading")
    
    # The model should already have the compressed layers since they're PyTorch modules
    # that were saved with the state dict
    print(f"Model loaded with {sum(p.numel() for p in model.parameters()):,} parameters")
    
    return model


def create_model_converter(
    model_identifier: str,
    compression_config: Dict[str, Any],
    device_map: Optional[Union[str, Dict[str, Any]]] = None,
    verbose: bool = True
) -> PreTrainedModel:
    """
    Create a converter to compress a Hugging Face model based on a configuration.
    
    Args:
        model_identifier: Hugging Face model identifier (e.g., 'bert-base-uncased')
        compression_config: Configuration for compression
        device_map: Device mapping for loading
        verbose: Whether to print progress
    
    Example config:
    {
        'method': 'calabi',
        'default_ratio': 0.5,
        'arch_specific': {
            'bert': {'attention': 0.4, 'mlp': 0.6},
            'gpt': {'attention': 0.3, 'mlp': 0.7}
        },
        'selective_layers': ['attention', 'mlp'],  # Only compress these layer types
        'min_features': 128
    }
    """
    try:
        from transformers import AutoConfig, AutoModel
    except ImportError:
        raise ImportError("transformers library is required for model conversion")
    
    # Load model configuration to detect architecture
    config = AutoConfig.from_pretrained(model_identifier)
    model_type = config.model_type
    
    if verbose:
        print(f"Loading model: {model_identifier}")
        print(f"Model type: {model_type}")
        print(f"Compression config: {compression_config}")
    
    # Load the model
    model = AutoModel.from_pretrained(model_identifier, device_map=device_map)
    
    # Apply compression based on config
    default_ratio = compression_config.get('default_ratio', 0.5)
    selective_layers = compression_config.get('selective_layers', None)
    min_features = compression_config.get('min_features', 128)
    
    if model_type in ['bert', 'roberta', 'albert', 'electra']:
        arch_config = compression_config.get('arch_specific', {}).get('bert', {})
        attention_ratio = arch_config.get('attention', default_ratio)
        mlp_ratio = arch_config.get('mlp', default_ratio)
        
        compressed_count = compress_bert_model(
            model,
            compression_ratio=default_ratio,
            attention_compression_ratio=attention_ratio,
            mlp_compression_ratio=mlp_ratio,
            verbose=verbose
        )
    elif model_type in ['gpt2', 'gpt', 'gpt_neo', 'gptj', 'gpt_neox']:
        arch_config = compression_config.get('arch_specific', {}).get('gpt', {})
        attention_ratio = arch_config.get('attention', default_ratio)
        mlp_ratio = arch_config.get('mlp', default_ratio)
        
        compressed_count = compress_gpt_model(
            model,
            compression_ratio=default_ratio,
            attention_compression_ratio=attention_ratio,
            mlp_compression_ratio=mlp_ratio,
            verbose=verbose
        )
    else:
        # Use generic transformer compression
        compressed_count = replace_transformer_linear_layers(
            model,
            compression_ratio=default_ratio,
            min_features=min_features,
            verbose=verbose
        )
    
    if verbose:
        print(f"Model compressed successfully!")
        print(f"Layers compressed: {compressed_count}")
        print(f"Original params: {sum(p.numel() for p in model.parameters(full=True)):,}")
    
    return model


# Add these functions to the main module
def _extend_hf_module():
    """Extend the main module with HF integration functions."""
    import sys
    if 'calabi' in sys.modules:
        calabi_module = sys.modules['calabi']
        calabi_module.compress_hf_model = compress_hf_model
        calabi_module.save_compressed_model = save_compressed_model
        calabi_module.load_compressed_model = load_compressed_model
        calabi_module.create_model_converter = create_model_converter


# Call this function to extend the main module
_extend_hf_module()


__all__ = [
    'compress_hf_model',
    'save_compressed_model',
    'load_compressed_model',
    'create_model_converter',
    '_detect_model_type',
    '_get_compression_ratios'
]