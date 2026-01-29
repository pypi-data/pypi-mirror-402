"""
Calabi-Yau LLM Compression Library

A novel approach to Large Language Model compression using principles from String Theory 
and Algebraic Geometry, specifically Calabi-Yau manifolds.

This library provides an efficient implementation of Calabi-Yau manifold-based
compression for neural networks, enabling significant parameter reduction while
preserving model accuracy.

Usage:
    >>> from calabi import OptimizedCalabiYauLinear  # Public import interface
    >>> import torch.nn as nn
    >>> 
    >>> # Replace a standard linear layer with a compressed one
    >>> original_layer = nn.Linear(1024, 1024)
    >>> compressed_layer = OptimizedCalabiYauLinear(
    ...     original_linear=original_layer,
    ...     compression_ratio=0.5  # 50% compression
    ... )
    >>> 
    >>> # Note: Although internal package is named 'calabi_yau_compression',
    >>> # the public import interface is 'calabi'
"""

__version__ = "1.0.0"
__author__ = "Calabi-Yau Compression Team"
__license__ = "MIT"
__maintainer__ = "Calabi-Yau Compression Team"
__email__ = "info@example.com"
__status__ = "Development"

from . import layers, utils
from .layers import OptimizedCalabiYauLinear
from .utils import OptimizedCYModelUtils

__all__ = ['OptimizedCalabiYauLinear', 'OptimizedCYModelUtils']

del layers, utils  # Clean up namespace after imports