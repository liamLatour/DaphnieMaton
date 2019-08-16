import os
import unittest

from app.libraries.classes import Input
from app.libraries.config import Config


class TestConfig(unittest.TestCase):

    def setUp(self):
        self.pipe = Input(callback=self.callback)
        self.default = {
            "nbPipe": {"value": 2, "inputs": [self.pipe]},
            "lenPipe": {"value": 1, "inputs": [Input(callback=self.callback)]},
            "photoPipe": {"value": 10, "inputs": [Input(callback=self.callback)]},
            "distOriginX": {"value": 5, "inputs": [Input(callback=self.callback)]},
            "distOriginY": {"value": 5, "inputs": [Input(callback=self.callback)]},
            "sameGap": {"value": True, "inputs": [Input(inputType=1, callback=self.callback)]},
            "horizontal": {"value": False, "inputs": [Input(inputType=1, callback=self.callback)]},
            "gaps": {"value": [20], "inputs": []},
            "loop": {"value": True, "inputs": [Input(inputType=1, callback=self.callback)]},
            "trace": {"value": [], "inputs": []},
            "photos": {"value": [], "inputs": []},
            "actionNodes": {"value": [], "inputs": []}
        }
        self.config = Config(self.default, (0, 0), 1, 1)

    def test_reset(self):
        self.config.currentConfig["nbPipe"]["value"] = 8
        self.config.currentConfig["trace"]["value"] = [(5, 2), (3, 6)]
        self.config.reset()
        self.assertEqual(self.config.currentConfig["nbPipe"]["value"], 2)
        self.assertEqual(self.config.currentConfig["trace"]["value"], [])

    def test_read(self):
        gaps = [Input(callback=self.callback, default_text="0"),
                Input(callback=self.callback, default_text="3.333"),
                Input(callback=self.callback, default_text="-2")]
        self.pipe.write(8)
        self.config.read(gaps)
        self.assertEqual(self.config.currentConfig["nbPipe"]["value"], 8)
        self.assertEqual(
            self.config.currentConfig["gaps"]["value"], [0, 3.333, -2])

    def test_load_save(self):
        self.config.currentConfig["nbPipe"]["value"] = 8
        self.config.currentConfig["trace"]["value"] = [(5, 2), (3, 6)]
        self.config.save(".\\", "lol")
        self.config.reset()
        self.config.load(".\\", ["lol.json"])
        self.assertEqual(self.config.currentConfig["nbPipe"]["value"], 8)
        self.assertEqual(
            self.config.currentConfig["trace"]["value"], [[5, 2], [3, 6]])
        os.remove("lol.json")

    def test_generatePathFromPipe(self):
        result = self.config.generatePathFromPipe()
        self.assertEqual(len(result[1]), len(result[2]))
        self.assertEqual(
            result[0], [(0.05, 0.05), (0.05, 1.05), (0.25, 0.05), (0.25, 1.05)])
        self.config.currentConfig["horizontal"]["value"] = True
        result = self.config.generatePathFromPipe()
        self.assertEqual(len(result[1]), len(result[2]))
        self.assertEqual(
            result[0], [(0.05, 0.05), (1.05, 0.05), (0.05, 0.25), (1.05, 0.25)])

    def callback(self):
        print("no callback")


if __name__ == '__main__':
    unittest.main()
