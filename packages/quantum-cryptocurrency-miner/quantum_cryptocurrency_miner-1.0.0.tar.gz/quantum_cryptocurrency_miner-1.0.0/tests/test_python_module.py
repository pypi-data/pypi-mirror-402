#!/usr/bin/env python3
"""
Unit tests for the Python module built with CMake.
Tests basic functionality without NumPy dependencies.
"""

import sys
import os
import unittest
import math

# Add the build directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python_package'))

try:
    import python_cmake_module as pcm
except ImportError as e:
    print(f"Failed to import python_cmake_module: {e}")
    print("Make sure the module is built and in the correct location.")
    sys.exit(1)

class TestMathOperations(unittest.TestCase):
    """Test mathematical operations"""
    
    def test_addition(self):
        self.assertAlmostEqual(pcm.add(2.5, 3.7), 6.2)
        self.assertAlmostEqual(pcm.add(-1.0, 1.0), 0.0)
        self.assertAlmostEqual(pcm.add(0.0, 0.0), 0.0)
    
    def test_multiplication(self):
        self.assertAlmostEqual(pcm.multiply(3.0, 4.0), 12.0)
        self.assertAlmostEqual(pcm.multiply(-2.0, 5.0), -10.0)
        self.assertAlmostEqual(pcm.multiply(0.0, 100.0), 0.0)
    
    def test_factorial(self):
        self.assertEqual(pcm.factorial(0), 1)
        self.assertEqual(pcm.factorial(1), 1)
        self.assertEqual(pcm.factorial(5), 120)
        self.assertEqual(pcm.factorial(10), 3628800)
        
        # Test negative input
        with self.assertRaises(ValueError):
            pcm.factorial(-1)
    
    def test_power(self):
        self.assertAlmostEqual(pcm.power(2.0, 3.0), 8.0)
        self.assertAlmostEqual(pcm.power(5.0, 0.0), 1.0)
        self.assertAlmostEqual(pcm.power(4.0, 0.5), 2.0)
        self.assertAlmostEqual(pcm.power(-2.0, 2.0), 4.0)
    
    def test_sum_vector(self):
        vec1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        self.assertAlmostEqual(pcm.sum_vector(vec1), 15.0)
        
        vec2 = [-1.0, 1.0, -2.0, 2.0]
        self.assertAlmostEqual(pcm.sum_vector(vec2), 0.0)
        
        empty_vec = []
        self.assertAlmostEqual(pcm.sum_vector(empty_vec), 0.0)
    
    def test_mean_vector(self):
        vec1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        self.assertAlmostEqual(pcm.mean_vector(vec1), 3.0)
        
        vec2 = [10.0, 20.0]
        self.assertAlmostEqual(pcm.mean_vector(vec2), 15.0)
        
        # Test empty vector
        with self.assertRaises(ValueError):
            pcm.mean_vector([])

class TestStringOperations(unittest.TestCase):
    """Test string manipulation operations"""
    
    def test_to_upper(self):
        self.assertEqual(pcm.to_upper("hello world"), "HELLO WORLD")
        self.assertEqual(pcm.to_upper("MiXeD cAsE"), "MIXED CASE")
        self.assertEqual(pcm.to_upper(""), "")
        self.assertEqual(pcm.to_upper("123!@#"), "123!@#")
    
    def test_to_lower(self):
        self.assertEqual(pcm.to_lower("HELLO WORLD"), "hello world")
        self.assertEqual(pcm.to_lower("MiXeD cAsE"), "mixed case")
        self.assertEqual(pcm.to_lower(""), "")
        self.assertEqual(pcm.to_lower("123!@#"), "123!@#")
    
    def test_split_string(self):
        result = pcm.split_string("apple,banana,cherry", ',')
        expected = ["apple", "banana", "cherry"]
        self.assertEqual(result, expected)
        
        result = pcm.split_string("one two three", ' ')
        expected = ["one", "two", "three"]
        self.assertEqual(result, expected)
        
        result = pcm.split_string("no-delimiter", ',')
        expected = ["no-delimiter"]
        self.assertEqual(result, expected)
        
        result = pcm.split_string("", ',')
        expected = [""]
        self.assertEqual(result, expected)

class TestModuleProperties(unittest.TestCase):
    """Test module properties and metadata"""
    
    def test_version(self):
        self.assertTrue(hasattr(pcm, '__version__'))
        self.assertIsInstance(pcm.__version__, str)
        self.assertRegex(pcm.__version__, r'\d+\.\d+\.\d+')
    
    def test_numpy_support(self):
        self.assertTrue(hasattr(pcm, '__numpy_support__'))
        self.assertIn(pcm.__numpy_support__, ['enabled', 'disabled'])

class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""
    
    def test_type_errors(self):
        # Test with wrong argument types
        with self.assertRaises(TypeError):
            pcm.add("string", 5.0)
        
        with self.assertRaises(TypeError):
            pcm.sum_vector("not a list")
        
        with self.assertRaises(TypeError):
            pcm.split_string(123, ',')
    
    def test_value_errors(self):
        # Test with invalid values
        with self.assertRaises(ValueError):
            pcm.factorial(-5)
        
        with self.assertRaises(ValueError):
            pcm.mean_vector([])
    
    def test_edge_cases(self):
        # Test with very large numbers
        large_result = pcm.add(1e10, 1e10)
        self.assertAlmostEqual(large_result, 2e10)
        
        # Test with very small numbers
        small_result = pcm.add(1e-10, 1e-10)
        self.assertAlmostEqual(small_result, 2e-10, places=15)
        
        # Test with infinity
        inf_result = pcm.add(float('inf'), 1.0)
        self.assertTrue(math.isinf(inf_result))
        
        # Test with NaN
        nan_result = pcm.add(float('nan'), 1.0)
        self.assertTrue(math.isnan(nan_result))

class TestPerformance(unittest.TestCase):
    """Test performance characteristics"""
    
    def test_large_vector_operations(self):
        import time
        
        # Create a large vector
        large_vector = list(range(100000))
        
        # Test C++ sum
        start_time = time.time()
        cpp_result = pcm.sum_vector(large_vector)
        cpp_time = time.time() - start_time
        
        # Test Python sum
        start_time = time.time()
        python_result = sum(large_vector)
        python_time = time.time() - start_time
        
        # Results should be the same
        self.assertAlmostEqual(cpp_result, python_result)
        
        # C++ should be faster (though this might not always be true for sum)
        print(f"C++ time: {cpp_time:.6f}s, Python time: {python_time:.6f}s")
        print(f"Speedup: {python_time/cpp_time:.2f}x")
    
    def test_string_operations_performance(self):
        import time
        
        # Test with a moderately large string
        test_string = "hello world " * 1000
        
        start_time = time.time()
        cpp_result = pcm.to_upper(test_string)
        cpp_time = time.time() - start_time
        
        start_time = time.time()
        python_result = test_string.upper()
        python_time = time.time() - start_time
        
        # Results should be the same
        self.assertEqual(cpp_result, python_result)
        
        print(f"String C++ time: {cpp_time:.6f}s, Python time: {python_time:.6f}s")

def run_tests():
    """Run all tests and return success status"""
    
    print("=== Python Module Unit Tests ===")
    print(f"Testing module: {pcm.__name__}")
    print(f"Module version: {pcm.__version__}")
    print(f"NumPy support: {pcm.__numpy_support__}")
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestMathOperations,
        TestStringOperations,
        TestModuleProperties,
        TestErrorHandling,
        TestPerformance
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
    success = run_tests()
    sys.exit(0 if success else 1)