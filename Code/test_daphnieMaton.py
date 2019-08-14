from app.ParametrageV2 import DaphnieMatonApp
import unittest
import random
import sys
import os
import time
from functools import partial
from kivy.clock import Clock


class TestDaphnieMaton(unittest.TestCase):

    def setUp(self):
        self.app = DaphnieMatonApp()

    def pause(*args):
        time.sleep(0.000001)

    def run_test_new_config(self, app):
        Clock.schedule_interval(self.pause, 0.000001)

        self.app.app.ids.nbPipe.write(5)

        # Comment out if you are editing the test, it'll leave the
        # Window opened.
        # self.app.stop()

    def test_new_config(self):
        Clock.schedule_once(self.run_test, 0.000001)
        self.app.run()


if __name__ == '__main__':
    unittest.main()
