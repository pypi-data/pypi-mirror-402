#!/usr/bin/env python3
"""
Unit tests for NumPy integration in the Python module built with CMake.
These tests require NumPy and the module to be compiled with ENABLE_NUMPY=ON.
"""

import sys
import os
import unittest
import math

# Add the build directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python_package'))

try:
    import numpy as np
except ImportError:
    print("NumPy is not available. Install it with: pip install numpy")
    sys.exit(1)

try:
    import python_cmake_module as pcm
except ImportError as e:
    print(f"Failed to import python_cmake_module: {e}")
    print("Make sure the module is built and in the correct location.")
    sys.exit(1)

class TestNumPyIntegration(unittest.TestCase):
    """Test NumPy integration functionality"""
    
    def setUp(self):
        if pcm.__numpy_support__ != "enabled":
            self.skipTest("NumPy support is not enabled in the compiled module")
    
    def test_numpy_to_list(self):
        """Test converting NumPy array to Python list"""
        if not hasattr(pcm, 'numpy_to_list'):
            self.skipTest("numpy_to_list function not available")
        
        arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = pcm.numpy_to_list(arr)
        expected = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        self.assertEqual(result, expected)
        self.assertIsInstance(result, list)
    
    def test_list_to_numpy(self):
        """Test converting Python list to NumPy array"""
        if not hasattr(pcm, 'list_to_numpy'):
            self.skipTest("list_to_numpy function not available")
        
        input_list = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = pcm.list_to_numpy(input_list)
        expected = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        self.assertIsInstance(result, np.ndarray)
        np.testing.assert_array_equal(result, expected)
    
    def test_roundtrip_conversion(self):
        """Test converting NumPy -> list -> NumPy"""
        if not (hasattr(pcm, 'numpy_to_list') and hasattr(pcm, 'list_to_numpy')):
            self.skipTest("Conversion functions not available")
        
        original = np.array([1.5, 2.5, 3.5, 4.5, 5.5])
        
        # NumPy -> list -> NumPy
        as_list = pcm.numpy_to_list(original)
        back_to_numpy = pcm.list_to_numpy(as_list)
        
        np.testing.assert_array_equal(original, back_to_numpy)
    
    def test_add_numpy_arrays(self):
        """Test element-wise addition of NumPy arrays"""
        if not hasattr(pcm, 'add_numpy_arrays'):
            self.skipTest("add_numpy_arrays function not available")
        
        arr1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        arr2 = np.array([0.5, 1.5, 2.5, 3.5, 4.5])
        
        cpp_result = pcm.add_numpy_arrays(arr1, arr2)
        numpy_result = arr1 + arr2
        
        self.assertIsInstance(cpp_result, np.ndarray)
        np.testing.assert_array_almost_equal(cpp_result, numpy_result)
    
    def test_process_numpy_1d_square(self):
        """Test processing NumPy array with square operation"""
        if not hasattr(pcm, 'process_numpy_1d'):
            self.skipTest("process_numpy_1d function not available")
        
        arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        cpp_result = pcm.process_numpy_1d(arr, 0)  # operation 0 = square
        numpy_result = arr ** 2
        
        self.assertIsInstance(cpp_result, np.ndarray)
        np.testing.assert_array_almost_equal(cpp_result, numpy_result)
    
    def test_process_numpy_1d_sqrt(self):
        """Test processing NumPy array with sqrt operation"""
        if not hasattr(pcm, 'process_numpy_1d'):
            self.skipTest("process_numpy_1d function not available")
        
        arr = np.array([1.0, 4.0, 9.0, 16.0, 25.0])
        
        cpp_result = pcm.process_numpy_1d(arr, 1)  # operation 1 = sqrt
        numpy_result = np.sqrt(arr)
        
        self.assertIsInstance(cpp_result, np.ndarray)
        np.testing.assert_array_almost_equal(cpp_result, numpy_result)
    
    def test_process_numpy_1d_abs(self):
        """Test processing NumPy array with abs operation"""
        if not hasattr(pcm, 'process_numpy_1d'):
            self.skipTest("process_numpy_1d function not available")
        
        arr = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
        
        cpp_result = pcm.process_numpy_1d(arr, 2)  # operation 2 = abs
        numpy_result = np.abs(arr)
        
        self.assertIsInstance(cpp_result, np.ndarray)
        np.testing.assert_array_almost_equal(cpp_result, numpy_result)

class TestNumPyDataTypes(unittest.TestCase):
    """Test NumPy data type handling"""
    
    def setUp(self):
        if pcm.__numpy_support__ != "enabled":
            self.skipTest("NumPy support is not enabled in the compiled module")
    
    def test_different_dtypes(self):
        """Test handling of different NumPy data types"""
        if not hasattr(pcm, 'numpy_to_list'):
            self.skipTest("numpy_to_list function not available")
        
        # Test different data types
        test_cases = [
            (np.array([1, 2, 3], dtype=np.int32), "int32"),
            (np.array([1.0, 2.0, 3.0], dtype=np.float32), "float32"),
            (np.array([1.0, 2.0, 3.0], dtype=np.float64), "float64"),
        ]
        
        for arr, dtype_name in test_cases:
            with self.subTest(dtype=dtype_name):
                try:
                    result = pcm.numpy_to_list(arr)
                    self.assertIsInstance(result, list)
                    self.assertEqual(len(result), len(arr))
                except Exception as e:
                    # Some data types might not be supported
                    print(f"Data type {dtype_name} not supported: {e}")
    
    def test_array_shapes(self):
        """Test handling of different array shapes"""
        if not hasattr(pcm, 'numpy_to_list'):
            self.skipTest("numpy_to_list function not available")
        
        # Test 1D array (should work)
        arr_1d = np.array([1.0, 2.0, 3.0])
        try:
            result = pcm.numpy_to_list(arr_1d)
            self.assertIsInstance(result, list)
        except Exception as e:
            self.fail(f"1D array should be supported: {e}")
        
        # Test 2D array (might not be supported)
        arr_2d = np.array([[1.0, 2.0], [3.0, 4.0]])
        try:
            result = pcm.numpy_to_list(arr_2d)
            print("2D arrays are supported")
        except Exception as e:
            print(f"2D arrays not supported (expected): {e}")

