import unittest
import random
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.assets.libraries import utilityFunctions


class TestUndoRedo(unittest.TestCase):

    def test_hitLine_borderTop(self):
        point1 = (random.random(), random.random())
        self.assertTrue(utilityFunctions.hitLine(point1, (2, 3), point1, 0))

    def test_hitLine_borderSide(self):
        a = random.random()
        self.assertTrue(utilityFunctions.hitLine((0, -3), (0, 3), (a, 0), a))
        self.assertTrue(utilityFunctions.hitLine((0, -3), (0, 3), (-a, 0), a))

    def test_hitLine_toFar(self):
        a = random.random()
        self.assertFalse(utilityFunctions.hitLine((0, -3), (0, 3), (0, 3+a), 0))
        self.assertFalse(utilityFunctions.hitLine((0, -3), (0, 3), (0, -3-a), 0))

    def test_hitLine_positiveWidth(self):
        with self.assertRaises(ValueError):
            utilityFunctions.hitLine((0, -3), (0, 3), (0, -3), -1)

    def test_lineToPictures(self):
        pass

if __name__ == '__main__':
    unittest.main()