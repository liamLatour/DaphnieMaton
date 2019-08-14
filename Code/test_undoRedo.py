from app.libraries.undoRedo import UndoRedo
import unittest
import random
import sys
import os


class TestUndoRedo(unittest.TestCase):

    def setUp(self):
        self.start = [[[(random.random(), random.random())], [
            random.randint(0, 1) == 1], [random.randint(0, 1) == 1]]]
        self.second = [[[(random.random(), random.random())], [
            random.randint(0, 1) == 1], [random.randint(0, 1) == 1]]]
        self.undoRedo = UndoRedo()
        self.undoRedo.do(self.start)
        self.undoRedo.do(self.second)

    def test_fullLeft(self):
        self.undoRedo.undo(-1)
        for i in range(5):  # Just to be sure some stacking of 'default' is not happening
            self.assertEqual(self.undoRedo.undo(-1), [[], [], []])

    def test_fullRight(self):
        self.assertEqual(self.undoRedo.undo(1), self.second)

    def test_simple(self):
        self.assertEqual(self.undoRedo.undo(-1), self.start)
        self.assertEqual(self.undoRedo.undo(1), self.second)

    def test_overlapping(self):
        self.undoRedo.undo(-1)
        a = [[[(random.random(), random.random())], [
            random.randint(0, 1) == 1], [random.randint(0, 1) == 1]]]
        self.undoRedo.do(a)
        self.assertEqual(self.undoRedo.undo(-1), self.start)
        self.assertEqual(self.undoRedo.undo(1), a)


if __name__ == '__main__':
    unittest.main()
