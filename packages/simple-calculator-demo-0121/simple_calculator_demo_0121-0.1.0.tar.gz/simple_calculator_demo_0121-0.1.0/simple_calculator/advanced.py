"""
Advanced mathematical operations
"""

import math
from typing import List

def factorial(n: int) -> int:
    """
    Calculate factorial of a number
    
    Args:
        n: Positive integer
    
    Returns:
        Factorial of n
    
    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n == 0:
        return 1
    return math.prod(range(1, n + 1))

def fibonacci(n: int) -> List[int]:
    """
    Generate Fibonacci sequence up to n terms
    
    Args:
        n: Number of terms to generate
    
    Returns:
        List of Fibonacci numbers
    """
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    fib_seq = [0, 1]
    for i in range(2, n):
        fib_seq.append(fib_seq[i-1] + fib_seq[i-2])
    return fib_seq

def is_prime(n: int) -> bool:
    """
    Check if a number is prime
    
    Args:
        n: Number to check
    
    Returns:
        True if prime, False otherwise
    """
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


class Statistics:
    """Statistics calculation class"""
    
    @staticmethod
    def mean(numbers: List[float]) -> float:
        """Calculate arithmetic mean"""
        if not numbers:
            raise ValueError("List cannot be empty")
        return sum(numbers) / len(numbers)
    
    @staticmethod
    def median(numbers: List[float]) -> float:
        """Calculate median"""
        if not numbers:
            raise ValueError("List cannot be empty")
        
        sorted_numbers = sorted(numbers)
        n = len(sorted_numbers)
        mid = n // 2
        
        if n % 2 == 0:
            return (sorted_numbers[mid - 1] + sorted_numbers[mid]) / 2
        else:
            return sorted_numbers[mid]
    
    @staticmethod
    def mode(numbers: List[float]) -> List[float]:
        """Calculate mode(s)"""
        if not numbers:
            raise ValueError("List cannot be empty")
        
        from collections import Counter
        counts = Counter(numbers)
        max_count = max(counts.values())
        return [num for num, count in counts.items() if count == max_count]
