import ctypes
from json import dumps as jsDumps
from json import load as jsLoad
from os.path import join as osJoinPath
import numpy as np
import copy


class Config():
    def __init__(self, default, origin, ratioX, ratioY):
        self.baseConfig = default
        self.copy()
        self.origin = origin
        self.ratioX = ratioX/100
        self.ratioY = ratioY/100

    def copy(self):
        self.currentConfig = {}
        for param in self.baseConfig:
            self.currentConfig[param] = {'value': copy.deepcopy(
                self.baseConfig[param]['value']), 'inputs': self.baseConfig[param]['inputs']}

    def reset(self):
        self.copy()
        for param in self.currentConfig:
            for inputs in self.currentConfig[param]["inputs"]:
                inputs.write(self.currentConfig[param]["value"])

    def read(self, gaps=None):
        for param in self.currentConfig:
            if len(self.currentConfig[param]["inputs"]) > 0:
                self.currentConfig[param]["value"] = self.currentConfig[param]["inputs"][0].read()

        if gaps is not None:
            gapsValue = []
            if max(self.currentConfig["nbPipe"]["value"], 1) > 1:
                if bool(self.currentConfig["sameGap"]["value"]):
                    gapsValue = np.ones(
                        max(self.currentConfig["nbPipe"]["value"], 1)-1) * gaps[0].read()
                else:
                    for gap in gaps:
                        gapsValue.append(gap.read())

            if len(gapsValue) == 0:
                gapsValue = [20]
                if len(self.currentConfig["gaps"]["value"]) > 0:
                    gapsValue = [self.currentConfig["gaps"]["value"][0]]
            self.currentConfig["gaps"]["value"] = gapsValue

    def load(self, path, filename):
        self.filePath = path
        self.fileName = filename[0].replace(".json", "")
        with open(osJoinPath(path, filename[0])) as stream:
            newConfig = jsLoad(stream)
            for param in self.currentConfig:
                self.currentConfig[param]["value"] = newConfig[param]
                for inputs in self.currentConfig[param]["inputs"]:
                    inputs.write(newConfig[param])

    def save(self, path, filename):
        if not filename.endswith(".json"):
            filename = filename+".json"

        with open(osJoinPath(path, filename), 'w') as stream:
            paramsCopy = self.currentConfig.copy()

            for item in paramsCopy:  # Converts numpy arrays into python list
                paramsCopy[item] = paramsCopy[item]["value"]
                if type(paramsCopy[item]).__module__ == np.__name__:
                    paramsCopy[item] = paramsCopy[item].tolist()

            stream.write(jsDumps(paramsCopy))

    def generatePathFromPipe(self, copy=False):
        """Converts the pipe parameters to a path.

        copy bool: copy in Free mode or not

        return: the converted path
        """
        path = []
        photos = []

        length = self.currentConfig["lenPipe"]["value"]*100

        xPosition = self.origin[0] + self.currentConfig["distOriginX"]["value"]*self.ratioX
        yPosition = self.origin[1] + self.currentConfig["distOriginY"]["value"]*self.ratioY

        path.append((xPosition, yPosition))
        photos.append(True)

        if self.currentConfig["horizontal"]["value"]:
            path.append((xPosition + length*self.ratioX, yPosition))
            photos.append(False)

            for x in range(self.currentConfig["nbPipe"]["value"]-1):
                yPosition += self.currentConfig["gaps"]["value"][x]*self.ratioY
                path.append((xPosition, yPosition))
                photos.append(True)
                path.append((xPosition + length*self.ratioX, yPosition))
                photos.append(False)
        else:
            path.append((xPosition, yPosition + length*self.ratioY))
            photos.append(False)

            for x in range(self.currentConfig["nbPipe"]["value"]-1):
                xPosition += self.currentConfig["gaps"]["value"][x]*self.ratioX
                path.append((xPosition, yPosition))
                photos.append(True)
                path.append((xPosition, yPosition + length*self.ratioY))
                photos.append(False)

        if copy:
            self.currentConfig["trace"]["value"] = path
            self.currentConfig["photos"]["value"] = photos
            self.currentConfig["actionNodes"]["value"] = [False for i in range(len(photos))]

        return (path, photos, [False for i in range(len(photos))])
