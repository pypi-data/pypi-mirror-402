# Calabi-Yau Compression Library Examples

This directory contains examples demonstrating how to use the Calabi-Yau compression library in various scenarios.

## Available Examples

### 1. Basic Usage (`basic_usage.py`)
Demonstrates the fundamental usage of the library:
- Compressing individual layers
- Compressing entire models
- Custom compression settings

Run with: `python -m examples.basic_usage`

### 2. Advanced Usage (`advanced_usage.py`)
Shows advanced features and techniques:
- Gradient flow verification
- Spectral analysis
- Fine-tuning setup
- Error handling

Run with: `python -m examples.advanced_usage`

### 3. Hugging Face Transformers Integration (`hf_compression_example.py`)
Demonstrates integration with Hugging Face Transformers:
- Compressing pre-trained models
- Custom compression configurations
- Save/load workflows

Run with: `python -m examples.hf_compression_example`

## Quick Start

```python
# Install the library
pip install -r requirements.txt

# Import and use
from calabi_yau_compression import OptimizedCalabiYauLinear
import torch.nn as nn

# Compress a layer
original = nn.Linear(1024, 512)
compressed = OptimizedCalabiYauLinear(original, compression_ratio=0.5)

# Use the compressed layer like any other
x = torch.randn(32, 1024)
output = compressed(x)
```

## Running Examples

To run the examples from the project root:

```bash
# Basic usage
python -m examples.basic_usage

# Advanced usage  
python -m examples.advanced_usage
```

## API Reference

See `API_REFERENCE.md` for detailed documentation of all classes and methods.