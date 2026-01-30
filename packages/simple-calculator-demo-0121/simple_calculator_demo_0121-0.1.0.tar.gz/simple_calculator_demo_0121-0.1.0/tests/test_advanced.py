import unittest
from simple_calculator.advanced import (
    factorial, fibonacci, is_prime, Statistics
)

class TestAdvancedOperations(unittest.TestCase):
    
    def test_factorial(self):
        self.assertEqual(factorial(0), 1)
        self.assertEqual(factorial(5), 120)
        with self.assertRaises(ValueError):
            factorial(-1)
    
    def test_fibonacci(self):
        self.assertEqual(fibonacci(0), [])
        self.assertEqual(fibonacci(1), [0])
        self.assertEqual(fibonacci(5), [0, 1, 1, 2, 3])
    
    def test_is_prime(self):
        self.assertTrue(is_prime(2))
        self.assertTrue(is_prime(17))
        self.assertFalse(is_prime(1))
        self.assertFalse(is_prime(4))

class TestStatistics(unittest.TestCase):
    
    def test_mean(self):
        stats = Statistics()
        self.assertEqual(stats.mean([1, 2, 3, 4, 5]), 3)
        self.assertEqual(stats.mean([10, 20, 30]), 20)
    
    def test_median(self):
        stats = Statistics()
        self.assertEqual(stats.median([1, 3, 5]), 3)
        self.assertEqual(stats.median([1, 2, 3, 4]), 2.5)
    
    def test_mode(self):
        stats = Statistics()
        self.assertEqual(stats.mode([1, 2, 2, 3, 4]), [2])
        self.assertEqual(sorted(stats.mode([1, 1, 2, 2, 3])), [1, 2])

if __name__ == '__main__':
    unittest.main()
