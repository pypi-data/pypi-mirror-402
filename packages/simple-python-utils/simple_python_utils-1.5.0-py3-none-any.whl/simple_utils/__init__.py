"""Simple Python Utilities Package.

A minimalist Python library providing basic utility functions
for common operations like printing messages and arithmetic.

Author: fjmpereira20
Version: 1.0.0
"""

from .core import (
    add_numbers,
    divide_numbers,
    multiply_numbers,
    print_message,
    square_numbers,
)

__version__ = "1.3.0"
__author__ = "fjmpereira20"
__email__ = "your.email@example.com"  # Replace with actual email

__all__ = [
    "print_message",
    "add_numbers",
    "multiply_numbers",
    "divide_numbers",
    "square_numbers",
]
