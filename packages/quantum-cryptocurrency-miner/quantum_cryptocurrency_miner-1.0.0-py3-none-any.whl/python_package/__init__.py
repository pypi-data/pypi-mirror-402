"""
Python CMake Integration Package

This package provides Python bindings for C++ functionality built with CMake.
It demonstrates integration between Python and C++ with optional NumPy support.

Features:
- Mathematical operations (add, multiply, factorial, power)
- Vector operations (sum, mean)
- Array processing with NumPy integration
- String utilities (case conversion, split, join, trim, replace)
- High-performance C++ implementations

Example usage:
    import python_cmake_module as pcm
    
    # Basic math
    result = pcm.add(5.0, 3.0)
    factorial = pcm.factorial(5)
    
    # Vector operations
    data = [1.0, 2.0, 3.0, 4.0, 5.0]
    total = pcm.sum_vector(data)
    average = pcm.mean_vector(data)
    
    # String operations
    upper_text = pcm.to_upper("hello world")
    words = pcm.split_string("apple,banana,cherry", ',')
    
    # NumPy integration (if enabled)
    import numpy as np
    arr = np.array([1.0, 2.0, 3.0])
    squared = pcm.process_numpy_1d(arr, 0)  # square operation
"""

__version__ = "1.0.0"
__author__ = "CMake Python Integration Team"
__email__ = "team@example.com"
__description__ = "Python bindings for C++ functionality built with CMake"

# Try to import the compiled module
try:
    from . import python_cmake_module
    
    # Re-export main functions for convenience
    from .python_cmake_module import (
        add, multiply, factorial, power,
        sum_vector, mean_vector,
        to_upper, to_lower, split_string
    )
    
    # Check for NumPy functions
    if hasattr(python_cmake_module, 'process_numpy_1d'):
        from .python_cmake_module import (
            process_numpy_1d, numpy_to_list, list_to_numpy, add_numpy_arrays
        )
        _numpy_functions_available = True
    else:
        _numpy_functions_available = False
    
    # Module information
    MODULE_VERSION = python_cmake_module.__version__
    NUMPY_SUPPORT = python_cmake_module.__numpy_support__
    
except ImportError as e:
    import warnings
    warnings.warn(f"Could not import compiled module: {e}")
    
    # Provide fallback implementations
    def add(a, b):
        """Fallback implementation of add"""
        return a + b
    
    def multiply(a, b):
        """Fallback implementation of multiply"""
        return a * b
    
    def factorial(n):
        """Fallback implementation of factorial"""
        if n < 0:
            raise ValueError("Factorial is not defined for negative numbers")
        if n <= 1:
            return 1
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result
    
    def power(base, exponent):
        """Fallback implementation of power"""
        return base ** exponent
    
    def sum_vector(vec):
        """Fallback implementation of sum_vector"""
        return sum(vec)
    
    def mean_vector(vec):
        """Fallback implementation of mean_vector"""
        if not vec:
            raise ValueError("Cannot calculate mean of empty vector")
        return sum(vec) / len(vec)
    
    def to_upper(s):
        """Fallback implementation of to_upper"""
        return s.upper()
    
    def to_lower(s):
        """Fallback implementation of to_lower"""
        return s.lower()
    
    def split_string(s, delimiter):
        """Fallback implementation of split_string"""
        return s.split(delimiter)
    
    MODULE_VERSION = __version__
    NUMPY_SUPPORT = "disabled"
    _numpy_functions_available = False

# Utility functions
def get_module_info():
    """Get information about the module"""
    info = {
        'package_version': __version__,
        'module_version': MODULE_VERSION,
        'numpy_support': NUMPY_SUPPORT,
        'numpy_functions_available': _numpy_functions_available,
        'description': __description__,
        'author': __author__
    }
    return info

def print_module_info():
    """Print module information"""
    info = get_module_info()
    print("Python CMake Integration Module")
    print("=" * 35)
    for key, value in info.items():
        print(f"{key.replace('_', ' ').title()}: {value}")

# Check for NumPy availability
def check_numpy_compatibility():
    """Check NumPy compatibility"""
    try:
        import numpy as np
        numpy_version = np.__version__
        numpy_available = True
    except ImportError:
        numpy_version = "Not installed"
        numpy_available = False
    
    return {
        'numpy_installed': numpy_available,
        'numpy_version': numpy_version,
        'module_numpy_support': NUMPY_SUPPORT,
        'numpy_functions_available': _numpy_functions_available,
        'compatible': numpy_available and NUMPY_SUPPORT == "enabled"
    }

# Performance testing utilities
def benchmark_operations(size=100000, iterations=5):
    """Benchmark C++ vs Python operations"""
    import time
    import statistics
    
    # Generate test data
    test_data = list(range(size))
    
    results = {}
    
    # Benchmark sum operation
    cpp_times = []
    python_times = []
    
    for _ in range(iterations):
        # C++ implementation
        start = time.time()
        cpp_result = sum_vector(test_data)
        cpp_times.append(time.time() - start)
        
        # Python implementation
        start = time.time()
        python_result = sum(test_data)
        python_times.append(time.time() - start)
        
        # Verify results match
        assert abs(cpp_result - python_result) < 1e-10
    
    results['sum_operation'] = {
        'cpp_mean_time': statistics.mean(cpp_times),
        'python_mean_time': statistics.mean(python_times),
        'speedup': statistics.mean(python_times) / statistics.mean(cpp_times),
        'data_size': size,
        'iterations': iterations
    }
    
    return results

# Export main interface
__all__ = [
    # Core functions
    'add', 'multiply', 'factorial', 'power',
    'sum_vector', 'mean_vector',
    'to_upper', 'to_lower', 'split_string',
    
    # Utility functions
    'get_module_info', 'print_module_info',
    'check_numpy_compatibility', 'benchmark_operations',
    
    # Constants
    'MODULE_VERSION', 'NUMPY_SUPPORT'
]

# Add NumPy functions to exports if available
if _numpy_functions_available:
    __all__.extend([
        'process_numpy_1d', 'numpy_to_list', 'list_to_numpy', 'add_numpy_arrays'
    ])