from app.libraries import utilityFunctions
import unittest
import random


class TestHitLine(unittest.TestCase):

    def test_hitLine_borderTop(self):
        point1 = (random.random(), random.random())
        self.assertTrue(utilityFunctions.hitLine(point1, (2, 3), point1, 0))

    def test_hitLine_borderSide(self):
        a = random.random()
        self.assertTrue(utilityFunctions.hitLine((0, -3), (0, 3), (a, 0), a))
        self.assertTrue(utilityFunctions.hitLine((0, -3), (0, 3), (-a, 0), a))

    def test_hitLine_toFar(self):
        a = random.random()
        self.assertFalse(utilityFunctions.hitLine(
            (0, -3), (0, 3), (0, 3+a), 0))
        self.assertFalse(utilityFunctions.hitLine(
            (0, -3), (0, 3), (0, -3-a), 0))

    def test_hitLine_positiveWidth(self):
        with self.assertRaises(ValueError):
            utilityFunctions.hitLine((0, -3), (0, 3), (0, -3), -1)


class TestLineToPictures(unittest.TestCase):

    def test_lineToPictures_normal(self):
        self.assertEqual(utilityFunctions.lineToPictures((11.4, 17.1), (94.3, 85.2), 10), [(14.21, 19.41), (21.94, 25.76), (29.67, 32.11), (
            37.4, 38.45), (45.12, 44.8), (52.85, 51.15), (60.58, 57.5), (68.3, 63.85), (76.03, 70.19), (83.76, 76.54), (91.49, 82.89)])

    def test_lineToPictures_zero(self):
        self.assertEqual(utilityFunctions.lineToPictures(
            (11.4, 17.1), (94.3, 85.2), 0), [])

    def test_lineToPictures_samePoint(self):
        self.assertEqual(utilityFunctions.lineToPictures(
            (10, 5), (10, 5), 5), [(10, 5)])


if __name__ == '__main__':
    unittest.main()
