stack = []

def do(thing):
    global stack
    if len(stack) == 0 or thing != stack[-1]:
        if len(stack) == 0:
            stack.append([[], [], []])
        stack.append(thing)

def undo(current):
    global stack
    if len(stack) > 0:
        a = stack.pop()
        if a == current:
            return stack.pop()
        else:
            return a
    else:
        return -1