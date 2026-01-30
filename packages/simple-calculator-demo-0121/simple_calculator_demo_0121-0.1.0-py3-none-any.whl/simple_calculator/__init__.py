"""
Simple Calculator - A basic calculator package for demonstration
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .calculator import (
    add,
    subtract,
    multiply,
    divide,
    power,
    Calculator
)

from .advanced import (
    factorial,
    fibonacci,
    is_prime,
    Statistics
)

__all__ = [
    'add',
    'subtract',
    'multiply',
    'divide',
    'power',
    'Calculator',
    'factorial',
    'fibonacci',
    'is_prime',
    'Statistics'
]
