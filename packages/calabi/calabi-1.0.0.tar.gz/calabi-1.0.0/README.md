# Calabi LLM Compression

## Concept
This project explores a novel approach to Large Language Model (LLM) compression using principles from String Theory and Algebraic Geometry, specifically **Calabi-Yau Manifolds**.

Named after the Calabi-Yau manifolds, this library implements geometric compression techniques that map weight matrices of neural networks onto lower-dimensional manifolds, achieving high compression ratios while preserving the geometric structure of the information.

## Methodology
1.  **Real SVD Decomposition**: Decompose real-valued weight matrices using standard SVD instead of complex SVD for efficiency.
2.  **Manifold Projection**: Project weight matrices onto lower-rank Calabi-Yau sub-manifolds using **Singular Value Decomposition (SVD)**. This finds the optimal linear manifold describing the data.
3.  **Dimensionality Reduction**: Store only the principal components (U, S, V matrices) required to reconstruct the manifold state, plus a reconstruction bias for accuracy preservation.
4.  **Smart Rank Selection**: Use both energy thresholding and spectral gap detection to make better rank selection decisions.
5.  **Efficient Inference**: Perform inference directly in the compressed "manifold" space using low-rank multiplication with reconstruction bias compensation.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### 1. Run the compression demo

```bash
python main.py
```

### 2. Using the library in your own code

```python
import torch
import torch.nn as nn
from calabi import OptimizedCalabiYauLinear

# Create a standard linear layer
original_layer = nn.Linear(1024, 1024)

# Convert to Calabi Layer (Compression happens on init)
# compression_ratio=0.5 means we keep only top 50% of dimensions
compressed_layer = OptimizedCalabiYauLinear(
    original_linear=original_layer, 
    compression_ratio=0.5
)

# Run inference (Faster and less memory)
x = torch.randn(32, 1024)
output = compressed_layer(x)
```

### 3. Compressing Entire Models

```python
from calabi.utils import OptimizedCYModelUtils
import torch.nn as nn

# Create a model with linear layers
model = nn.Sequential(
    nn.Linear(1024, 2048),
    nn.ReLU(),
    nn.Linear(2048, 1024)
)

# Compress all Linear layers
compressed_count = OptimizedCYModelUtils.replace_linear_layers(
    model, 
    compression_ratio=0.5,
    min_features=128
)

print(f"Compressed {compressed_count} layers")
```

### 4. Hugging Face Transformers Integration

The library provides seamless integration with Hugging Face Transformers:

```python
from calabi import compress_hf_model

# Compress a pre-trained model directly
compressed_model = compress_hf_model(
    "bert-base-uncased",  # or any Hugging Face model
    compression_ratio=0.5,
    verbose=True
)
```

### 5. Advanced Usage

Check the `examples/` directory for more detailed usage patterns:
- `examples/basic_usage.py` - Basic layer and model compression
- `examples/advanced_usage.py` - Gradient checking, spectral analysis, and fine-tuning
- `examples/hf_compression_example.py` - Hugging Face integration examples

API reference is available in `API_REFERENCE.md`

## Files
*   `main.py`: Main entry point for the compression demo.
*   `setup.py`: Package setup file.
*   `requirements.txt`: Python package dependencies.
*   `calabi_yau_compression/`: Main package directory (note: despite the name, imports should use `calabi`):
    *   `__init__.py`: Package initialization
    *   `layers.py`: The `OptimizedCalabiYauLinear` module implementation
    *   `utils.py`: Utilities for recursive model patching

Note: Although the internal package directory is named `calabi_yau_compression`, the public import interface is `calabi`.

## Key Improvements

* **Enhanced Accuracy**: Added reconstruction bias compensation to minimize accuracy loss during compression
* **Smart Rank Selection**: Combined energy thresholding with spectral gap detection for better rank selection
* **Robust Error Handling**: Comprehensive error handling for SVD operations with CPU fallback
* **Numerical Stability**: Extensive checks throughout forward pass to prevent NaN/Inf values
* **Gradient Verification**: Built-in gradient flow verification for stable training
* **Memory Efficiency**: Optimized matrix operations to reduce memory footprint

## Why Calabi-Yau?
Standard quantization (e.g., INT4) acts on individual weights, often introducing "rounding noise." The Calabi-Yau approach treats the layer as a holistic geometric object. By preserving the principal components in the real domain with reconstruction bias, we maintain the "shape" of the transformation the layer performs, effectively denoising the signal while compressing it.
