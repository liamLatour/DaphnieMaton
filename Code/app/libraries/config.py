import copy
import ctypes
from json import dumps as jsDumps
from json import load as jsLoad
from os.path import join as osJoinPath

import numpy as np
from scipy.spatial import distance

from .utilityFunctions import lineToPictures

class Config():
    def __init__(self, default, cmToPixel, pixelToCM):
        self.baseConfig = default
        self.copy()
        self.pixelToCM = pixelToCM
        self.cmToPixel = cmToPixel

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

        length = distance.euclidean(self.cmToPixel((0, 0)), self.cmToPixel((0, self.currentConfig["lenPipe"]["value"]*100)))
        if self.currentConfig["horizontal"]["value"]:
            length = distance.euclidean(self.cmToPixel((0, 0)), self.cmToPixel((self.currentConfig["lenPipe"]["value"]*100, 0)))
        
        xPosition, yPosition = self.cmToPixel((self.currentConfig["distOriginX"]["value"], self.currentConfig["distOriginY"]["value"]))
        
        path.append((xPosition, yPosition))
        photos.append(True)
        path.append((xPosition, yPosition + length))
        photos.append(False)

        for i in range(self.currentConfig["nbPipe"]["value"]-1):
            gap = distance.euclidean(self.cmToPixel((0, 0)), self.cmToPixel((self.currentConfig["gaps"]["value"][i], 0)))
            if self.currentConfig["horizontal"]["value"]:
                gap = distance.euclidean(self.cmToPixel((0, 0)), self.cmToPixel((0, self.currentConfig["gaps"]["value"][i])))
            xPosition += gap
            path.append((xPosition, yPosition))
            photos.append(True)
            path.append((xPosition, yPosition + length))
            photos.append(False)

        if self.currentConfig["horizontal"]["value"]:
            path = [a[::-1] for a in path]

        if copy:
            self.currentConfig["trace"]["value"] = path
            self.currentConfig["photos"]["value"] = photos
            self.currentConfig["actionNodes"]["value"] = [False for i in range(len(photos))]

        return (path, photos, [False for i in range(len(photos))])

    def unravelPath(self, path, pictures, actionNodes):
        cmValues = []
        photos = []

        for i in range(len(path)):
            curent = self.pixelToCM(path[i])
            cmValues.append((curent[1], curent[0]))

        lookAhead = 1

        for i in range(len(path)):
            photos.append(actionNodes[i])
            if pictures[i]:
                middles = lineToPictures(cmValues[i+lookAhead-1], cmValues[(i+lookAhead) % len(cmValues)], self.currentConfig["photoPipe"]["value"])
                cmValues[i+lookAhead:i+lookAhead] = middles
                lookAhead += len(middles)
                photos.extend([True for i in range(len(middles))])      

        return (cmValues, photos)

    def pathStats(self, isFree, speed):
        path = self.currentConfig["trace"]["value"]
        pictures = self.currentConfig["photos"]["value"]
        actionNodes = self.currentConfig["actionNodes"]["value"]
        if not isFree:
            path, pictures, actionNodes = self.generatePathFromPipe()

        realPath = self.unravelPath(path, pictures, actionNodes)

        dist = 0
        time = 0

        for i in range(len(realPath[0])):
            nextI = (i+1) % len(realPath[0])
            dist += distance.euclidean(realPath[0][i], realPath[0][nextI])
            time += max(abs(realPath[0][i][0]-realPath[0][nextI][0]), abs(realPath[0][i][1]-realPath[0][nextI][1]))/float(speed)

        secBetweenPhoto = self.currentConfig["photoPipe"]["value"]/float(speed)

        nbPhotos = np.sum(realPath[1])

        return ('%.2f'%(time), '%.2f'%(dist), '%.2f'%(secBetweenPhoto), nbPhotos)
