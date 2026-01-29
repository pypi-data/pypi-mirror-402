"""
Calabi - Geometric Neural Network Compression Library

A novel approach to LLM compression using principles from String Theory 
and Algebraic Geometry, specifically Calabi-Yau manifolds.

This package provides an efficient implementation of Calabi-Yau manifold-based
compression for neural networks, enabling significant parameter reduction while
preserving model accuracy.

Usage:
    >>> from calabi import OptimizedCalabiYauLinear
    >>> import torch.nn as nn
    >>> 
    >>> # Replace a standard linear layer with a compressed one
    >>> original_layer = nn.Linear(1024, 1024)
    >>> compressed_layer = OptimizedCalabiYauLinear(
    ...     original_linear=original_layer,
    ...     compression_ratio=0.5  # 50% compression
    ... )
"""

__version__ = "1.0.0"
__author__ = "Calabi Team"
__license__ = "MIT"
__maintainer__ = "Calabi Team"
__email__ = "info@example.com"
__status__ = "Development"

# Re-export the main classes from the internal package
from calabi_yau_compression import OptimizedCalabiYauLinear
from calabi_yau_compression.utils import OptimizedCYModelUtils

# Import transformers support
from .transformers_support import (
    replace_transformer_linear_layers,
    compress_bert_model,
    compress_gpt_model,
    create_conversion_utility,
)

# Import Hugging Face integration
from .hf_integration import (
    compress_hf_model,
    save_compressed_model,
    load_compressed_model,
    create_model_converter,
)

__all__ = [
    'OptimizedCalabiYauLinear', 
    'OptimizedCYModelUtils',
    'replace_transformer_linear_layers',
    'compress_bert_model',
    'compress_gpt_model',
    'create_conversion_utility',
    'compress_hf_model',
    'save_compressed_model',
    'load_compressed_model',
    'create_model_converter'
]