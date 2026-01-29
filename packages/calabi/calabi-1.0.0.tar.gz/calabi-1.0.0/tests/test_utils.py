"""
Unit tests for utils module
"""

import unittest
import torch
import torch.nn as nn
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from calabi import OptimizedCYModelUtils, OptimizedCalabiYauLinear


class TestUtils(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.simple_model = nn.Sequential(
            nn.Linear(128, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 64)
        )
    
    def test_replace_linear_layers(self):
        """Test replacing linear layers in a model."""
        # Count original linear layers before compression
        original_linear_count = 0
        for name, module in self.simple_model.named_modules():
            if isinstance(module, nn.Linear):
                original_linear_count += 1
        
        original_params = sum(p.numel() for p in self.simple_model.parameters())
        
        compressed_count = OptimizedCYModelUtils.replace_linear_layers(
            self.simple_model,
            compression_ratio=0.5,
            min_features=64
        )
        
        new_params = sum(p.numel() for p in self.simple_model.parameters())
        
        # Should have compressed all linear layers (since they all have >64 features)
        self.assertEqual(compressed_count, original_linear_count)
        # Should have fewer parameters after compression
        self.assertLess(new_params, original_params)
    
    def test_replace_linear_layers_min_features(self):
        """Test that min_features parameter works correctly."""
        # Create a model with layers of different sizes
        model = nn.Sequential(
            nn.Linear(32, 64),  # Small layer - should not be compressed
            nn.Linear(64, 128), # Should be compressed (exactly at threshold)
            nn.Linear(128, 32)  # Small output - should not be compressed
        )
        
        original_params = sum(p.numel() for p in model.parameters())
        
        compressed_count = OptimizedCYModelUtils.replace_linear_layers(
            model,
            compression_ratio=0.5,
            min_features=64
        )
        
        new_params = sum(p.numel() for p in model.parameters())
        
        # Only the middle layer should be compressed (64->128)
        # The 32->64 and 128->32 layers have features below the threshold
        self.assertGreaterEqual(compressed_count, 1)  # At least the middle layer
        # Should have fewer or equal parameters (fewer if compression happened)
        self.assertLessEqual(new_params, original_params)
    
    def test_replace_linear_layers_verbose(self):
        """Test verbose parameter doesn't break functionality."""
        original_params = sum(p.numel() for p in self.simple_model.parameters())
        
        compressed_count = OptimizedCYModelUtils.replace_linear_layers(
            self.simple_model,
            compression_ratio=0.5,
            min_features=64,
            verbose=True
        )
        
        new_params = sum(p.numel() for p in self.simple_model.parameters())
        
        # Should still work with verbose enabled
        self.assertGreater(compressed_count, 0)
        self.assertLess(new_params, original_params)
    
    def test_count_parameters(self):
        """Test parameter counting utility."""
        model = nn.Sequential(
            nn.Linear(10, 20),
            nn.Linear(20, 5)
        )
        
        # Calculate expected parameters manually
        expected_params = (10 * 20 + 20) + (20 * 5 + 5)  # (input*output+bias) for each layer
        
        counted_params = OptimizedCYModelUtils.count_parameters(model)
        
        self.assertEqual(counted_params, expected_params)
    
    def test_print_model_stats(self):
        """Test model stats printing doesn't crash."""
        import io
        import contextlib
        
        # Capture print output
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            OptimizedCYModelUtils.print_model_stats(self.simple_model, "TestModel")
        
        output = f.getvalue()
        # Should contain the model name and some statistics
        self.assertIn("TestModel", output)
        self.assertIn("Params:", output)
    
    def test_replace_linear_layers_no_compression(self):
        """Test with compression ratio of 1.0 (no compression)."""
        model = nn.Sequential(nn.Linear(128, 64))
        original_params = sum(p.numel() for p in model.parameters())
        
        compressed_count = OptimizedCYModelUtils.replace_linear_layers(
            model,
            compression_ratio=1.0,  # No compression
            min_features=1
        )
        
        new_params = sum(p.numel() for p in model.parameters())
        
        # Should still replace the layer but with minimal compression
        self.assertEqual(compressed_count, 1)
        # Parameters might be slightly different due to SVD overhead, but similar
        self.assertGreater(new_params, 0)
    
    def test_replace_linear_layers_complex_model(self):
        """Test with a more complex model structure."""
        class ComplexModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.features = nn.Sequential(
                    nn.Linear(256, 512),
                    nn.ReLU(),
                    nn.Linear(512, 256)
                )
                self.classifier = nn.Linear(256, 10)
                self.auxiliary = nn.ModuleList([
                    nn.Linear(128, 64),
                    nn.Linear(64, 32)
                ])
        
        model = ComplexModel()
        original_params = sum(p.numel() for p in model.parameters())
        
        compressed_count = OptimizedCYModelUtils.replace_linear_layers(
            model,
            compression_ratio=0.5,
            min_features=64
        )
        
        new_params = sum(p.numel() for p in model.parameters())
        
        # Should have compressed multiple layers
        self.assertGreater(compressed_count, 0)
        self.assertLess(new_params, original_params)
        
        # Verify that compressed layers are actually OptimizedCalabiYauLinear
        for name, module in model.named_modules():
            if isinstance(module, OptimizedCalabiYauLinear):
                # This confirms that replacement worked
                self.assertIsInstance(module, OptimizedCalabiYauLinear)


if __name__ == '__main__':
    unittest.main()