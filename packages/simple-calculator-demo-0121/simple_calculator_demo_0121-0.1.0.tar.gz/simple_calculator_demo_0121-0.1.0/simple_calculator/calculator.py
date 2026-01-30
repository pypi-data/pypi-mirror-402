"""
Basic calculator operations
"""

class Calculator:
    """A simple calculator class"""
    
    def __init__(self, name="MyCalculator"):
        self.name = name
        self.history = []
    
    def add(self, a, b):
        """Return the sum of a and b"""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def subtract(self, a, b):
        """Return the difference of a and b"""
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result
    
    def multiply(self, a, b):
        """Return the product of a and b"""
        result = a * b
        self.history.append(f"{a} × {b} = {result}")
        return result
    
    def divide(self, a, b):
        """Return the quotient of a and b"""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = a / b
        self.history.append(f"{a} ÷ {b} = {result}")
        return result
    
    def power(self, base, exponent):
        """Return base raised to the power of exponent"""
        result = base ** exponent
        self.history.append(f"{base}^{exponent} = {result}")
        return result
    
    def get_history(self):
        """Return calculation history"""
        return self.history
    
    def clear_history(self):
        """Clear calculation history"""
        self.history.clear()


# Functional API (alternative to class-based)
def add(a, b):
    """Return the sum of a and b"""
    return a + b

def subtract(a, b):
    """Return the difference of a and b"""
    return a - b

def multiply(a, b):
    """Return the product of a and b"""
    return a * b

def divide(a, b):
    """Return the quotient of a and b"""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

def power(base, exponent):
    """Return base raised to the power of exponent"""
    return base ** exponent
