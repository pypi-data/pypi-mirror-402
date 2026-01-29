#!/usr/bin/env python3
"""
Comprehensive test suite for tensor operations in PyTorch CMake integration.
"""

import unittest
import torch
import numpy as np
import sys
import os

# Add the build directory to Python path if needed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'build'))

try:
    import pytorch_cmake_module as pcm
except ImportError as e:
    print(f"Error importing pytorch_cmake_module: {e}")
    print("Make sure the module is built and in the Python path")
    sys.exit(1)

class TestTensorOperations(unittest.TestCase):
    """Test basic tensor operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        torch.manual_seed(42)
        np.random.seed(42)
        pcm.set_random_seed(42)
    
    def test_add_tensors(self):
        """Test tensor addition."""
        a = torch.randn(3, 4, device=self.device)
        b = torch.randn(3, 4, device=self.device)
        
        # Test custom implementation
        result_custom = pcm.add_tensors(a, b)
        
        # Test against PyTorch
        result_pytorch = a + b
        
        self.assertTrue(torch.allclose(result_custom, result_pytorch, rtol=1e-5, atol=1e-6))
        self.assertEqual(result_custom.shape, result_pytorch.shape)
        self.assertEqual(result_custom.device, result_pytorch.device)
    
    def test_add_tensors_broadcasting(self):
        """Test tensor addition with broadcasting."""
        a = torch.randn(3, 4, device=self.device)
        b = torch.randn(4, device=self.device)
        
        result_custom = pcm.add_tensors(a, b)
        result_pytorch = a + b
        
        self.assertTrue(torch.allclose(result_custom, result_pytorch, rtol=1e-5, atol=1e-6))
    
    def test_matmul(self):
        """Test matrix multiplication."""
        a = torch.randn(3, 4, device=self.device)
        b = torch.randn(4, 5, device=self.device)
        
        result_custom = pcm.matmul(a, b)
        result_pytorch = torch.matmul(a, b)
        
        self.assertTrue(torch.allclose(result_custom, result_pytorch, rtol=1e-4, atol=1e-5))
        self.assertEqual(result_custom.shape, (3, 5))
    
    def test_matmul_batch(self):
        """Test batch matrix multiplication."""
        a = torch.randn(2, 3, 4, device=self.device)
        b = torch.randn(2, 4, 5, device=self.device)
        
        result_custom = pcm.matmul(a, b)
        result_pytorch = torch.matmul(a, b)
        
        self.assertTrue(torch.allclose(result_custom, result_pytorch, rtol=1e-4, atol=1e-5))
        self.assertEqual(result_custom.shape, (2, 3, 5))
    
    def test_relu(self):
        """Test ReLU activation."""
        x = torch.randn(5, 10, device=self.device)
        
        result_custom = pcm.relu(x)
        result_pytorch = torch.relu(x)
        
        self.assertTrue(torch.allclose(result_custom, result_pytorch, rtol=1e-6, atol=1e-7))
        
        # Test that negative values are zero
        negative_mask = x < 0
        self.assertTrue(torch.all(result_custom[negative_mask] == 0))
    
    def test_softmax(self):
        """Test softmax function."""
        x = torch.randn(5, 10, device=self.device)
        
        for dim in [-1, 0, 1]:
            with self.subTest(dim=dim):
                result_custom = pcm.softmax(x, dim=dim)
                result_pytorch = torch.softmax(x, dim=dim)
                
                self.assertTrue(torch.allclose(result_custom, result_pytorch, rtol=1e-5, atol=1e-6))
                
                # Test that probabilities sum to 1
                sum_result = torch.sum(result_custom, dim=dim)
                expected_sum = torch.ones_like(sum_result)
                self.assertTrue(torch.allclose(sum_result, expected_sum, rtol=1e-5, atol=1e-6))
    
    def test_reduce_sum(self):
        """Test reduction sum."""
        x = torch.randn(3, 4, 5, device=self.device)
        
        # Test different dimensions
        for dim in [None, 0, 1, 2, -1]:
            with self.subTest(dim=dim):
                result_custom = pcm.reduce_sum(x, dim=dim)
                result_pytorch = torch.sum(x, dim=dim) if dim is not None else torch.sum(x)
                
                self.assertTrue(torch.allclose(result_custom, result_pytorch, rtol=1e-5, atol=1e-6))
    
    def test_reduce_mean(self):
        """Test reduction mean."""
        x = torch.randn(3, 4, 5, device=self.device)
        
        # Test different dimensions
        for dim in [None, 0, 1, 2, -1]:
            with self.subTest(dim=dim):
                result_custom = pcm.reduce_mean(x, dim=dim)
                result_pytorch = torch.mean(x, dim=dim) if dim is not None else torch.mean(x)
                
                self.assertTrue(torch.allclose(result_custom, result_pytorch, rtol=1e-5, atol=1e-6))
    
    def test_cross_entropy_loss(self):
        """Test cross-entropy loss."""
        logits = torch.randn(5, 10, device=self.device)
        targets = torch.randint(0, 10, (5,), device=self.device)
        
        result_custom = pcm.cross_entropy_loss(logits, targets)
        result_pytorch = torch.nn.functional.cross_entropy(logits, targets)
        
        self.assertTrue(torch.allclose(result_custom, result_pytorch, rtol=1e-5, atol=1e-6))
    
    def test_mse_loss(self):
        """Test MSE loss."""
        pred = torch.randn(5, 3, device=self.device)
        target = torch.randn(5, 3, device=self.device)
        
        result_custom = pcm.mse_loss(pred, target)
        result_pytorch = torch.nn.functional.mse_loss(pred, target)
        
        self.assertTrue(torch.allclose(result_custom, result_pytorch, rtol=1e-5, atol=1e-6))
    
    def test_attention(self):
        """Test attention mechanism."""
        batch_size, seq_len, d_model = 2, 5, 8
        
        query = torch.randn(batch_size, seq_len, d_model, device=self.device)
        key = torch.randn(batch_size, seq_len, d_model, device=self.device)
        value = torch.randn(batch_size, seq_len, d_model, device=self.device)
        
        result = pcm.attention(query, key, value)
        
        self.assertEqual(result.shape, (batch_size, seq_len, d_model))
        self.assertEqual(result.device, query.device)
        
        # Test that output is finite
        self.assertTrue(torch.all(torch.isfinite(result)))

class TestCustomOperators(unittest.TestCase):
    """Test custom operators."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        torch.manual_seed(42)
        np.random.seed(42)
        pcm.set_random_seed(42)
    
    def test_gelu(self):
        """Test GELU activation."""
        x = torch.randn(5, 10, device=self.device)
        
        result_custom = pcm.gelu(x)
        result_pytorch = torch.nn.functional.gelu(x)
        
        self.assertTrue(torch.allclose(result_custom, result_pytorch, rtol=1e-4, atol=1e-5))
        self.assertEqual(result_custom.shape, x.shape)
    
    def test_swish(self):
        """Test Swish activation."""
        x = torch.randn(5, 10, device=self.device)
        beta = 1.5
        
        result_custom = pcm.swish(x, beta=beta)
        
        # Manual implementation for comparison
        result_manual = x * torch.sigmoid(beta * x)
        
        self.assertTrue(torch.allclose(result_custom, result_manual, rtol=1e-5, atol=1e-6))
        self.assertEqual(result_custom.shape, x.shape)
    
    def test_layer_norm(self):
        """Test layer normalization."""
        x = torch.randn(2, 3, 4, device=self.device)
        norm_shape = [4]
        weight = torch.ones(4, device=self.device)
        bias = torch.zeros(4, device=self.device)
        
        result_custom = pcm.layer_norm(x, norm_shape, weight, bias)
        
        # Compare with PyTorch LayerNorm
        ln = torch.nn.LayerNorm(4).to(self.device)
        ln.weight.data = weight
        ln.bias.data = bias
        result_pytorch = ln(x)
        
        self.assertTrue(torch.allclose(result_custom, result_pytorch, rtol=1e-4, atol=1e-5))
        self.assertEqual(result_custom.shape, x.shape)
    
    def test_dropout(self):
        """Test dropout."""
        x = torch.randn(100, 50, device=self.device)
        p = 0.5
        
        # Test training mode
        result_train = pcm.dropout(x, p=p, training=True)
        self.assertEqual(result_train.shape, x.shape)
        
        # Test that some elements are zero (with high probability)
        zero_mask = result_train == 0
        zero_ratio = torch.sum(zero_mask.float()) / zero_mask.numel()
        self.assertGreater(zero_ratio, 0.3)  # Should be around 0.5, but allow variance
        self.assertLess(zero_ratio, 0.7)
        
        # Test evaluation mode
        result_eval = pcm.dropout(x, p=p, training=False)
        self.assertTrue(torch.allclose(result_eval, x, rtol=1e-6, atol=1e-7))
    
    def test_positional_encoding(self):
        """Test positional encoding."""
        seq_len = 10
        d_model = 8
        
        pos_encoding = pcm.positional_encoding(seq_len, d_model, device=self.device)
        
        self.assertEqual(pos_encoding.shape, (seq_len, d_model))
        self.assertEqual(pos_encoding.device, self.device)
        
        # Test that encoding is finite
        self.assertTrue(torch.all(torch.isfinite(pos_encoding)))
        
        # Test that different positions have different encodings
        self.assertFalse(torch.allclose(pos_encoding[0], pos_encoding[1]))
    
    def test_multi_head_attention(self):
        """Test multi-head attention."""
        batch_size, seq_len, d_model = 2, 5, 8
        num_heads = 2
        
        query = torch.randn(batch_size, seq_len, d_model, device=self.device)
        key = torch.randn(batch_size, seq_len, d_model, device=self.device)
        value = torch.randn(batch_size, seq_len, d_model, device=self.device)
        
        attn_output, attn_weights = pcm.multi_head_attention(
            query, key, value, num_heads, dropout_p=0.0
        )
        
        self.assertEqual(attn_output.shape, (batch_size, seq_len, d_model))
        self.assertEqual(attn_weights.shape, (batch_size, num_heads, seq_len, seq_len))
        
        # Test that attention weights sum to 1
        weight_sums = torch.sum(attn_weights, dim=-1)
        expected_sums = torch.ones_like(weight_sums)
        self.assertTrue(torch.allclose(weight_sums, expected_sums, rtol=1e-5, atol=1e-6))
    
    def test_focal_loss(self):
        """Test focal loss."""
        logits = torch.randn(5, 10, device=self.device)
        targets = torch.randint(0, 10, (5,), device=self.device)
        alpha = 1.0
        gamma = 2.0
        
        result = pcm.focal_loss(logits, targets, alpha=alpha, gamma=gamma)
        
        self.assertTrue(torch.isfinite(result))
        self.assertGreater(result.item(), 0)  # Loss should be positive
    
    def test_label_smoothing_loss(self):
        """Test label smoothing loss."""
        logits = torch.randn(5, 10, device=self.device)
        targets = torch.randint(0, 10, (5,), device=self.device)
        smoothing = 0.1
        
        result = pcm.label_smoothing_loss(logits, targets, smoothing=smoothing)
        
        self.assertTrue(torch.isfinite(result))
        self.assertGreater(result.item(), 0)  # Loss should be positive
        
        # Compare with regular cross-entropy (should be different)
        ce_loss = pcm.cross_entropy_loss(logits, targets)
        self.assertNotEqual(result.item(), ce_loss.item())

