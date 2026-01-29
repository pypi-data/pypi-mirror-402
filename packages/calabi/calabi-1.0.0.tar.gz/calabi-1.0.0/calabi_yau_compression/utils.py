import torch
import torch.nn as nn


class OptimizedCYModelUtils:
    """
    Utility class for model-level compression operations.
    
    This class provides utility functions to compress entire models
    by replacing linear layers with their Calabi-Yau compressed equivalents.
    """
    
    @staticmethod
    def replace_linear_layers(model, compression_ratio=0.5, min_features=128, verbose=True):
        """Optimized replacement of linear layers in the entire model hierarchy"""
        replaced_count = 0
        
        # Iterate through all named modules in the model, not just direct children
        for full_name, module in model.named_modules():
            # Only process direct children of parent modules to avoid replacing nested parts
            # of already replaced modules
            if isinstance(module, nn.Linear):
                # Check if this is a direct child of the model or a submodule
                parent_name = "".join(full_name.split(".")[:-1])
                
                # Check feature size requirements
                if module.in_features < min_features or module.out_features < min_features:
                    continue
                    
                if verbose:
                    print(f"Replacing {full_name} ({module.in_features}x{module.out_features}) with compression ratio {compression_ratio}...")
                
                # Find the parent module and the attribute name to replace
                name_parts = full_name.split('.')
                parent = model
                for part in name_parts[:-1]:
                    parent = getattr(parent, part)
                
                # Replace with optimized version
                from .layers import OptimizedCalabiYauLinear
                compressed_layer = OptimizedCalabiYauLinear(
                    original_linear=module, 
                    compression_ratio=compression_ratio
                )
                setattr(parent, name_parts[-1], compressed_layer)
                replaced_count += 1
        
        return replaced_count


    @staticmethod
    def print_model_stats(model, name="Model"):
        """Prints size and parameter count."""
        params = sum(p.numel() for p in model.parameters())
        # Estimate size in MB (assuming float32)
        size_mb = params * 4 / (1024 * 1024)
        print(f"[{name}] Params: {params:,} | Size: {size_mb:.2f} MB")

    @staticmethod
    def count_parameters(model):
        """Counts total parameters."""
        return sum(p.numel() for p in model.parameters())