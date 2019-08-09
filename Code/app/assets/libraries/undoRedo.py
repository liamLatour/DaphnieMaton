class UndoRedo():
    def __init__(self):
        self.stack = []

    def do(self, thing):
        if len(self.stack) == 0 or thing != self.stack[-1]:
            if len(self.stack) == 0:
                self.stack.append([[], [], []])
            self.stack.append(thing)

    def undo(self, current):
        if len(self.stack) > 0:
            a = self.stack.pop()
            if a == current:
                return self.stack.pop()
            return a
        return -1