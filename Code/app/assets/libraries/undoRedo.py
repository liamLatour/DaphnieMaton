class UndoRedo():
    def __init__(self):
        self.stack = [[[], [], []]]
        self.index = 0

    def do(self, thing):
        if self.index < len(self.stack)-1:
            del self.stack[self.index+1:]
        self.stack.append(thing)
        self.index += 1

    def undo(self, direction):
        self.index = min(max(self.index+direction, 0), len(self.stack)-1)
        return self.stack[self.index]
