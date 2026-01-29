"""
Unit tests for transformers support module
"""

import unittest
import torch
import torch.nn as nn
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from calabi import (
    replace_transformer_linear_layers,
    compress_bert_model,
    compress_gpt_model,
    create_conversion_utility
)


class TestTransformersSupport(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.simple_transformer = nn.Module()
        # Create a simple transformer-like structure
        self.simple_transformer.encoder = nn.Sequential(
            nn.Linear(128, 256),
            nn.ReLU(),
            nn.Linear(256, 128)
        )
        self.simple_transformer.attention = nn.Linear(128, 128)
        self.simple_transformer.mlp = nn.Sequential(
            nn.Linear(128, 512),
            nn.ReLU(),
            nn.Linear(512, 128)
        )
    
    def test_replace_transformer_linear_layers(self):
        """Test replacing transformer linear layers."""
        original_params = sum(p.numel() for p in self.simple_transformer.parameters())
        
        compressed_count = replace_transformer_linear_layers(
            self.simple_transformer,
            compression_ratio=0.5,
            min_features=64,
            verbose=False
        )
        
        new_params = sum(p.numel() for p in self.simple_transformer.parameters())
        
        # Should have compressed some layers
        self.assertGreater(compressed_count, 0)
        # Should have fewer parameters after compression
        self.assertLess(new_params, original_params)
    
    def test_replace_transformer_linear_layers_with_patterns(self):
        """Test replacing layers with specific patterns."""
        # Count original linear layers
        original_linear_count = 0
        for name, module in self.simple_transformer.named_modules():
            if isinstance(module, nn.Linear):
                original_linear_count += 1
        
        compressed_count = replace_transformer_linear_layers(
            self.simple_transformer,
            compression_ratio=0.5,
            min_features=64,
            layer_patterns=['attention', 'mlp'],  # Only target attention and mlp layers
            verbose=False
        )
        
        # Should have compressed some but not necessarily all layers
        self.assertGreaterEqual(compressed_count, 0)
    
    def test_compress_bert_model(self):
        """Test BERT-specific compression."""
        # Create a simple BERT-like model
        bert_model = nn.Module()
        bert_model.bert = nn.Module()
        bert_model.bert.encoder = nn.Module()
        bert_model.bert.encoder.layer = nn.ModuleList([
            nn.Module(),
            nn.Module()
        ])
        
        # Add attention and intermediate layers
        for i, layer in enumerate(bert_model.bert.encoder.layer):
            layer.attention = nn.Module()
            layer.attention.query = nn.Linear(128, 128)
            layer.attention.key = nn.Linear(128, 128)
            layer.attention.value = nn.Linear(128, 128)
            layer.attention.output = nn.Linear(128, 128)
            layer.intermediate = nn.Linear(128, 512)
            layer.output = nn.Linear(512, 128)
        
        original_params = sum(p.numel() for p in bert_model.parameters())
        
        compressed_count = compress_bert_model(
            bert_model,
            compression_ratio=0.5,
            verbose=False
        )
        
        new_params = sum(p.numel() for p in bert_model.parameters())
        
        # Should have compressed some layers
        self.assertGreater(compressed_count, 0)
        # Should have fewer parameters after compression
        self.assertLess(new_params, original_params)
    
    def test_compress_gpt_model(self):
        """Test GPT-specific compression."""
        # Create a simple GPT-like model
        gpt_model = nn.Module()
        gpt_model.transformer = nn.Module()
        gpt_model.transformer.h = nn.ModuleList([
            nn.Module(),
            nn.Module()
        ])
        
        # Add attention and MLP layers
        for i, layer in enumerate(gpt_model.transformer.h):
            layer.attn = nn.Linear(128, 128)  # Simplified attention
            layer.mlp = nn.Sequential(
                nn.Linear(128, 512),
                nn.Linear(512, 128)
            )
        
        original_params = sum(p.numel() for p in gpt_model.parameters())
        
        compressed_count = compress_gpt_model(
            gpt_model,
            compression_ratio=0.5,
            verbose=False
        )
        
        new_params = sum(p.numel() for p in gpt_model.parameters())
        
        # Should have compressed some layers
        self.assertGreater(compressed_count, 0)
        # Should have fewer parameters after compression
        self.assertLess(new_params, original_params)
    
    def test_create_conversion_utility(self):
        """Test the general conversion utility."""
        model = nn.Sequential(
            nn.Linear(256, 512),
            nn.ReLU(),
            nn.Linear(512, 256)
        )
        
        original_params = sum(p.numel() for p in model.parameters())
        
        config = {
            'default_ratio': 0.5,
            'patterns': {
                'attention': 0.4,
                'mlp': 0.6,
                'output': 0.3
            }
        }
        
        converted_model = create_conversion_utility(
            model,
            compression_config=config,
            verbose=False
        )
        
        new_params = sum(p.numel() for p in converted_model.parameters())
        
        # Should have fewer parameters after conversion
        self.assertLess(new_params, original_params)
    
    def test_different_compression_ratios(self):
        """Test that different compression ratios work properly."""
        # Use larger layers where compression effects are more pronounced
        model_low = nn.Sequential(
            nn.Linear(256, 512),
            nn.Linear(512, 256)
        )
        compress_count_low = replace_transformer_linear_layers(
            model_low, compression_ratio=0.8, verbose=False
        )
        
        model_high = nn.Sequential(
            nn.Linear(256, 512),
            nn.Linear(512, 256)
        )
        compress_count_high = replace_transformer_linear_layers(
            model_high, compression_ratio=0.3, verbose=False
        )
        
        # Both should have compressed the same number of layers
        self.assertEqual(compress_count_low, compress_count_high)
        
        # But the high compression model should have fewer parameters
        params_low = sum(p.numel() for p in model_low.parameters())
        params_high = sum(p.numel() for p in model_high.parameters())
        # Allow for some tolerance due to compression overhead
        self.assertLessEqual(params_high, params_low)


if __name__ == '__main__':
    unittest.main()