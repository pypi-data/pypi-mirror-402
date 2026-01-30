import unittest
from simple_calculator.calculator import (
    add, subtract, multiply, divide, power, Calculator
)

class TestBasicOperations(unittest.TestCase):
    
    def test_add(self):
        self.assertEqual(add(2, 3), 5)
        self.assertEqual(add(-1, 1), 0)
    
    def test_subtract(self):
        self.assertEqual(subtract(5, 3), 2)
        self.assertEqual(subtract(3, 5), -2)
    
    def test_multiply(self):
        self.assertEqual(multiply(4, 3), 12)
        self.assertEqual(multiply(-2, 3), -6)
    
    def test_divide(self):
        self.assertEqual(divide(10, 2), 5)
        with self.assertRaises(ValueError):
            divide(5, 0)
    
    def test_power(self):
        self.assertEqual(power(2, 3), 8)
        self.assertEqual(power(5, 0), 1)

class TestCalculatorClass(unittest.TestCase):
    
    def setUp(self):
        self.calc = Calculator()
    
    def test_calculator_operations(self):
        self.assertEqual(self.calc.add(2, 3), 5)
        self.assertEqual(self.calc.multiply(4, 3), 12)
    
    def test_history(self):
        self.calc.add(1, 2)
        self.calc.multiply(3, 4)
        history = self.calc.get_history()
        self.assertEqual(len(history), 2)
        self.assertIn("1 + 2 = 3", history)

if __name__ == '__main__':
    unittest.main()
