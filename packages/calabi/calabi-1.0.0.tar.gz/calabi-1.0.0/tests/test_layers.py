"""
Unit tests for Calabi-Yau compression layers
"""

import unittest
import torch
import torch.nn as nn
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from calabi import OptimizedCalabiYauLinear


class TestOptimizedCalabiYauLinear(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.input_size = 128
        self.output_size = 64
        self.original_layer = nn.Linear(self.input_size, self.output_size)
        self.compression_ratio = 0.5
    
    def test_initialization(self):
        """Test initialization of OptimizedCalabiYauLinear."""
        compressed_layer = OptimizedCalabiYauLinear(
            original_linear=self.original_layer,
            compression_ratio=self.compression_ratio
        )
        
        self.assertIsInstance(compressed_layer, OptimizedCalabiYauLinear)
        self.assertEqual(compressed_layer.in_features, self.input_size)
        self.assertEqual(compressed_layer.out_features, self.output_size)
        # Check that rank is reduced according to compression ratio
        expected_rank = int(self.output_size * self.compression_ratio)
        self.assertLessEqual(compressed_layer.rank, expected_rank)
    
    def test_forward_pass_shape(self):
        """Test that forward pass produces correct output shape."""
        compressed_layer = OptimizedCalabiYauLinear(
            original_linear=self.original_layer,
            compression_ratio=self.compression_ratio
        )
        
        x = torch.randn(32, self.input_size)
        output = compressed_layer(x)
        
        self.assertEqual(output.shape, (32, self.output_size))
    
    def test_compression_ratio_effect(self):
        """Test that different compression ratios produce different ranks."""
        layer_low_comp = OptimizedCalabiYauLinear(
            original_linear=self.original_layer,
            compression_ratio=0.3
        )
        
        layer_high_comp = OptimizedCalabiYauLinear(
            original_linear=self.original_layer,
            compression_ratio=0.8
        )
        
        self.assertLess(layer_low_comp.rank, layer_high_comp.rank)
        self.assertGreater(layer_low_comp.rank, 0)
        self.assertGreater(layer_high_comp.rank, 0)
    
    def test_energy_threshold(self):
        """Test compression using energy threshold instead of ratio."""
        compressed_layer = OptimizedCalabiYauLinear(
            original_linear=self.original_layer,
            energy_threshold=0.90
        )
        
        self.assertIsInstance(compressed_layer, OptimizedCalabiYauLinear)
        self.assertGreater(compressed_layer.rank, 0)
        self.assertLessEqual(compressed_layer.rank, self.output_size)
    
    def test_gradient_flow(self):
        """Test that gradients flow properly through compressed layer."""
        compressed_layer = OptimizedCalabiYauLinear(
            original_linear=self.original_layer,
            compression_ratio=self.compression_ratio
        )
        
        x = torch.randn(16, self.input_size, requires_grad=True)
        output = compressed_layer(x)
        loss = output.sum()
        loss.backward()
        
        # Check that gradients exist
        self.assertIsNotNone(x.grad)
        self.assertTrue(torch.all(torch.isfinite(x.grad)))
    
    def test_error_correction_exists(self):
        """Test that error correction parameters exist and are properly initialized."""
        compressed_layer = OptimizedCalabiYauLinear(
            original_linear=self.original_layer,
            compression_ratio=self.compression_ratio
        )
        
        x = torch.randn(16, self.input_size)
        output = compressed_layer(x)
        
        # Check that error correction parameters exist
        self.assertTrue(hasattr(compressed_layer, 'error_U'))
        self.assertTrue(hasattr(compressed_layer, 'error_S'))
        self.assertTrue(hasattr(compressed_layer, 'error_V'))
        
        # Check that output is finite (no NaN or Inf)
        self.assertTrue(torch.all(torch.isfinite(output)))


if __name__ == '__main__':
    unittest.main()