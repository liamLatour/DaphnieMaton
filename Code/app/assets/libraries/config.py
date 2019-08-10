import ctypes
from json import dumps as jsDumps
from json import load as jsLoad
from os.path import join as osJoinPath


class Config():
    def __init__(self, default, origin, ratioX, ratioY):
        self.baseConfig = default
        self.currentConfig = self.baseConfig
        self.origin = origin
        self.ratioX = ratioX
        self.ratioY = ratioY

    def reset(self):
        self.currentConfig = self.baseConfig

        for param in self.currentConfig:
            for inputs in self.currentConfig[param]["inputs"]:
                inputs.write(self.currentConfig[param]["value"])

    def read(self):
        for param in self.currentConfig:
            if len(self.currentConfig[param]["inputs"]) > 0:
                self.currentConfig[param]["value"] = self.currentConfig[param]["inputs"][0].read()

    def load(self, path, filename):
        self.filePath = path
        self.fileName = filename[0].replace(".json", "")
        with open(osJoinPath(path, filename[0])) as stream:
            self.currentConfig = jsLoad(stream)
            for param in self.currentConfig:
                for inputs in self.currentConfig[param]["inputs"]:
                    inputs.write(self.currentConfig[param]["value"])

    def save(self, path, filename):
        if not filename.endswith(".json"):
            filename = filename+".json"

        with open(osJoinPath(path, filename), 'w') as stream:
            paramsCopy = self.currentConfig.copy()

            for item in paramsCopy: # Converts numpy arrays into python list
                try: paramsCopy[item]["value"] = paramsCopy[item]["value"].tolist()
                except: pass

            stream.write(jsDumps( paramsCopy ))

    def generatePathFromPipe(self, copy=False):
        """Converts the pipe parameters to a path.

        copy bool: copy in Free mode or not

        return: the converted path
        """
        path = []
        photos = []

        length = self.currentConfig["lenPipe"]*100
        self.ratioY /= 100

        xPosition = self.origin[0] + self.currentConfig["distOriginX"]*self.ratioX
        yPosition = self.origin[1] + self.currentConfig["distOriginY"]*self.ratioY

        path.append(xPosition)
        path.append(yPosition)
        photos.append(True)

        if self.currentConfig["horizontal"]:
            path.append(xPosition + length*self.ratioX)
            path.append(yPosition)
            photos.append(False)

            for x in range(self.currentConfig["nbPipe"]-1):
                yPosition += self.currentConfig["gaps"][x]*self.ratioY
                path.append(xPosition)
                path.append(yPosition)
                photos.append(True)
                path.append(xPosition + length*self.ratioX)
                path.append(yPosition)
                photos.append(False)
        else:
            path.append(xPosition)
            path.append(yPosition + length*self.ratioY)
            photos.append(False)

            for x in range(self.currentConfig["nbPipe"]-1):
                xPosition += self.currentConfig["gaps"][x]*self.ratioX
                path.append(xPosition)
                path.append(yPosition)
                photos.append(True)
                path.append(xPosition)
                path.append(yPosition + length*self.ratioY)
                photos.append(False)

        if copy:
            self.currentConfig["trace"] = path
            self.currentConfig["photos"] = photos
            self.currentConfig["actionNodes"] = [False for i in range(len(photos))]

        return (path, photos, self.currentConfig["actionNodes"])