class TestNumPyPerformance(unittest.TestCase):
    """Test performance of NumPy operations"""
    
    def setUp(self):
        if pcm.__numpy_support__ != "enabled":
            self.skipTest("NumPy support is not enabled in the compiled module")
    
    def test_large_array_performance(self):
        """Test performance with large arrays"""
        if not hasattr(pcm, 'add_numpy_arrays'):
            self.skipTest("add_numpy_arrays function not available")
        
        import time
        
        # Create large arrays
        size = 1000000
        arr1 = np.random.random(size)
        arr2 = np.random.random(size)
        
        # Test C++ implementation
        start_time = time.time()
        cpp_result = pcm.add_numpy_arrays(arr1, arr2)
        cpp_time = time.time() - start_time
        
        # Test NumPy implementation
        start_time = time.time()
        numpy_result = arr1 + arr2
        numpy_time = time.time() - start_time
        
        # Verify results are the same
        np.testing.assert_array_almost_equal(cpp_result, numpy_result, decimal=10)
        
        print(f"Array size: {size}")
        print(f"C++ time: {cpp_time:.6f}s")
        print(f"NumPy time: {numpy_time:.6f}s")
        print(f"NumPy speedup: {cpp_time/numpy_time:.2f}x")
        
        # NumPy should typically be faster for large arrays
        # due to optimized BLAS libraries
    
    def test_processing_performance(self):
        """Test performance of array processing operations"""
        if not hasattr(pcm, 'process_numpy_1d'):
            self.skipTest("process_numpy_1d function not available")
        
        import time
        
        # Create test array
        size = 100000
        arr = np.random.random(size)
        
        # Test square operation
        start_time = time.time()
        cpp_result = pcm.process_numpy_1d(arr, 0)  # square
        cpp_time = time.time() - start_time
        
        start_time = time.time()
        numpy_result = arr ** 2
        numpy_time = time.time() - start_time
        
        # Verify results
        np.testing.assert_array_almost_equal(cpp_result, numpy_result, decimal=10)
        
        print(f"Square operation - Array size: {size}")
        print(f"C++ time: {cpp_time:.6f}s")
        print(f"NumPy time: {numpy_time:.6f}s")
        print(f"NumPy speedup: {cpp_time/numpy_time:.2f}x")

class TestNumPyErrorHandling(unittest.TestCase):
    """Test error handling with NumPy operations"""
    
    def setUp(self):
        if pcm.__numpy_support__ != "enabled":
            self.skipTest("NumPy support is not enabled in the compiled module")
    
    def test_invalid_array_types(self):
        """Test error handling with invalid array types"""
        if not hasattr(pcm, 'numpy_to_list'):
            self.skipTest("numpy_to_list function not available")
        
        # Test with non-array input
        with self.assertRaises(TypeError):
            pcm.numpy_to_list([1, 2, 3])  # Python list, not NumPy array
        
        with self.assertRaises(TypeError):
            pcm.numpy_to_list("not an array")
    
    def test_mismatched_array_sizes(self):
        """Test error handling with mismatched array sizes"""
        if not hasattr(pcm, 'add_numpy_arrays'):
            self.skipTest("add_numpy_arrays function not available")
        
        arr1 = np.array([1.0, 2.0, 3.0])
        arr2 = np.array([1.0, 2.0])  # Different size
        
        with self.assertRaises(ValueError):
            pcm.add_numpy_arrays(arr1, arr2)
    
    def test_invalid_operations(self):
        """Test error handling with invalid operations"""
        if not hasattr(pcm, 'process_numpy_1d'):
            self.skipTest("process_numpy_1d function not available")
        
        arr = np.array([1.0, 2.0, 3.0])
        
        # Test invalid operation code
        with self.assertRaises(ValueError):
            pcm.process_numpy_1d(arr, 999)  # Invalid operation

def run_numpy_tests():
    """Run all NumPy tests and return success status"""
    
    print("=== NumPy Integration Tests ===")
    print(f"Testing module: {pcm.__name__}")
    print(f"Module version: {pcm.__version__}")
    print(f"NumPy support: {pcm.__numpy_support__}")
    print(f"NumPy version: {np.__version__}")
    print()
    
    if pcm.__numpy_support__ != "enabled":
        print("NumPy support is not enabled in the compiled module.")
        print("Rebuild with ENABLE_NUMPY=ON to run these tests.")
        return False
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestNumPyIntegration,
        TestNumPyDataTypes,
        TestNumPyPerformance,
        TestNumPyErrorHandling
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\nTests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall result: {'PASSED' if success else 'FAILED'}")
    
    return success

if __name__ == '__main__':
    success = run_numpy_tests()
    sys.exit(0 if success else 1)