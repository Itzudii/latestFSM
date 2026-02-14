class Stack:
    def __init__(self):
        self.container = []
    
    def push(self,value):
        self.container.append(value)
        return value
    
    def pop(self):
        return self.container.pop(-1)
    
    def top(self):
        return self.container[-1]

    def empty(self):
        return True if not self.container else False