class TestUtilities(unittest.TestCase):
    """Test utility functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    def test_cuda_availability(self):
        """Test CUDA availability functions."""
        cuda_available = pcm.is_cuda_available()
        pytorch_cuda_available = torch.cuda.is_available()
        
        self.assertEqual(cuda_available, pytorch_cuda_available)
        
        if cuda_available:
            device_count = pcm.get_cuda_device_count()
            pytorch_device_count = torch.cuda.device_count()
            self.assertEqual(device_count, pytorch_device_count)
            
            if device_count > 0:
                device_name = pcm.get_device_name(0)
                self.assertIsInstance(device_name, str)
                self.assertGreater(len(device_name), 0)
    
    def test_tensor_creation(self):
        """Test tensor creation utilities."""
        shape = [3, 4]
        
        tensor = pcm.create_tensor(shape, dtype=torch.float32, device='cpu', requires_grad=False)
        
        self.assertEqual(list(tensor.shape), shape)
        self.assertEqual(tensor.dtype, torch.float32)
        self.assertEqual(tensor.device, torch.device('cpu'))
        self.assertFalse(tensor.requires_grad)
    
    def test_random_tensor_creation(self):
        """Test random tensor creation."""
        shape = [2, 3]
        min_val = -1.0
        max_val = 1.0
        
        tensor = pcm.create_random_tensor(shape, min_val, max_val, device='cpu')
        
        self.assertEqual(list(tensor.shape), shape)
        self.assertGreaterEqual(torch.min(tensor).item(), min_val)
        self.assertLessEqual(torch.max(tensor).item(), max_val)
    
    def test_mathematical_utilities(self):
        """Test mathematical utility functions."""
        x = torch.randn(100)
        
        mean_custom = pcm.compute_mean(x)
        mean_pytorch = torch.mean(x).item()
        self.assertAlmostEqual(mean_custom, mean_pytorch, places=5)
        
        std_custom = pcm.compute_std(x)
        std_pytorch = torch.std(x).item()
        self.assertAlmostEqual(std_custom, std_pytorch, places=5)
        
        var_custom = pcm.compute_variance(x)
        var_pytorch = torch.var(x).item()
        self.assertAlmostEqual(var_custom, var_pytorch, places=5)
    
    def test_random_seed(self):
        """Test random seed setting."""
        # Set seed and generate tensor
        pcm.set_random_seed(42)
        tensor1 = torch.randn(5, 5)
        
        # Set same seed and generate tensor again
        pcm.set_random_seed(42)
        tensor2 = torch.randn(5, 5)
        
        # They should be the same
        self.assertTrue(torch.allclose(tensor1, tensor2))
    
    def test_benchmark_operation(self):
        """Test operation benchmarking."""
        def simple_operation():
            x = torch.randn(100, 100)
            y = torch.matmul(x, x)
        
        time_ms = pcm.benchmark_operation(simple_operation, num_runs=5)
        
        self.assertIsInstance(time_ms, float)
        self.assertGreater(time_ms, 0)

class TestGradients(unittest.TestCase):
    """Test gradient computation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        torch.manual_seed(42)
    
    def test_gelu_gradient(self):
        """Test GELU gradient computation."""
        x = torch.randn(5, 10, device=self.device, requires_grad=True)
        
        # Custom GELU
        y_custom = pcm.gelu(x)
        loss_custom = torch.sum(y_custom)
        loss_custom.backward()
        grad_custom = x.grad.clone()
        
        # Reset gradient
        x.grad.zero_()
        
        # PyTorch GELU
        y_pytorch = torch.nn.functional.gelu(x)
        loss_pytorch = torch.sum(y_pytorch)
        loss_pytorch.backward()
        grad_pytorch = x.grad.clone()
        
        # Compare gradients
        self.assertTrue(torch.allclose(grad_custom, grad_pytorch, rtol=1e-4, atol=1e-5))
    
    def test_layer_norm_gradient(self):
        """Test layer normalization gradient computation."""
        x = torch.randn(2, 3, 4, device=self.device, requires_grad=True)
        weight = torch.ones(4, device=self.device, requires_grad=True)
        bias = torch.zeros(4, device=self.device, requires_grad=True)
        
        # Custom layer norm
        y = pcm.layer_norm(x, [4], weight, bias)
        loss = torch.sum(y)
        loss.backward()
        
        # Check that gradients exist and are finite
        self.assertIsNotNone(x.grad)
        self.assertIsNotNone(weight.grad)
        self.assertIsNotNone(bias.grad)
        
        self.assertTrue(torch.all(torch.isfinite(x.grad)))
        self.assertTrue(torch.all(torch.isfinite(weight.grad)))
        self.assertTrue(torch.all(torch.isfinite(bias.grad)))

def run_tests():
    """Run all tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestTensorOperations,
        TestCustomOperators,
        TestUtilities,
        TestGradients
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    print("=== PyTorch CMake Integration - Test Suite ===")
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    print(f"Module version: {pcm.get_version()}")
    
    success = run_tests()
    
    if success:
        print("\n✅ All tests passed!")
        exit(0)
    else:
        print("\n❌ Some tests failed!")
        exit(1)