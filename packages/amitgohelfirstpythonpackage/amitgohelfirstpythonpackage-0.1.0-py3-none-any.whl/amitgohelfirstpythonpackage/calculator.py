class Calculator:
    def __init__(self, base=0):
        self.base = base

    def add(self, value):
        self.base += value
        return self.base

    def reset(self):
        self.base = 0
