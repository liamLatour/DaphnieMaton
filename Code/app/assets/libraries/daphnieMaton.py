import ctypes
import json
import os
import re
import threading
import time
from functools import partial
from json import dumps as jsDumps
from json import load as jsLoad
from math import atan2, cos, floor, hypot, pi, pow, sin, sqrt
from os import system as osSystem
from os.path import join as osJoinPath

import keyboard
import kivy.utils as utils
import numpy as np
import pyperclip
import serial
from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from scipy.spatial import distance

from .arduinoMega import Arduino
from .classes import (
    ActionChoosing, Input, LoadDialog, MenuDropDown, MyLabel, SaveDialog)
from .createFile import generateFile
from .helpMsg import helpMsg
from .localization import _
from .undoRedo import UndoRedo
from .utilityFunctions import checkUpdates, getPorts, hitLine, urlOpen
from .config import Config

class Parametrage(BoxLayout):
    def __init__(self, *args, **kwargs):
        super(Parametrage, self).__init__(*args, **kwargs)
        self.settings = App.get_running_app().config
        self.font = ".\\assets\\seguisym.ttf"
        self.mode = "Pipe" # Stores the current mode
        self.portDropDown = MenuDropDown()
        self.fileDropDown = MenuDropDown()
        self.undoRedo = UndoRedo()
        self.arduino = Arduino(self.settings, self.easyPopup, self.update_rect, programs={
                                            "Direct":
                                                    {"isDirectProgram": True, "path": ".\\assets\\directFile\\directFile.ino"},
                                            "Current":
                                                    {"isDirectProgram": False, "path": ".\\assets\\currentFile\\currentFile.ino"}})

        self.speed = self.settings.get('general', 'speed') # meters per second
        self.imageWidth = 1.4 # in meter
        self.imageHeight = 1.4 # in meter
        self.actualWidth = 1.144 # in meter
        self.actualHeight = 1.1 # in meter
        self.imageOrigin = (17, 17.2) # in cm

        # Search for arduino installation
        if not os.path.isfile(self.settings.get('general', 'arduinoPath') + '/arduino_debug.exe'):
            threading.Thread(target=lambda: self.findArduinoDir("arduino.exe", "C:\\")).start()

        # Specific to the mode 'Pipe'
        self.pipePanel = self.ids.tuyeauInputs
        self.gaps = []

        # Specific to the mode 'Free'
        self.lineWidth = 5
        self.diametre = 20
        self.isDragging = -1
        self.lastTouched = -1
        self.zoomFactor = 1
        self.innerScreenMargin = [-self.diametre/2-5, self.diametre/2+5, self.diametre/2+25, -self.diametre/2-25] # Left, Right, Top, Down
        self.corners = [(88, 82), (88, -72), (-75, 82), (-75, -72)] # Right-Top, Right-Down, Left-Top, Left-Down

        # Specific to the mode 'direct'
        self.switchDiameter = 30.

        Clock.schedule_once(self.binding)
        Clock.schedule_interval(partial(self.save, -1, -1), int(self.settings.get('general', 'autoSave'))*60)

        keyboard.on_release_key('shift', self.update_rect)

    def binding(self, *args):
        self.ids.pipeDrawing.bind(size=self.update_rect, pos=self.update_rect)
        self.ids.directDrawing.bind(size=self.update_rect, pos=self.update_rect)
        self.ids.libreDrawing.bind(size=self.update_rect, pos=self.update_rect)
        self.ids.changeTab.bind(on_touch_up = self.changedTab)
        self.config = Config({
                "nbPipe": {"value": 2, "inputs": [self.ids.nbPipe]},
                "lenPipe" : {"value": 0.9, "inputs": [self.ids.lenPipe]},
                "photoPipe" : {"value": 10, "inputs": [self.ids.photoPipe]},
                "distOriginX" : {"value": 5, "inputs": [self.ids.distOriginX]},
                "distOriginY" : {"value": 5, "inputs": [self.ids.distOriginY]},
                "sameGap" : {"value": True, "inputs": [self.ids.sameGap]},
                "horizontal" : {"value": False, "inputs": [self.ids.horizontal]},
                "gaps" : {"value": [20], "inputs": []},    #
                "loop" : {"value": True, "inputs": [self.ids.loop]},
                "trace" : {"value": [], "inputs": []},     #
                "photos" : {"value": [], "inputs": []},    #
                "actionNodes": {"value": [], "inputs": []} #
            },
            self.corners[3],
            (self.corners[0][0]-self.corners[2][0])/(self.actualWidth*100),
            (self.corners[0][1] - self.corners[1][1]) / (self.actualHeight)
        )
        self.newFile(False)
        self.updateColors(refresh=False)
        self.tuyeauGap()

        newVersion = checkUpdates("../../version")
        textPopup = "[u]A new version is available ![/u]\n\n \
                        You can download it [ref=https://github.com/liamLatour/DaphnieMaton/archive/master.zip][color=0083ff][u]here[/u][/color][/ref]"
        if newVersion != False:
            self.popbox = BoxLayout()
            self.poplb = Label(text=textPopup, markup = True)
            self.poplb.bind(on_ref_press=urlOpen)
            self.popbox.add_widget(self.poplb)

            self.easyPopup(_('New Version ' + newVersion), self.popbox)

    def updateColors(self, refresh=True):
        self.pipeColor = utils.get_color_from_hex(self.settings.get('colors', 'pipeColor'))
        self.background = utils.get_color_from_hex(self.settings.get('colors', 'background'))
        self.nodeColor = utils.get_color_from_hex(self.settings.get('colors', 'nodeColor'))
        self.nodeHighlight = utils.get_color_from_hex(self.settings.get('colors', 'nodeHighlight'))
        self.actionNode = utils.get_color_from_hex(self.settings.get('colors', 'actionNode'))
        self.pathColor = utils.get_color_from_hex(self.settings.get('colors', 'pathColor'))
        self.pathHighlight = utils.get_color_from_hex(self.settings.get('colors', 'pathHighlight'))

        if refresh:
            self.update_rect()

    def findArduinoDir(self, name, path):
        for currentPath in os.walk(path):
            if name in currentPath[2]:
                print("Found arduino path: " + currentPath[0])
                self.settings.set("general", "arduinoPath", str(currentPath[0]))
                self.settings.write()
                return

    def help(self, *args):
        self.popbox = BoxLayout()

        self.poplb = MyLabel(text=helpMsg[self.mode])
        self.poplb.bind(on_ref_press=urlOpen)
        self.popbox.add_widget(self.poplb)

        self.easyPopup(_('Help'), self.popbox)




    def newFile(self, refresh, *args):
        self.filePath = -1
        self.fileName = _("configuration")
        
        self.config.reset()

        if refresh:
            self.update_rect()





    def about_panel(self):
        self.popbox = BoxLayout()
        self.poplb = MyLabel(text=helpMsg["About"])
        self.poplb.bind(on_ref_press=urlOpen)
        self.popbox.add_widget(self.poplb)

        self.easyPopup(_('About'), self.popbox)

    def show_file(self):
        self.fileDropDown.open(self.ids.fileButton)
        self.fileDropDown.clear_widgets()

        self.fileDropDown.add_widget(Button(text=_("New"), height=48, size_hint_y= None, on_release=lambda a: self.newFile(True)))
        if self.filePath != -1:
            self.fileDropDown.add_widget(Button(text=_("Save"), height=48, size_hint_y= None, on_release=lambda a: self.save(-1, -1)))
        self.fileDropDown.add_widget(Button(text=_("Save as"), height=48, size_hint_y= None, on_release=self.show_save))
        self.fileDropDown.add_widget(Button(text=_("Open"), height=48, size_hint_y= None, on_release=self.show_load))

    def show_port(self):
        self.portDropDown.open(self.ids.port_button)
        self.portDropDown.clear_widgets()

        self.portDropDown.add_widget(Button(text=_("No port"), height=48, size_hint_y= None, on_release=lambda a:self.change_port(-1)))
        arduinoPorts = getPorts()
        for port in arduinoPorts:
            self.portDropDown.add_widget(Button(text=port, height=48, size_hint_y= None, on_release=lambda a:self.change_port(port)))

    def change_port(self, port):
        self.arduino.port = port
        if port != -1:
            self.ids.port_button.text = _("Port") + " " + port
            threading.Thread(target=lambda: self.arduino.checkItHasDirectProgram()).start()
        else:
            self.ids.port_button.text = _("Port")
        self.portDropDown.dismiss()

    def dismiss_popup(self):
        self.popup.dismiss()

    def show_load(self, *args):
        if self.filePath != -1:
            content = LoadDialog(load=self.load, cancel=self.dismiss_popup, path=self.filePath)
        else:
            content = LoadDialog(load=self.load, cancel=self.dismiss_popup, path=self.settings.get('general', 'savePath'))

        self.easyPopup(_("Load file"), content)

    def show_save(self, *args):
        content = SaveDialog(save=self.save, cancel=self.dismiss_popup, path=self.settings.get('general', 'savePath'))
        self.easyPopup(_("Save file"), content)






    def load(self, path, filename):
        try:
            self.config.load(path, filename)
            self.tuyeauGap()
            self.dismiss_popup()
        except Exception as e:
            ctypes.windll.user32.MessageBoxW(0, u"An error occured: \n" + str(e), u"Wrong File Error", 0)

    def save(self, path, filename, *args):
        if path == -1:
            if self.filePath == -1:
                print("no path")
                return
            path = self.filePath
            filename = self.fileName

        self.filePath = path
        self.fileName = filename

        self.config.save(path, filename)
        self.dismiss_popup()





    def chooseAction(self):
        content = ActionChoosing(newAction=self.newAction,
                                 chose=lambda path, filename: threading.Thread(target=lambda: self.uploadPath(path=path, filename=filename)).start(),
                                 actions=self.settings.get('hidden', 'action'),
                                 cancel=lambda: self.easyPopup(_('Upload aborted'), _('Upload has been aborted')))
        self.easyPopup(_("Action program"), content)

    def newAction(self):
        content = LoadDialog(load=lambda path, filename: self.addAction(path, filename))
        self.actionPopup = Popup(title=_("New action program"), content=content,
                            size_hint=(0.9, 0.9))
        content.cancel = self.actionPopup.dismiss
        self.actionPopup.open()

    def addAction(self, path, filename):
        try:
            if ".ino" not in filename[0]:
                ctypes.windll.user32.MessageBoxW(0, u"An error occured: \n The file has to be '.ino'", u"Wrong File Error", 0)
                return
            
            current = json.loads(self.settings.get('hidden', 'action'))
            current[str(filename[0])] = path
            self.settings.set('hidden', 'action', str(json.dumps(current)))
            self.settings.write()

            self.actionPopup.dismiss()
            threading.Thread(target=lambda: self.uploadPath(path=path, filename=filename[0])).start()
        except:
            print("error")


    def uploadPath(self, path, filename):
        try:
            if self.mode == "Pipe":
                trace, pictures, actionNodes = self.config.generatePathFromPipe()
            else:
                trace = self.config.currentConfig["trace"]["value"]
                pictures = self.config.currentConfig["photos"]["value"]
                actionNodes = self.config.currentConfig["actionNodes"]["value"]
                
            cmValues = []
            photos = []

            for i in range(round(len(trace)/2)):
                curent = self.pixelToCM(trace[i*2], trace[i*2+1])
                cmValues.append(curent[1])
                cmValues.append(curent[0])

            for i in range(round(len(trace)/2)):
                photos.append(actionNodes[i])
                if pictures[i]:
                    middles = self.lineToPictures((cmValues[i*2], cmValues[i*2+1]), (cmValues[((i+1)*2)%len(cmValues)], cmValues[((i+1)*2+1)%len(cmValues)]))
                    cmValues[(i+1)*2:(i+1)*2] = middles
                    photos.extend([True for i in range(int(len(middles)/2))])

            genFile = generateFile(cmValues, photos, float(self.settings.get('general', 'stepToCm')), str(osJoinPath(path, filename)))
            f = open(".\\assets\\currentFile\\currentFile.ino","w+")
            f.write(genFile)
            f.close()

            self.arduino.uploadProgram("Current")
        except Exception as e:
            ctypes.windll.user32.MessageBoxW(0, u"An error occured: \n" + str(e), u"Wrong File Error", 0)




    def changedTab(self, *args):
        self.mode = self.ids.tabbedPanel.current_tab.name
        self.zoomFactor = float('inf')

        if self.mode == "Direct" and self.arduino.port != -1:
            self.arduino.checkItHasDirectProgram()
        else:
            self.arduino.stopReading()

        self.update_rect()


    def update_rect(self, *args):
        self.mode = self.ids.tabbedPanel.current_tab.name

        if self.mode == "Pipe":
            middle = (self.ids.pipeDrawing.center_x, self.ids.pipeDrawing.center_y)
            self.ids.pipeDrawing.canvas.before.clear()

            gapsValue = []
            if max(self.sanitize(self.ids.nbPipe.input.text), 1) > 1:
                if bool(self.ids.sameGap.input.active):
                    gapsValue = np.ones(max(self.sanitize(self.ids.nbPipe.input.text), 1)-1) * self.sanitize(self.gaps[0].input.text)
                else:
                    for gap in self.gaps:
                        gapsValue.append(max(self.sanitize(gap.input.text), 0))

            if len(gapsValue) == 0:
                if len(self.config.currentConfig["gaps"]["value"]) > 0:
                    gapsValue = [self.config.currentConfig["gaps"]["value"][0]]
                else:
                    gapsValue = [20]


            self.config.read()
            self.config.currentConfig["gaps"]["value"] = gapsValue

            if self.config.currentConfig["nbPipe"]["value"] <= 2:
                self.ids.sameGap.hide()
            else:
                self.ids.sameGap.show()

            self.ids.pipeSplitter.max_size = self.size[0] - 400
            self.ids.pipeSplitter.min_size = int(round(self.size[0]/2))

            self.ids.pipeBack.canvas.before.clear()

            with self.ids.pipeBack.canvas.before:
                Color(self.background[0], self.background[1], self.background[2], self.background[3])
                Rectangle(pos = self.pos, size = (self.size[0], self.ids.pipeSplitter.size[1]))

            with self.ids.pipeDrawing.canvas.before:
                width = min(self.ids.pipeSplitter.size[0]-50, self.ids.pipeSplitter.size[1]-50)
                height = self.config.currentConfig["lenPipe"]["value"]/self.imageHeight *width

                Color(1,1,1,1)
                Rectangle(source=self.settings.get('colors', 'imagePath'), pos = (middle[0]-width/2, middle[1]-width/2), size = (width, width))

                text = _("Total time") + ": " + str(round( ((self.config.currentConfig["nbPipe"]["value"]*self.config.currentConfig["lenPipe"]["value"])/float(self.speed)) *10)/10) + " sec" + \
                                        "\n"+_("Photo number") + ": " + str( round((self.config.currentConfig["nbPipe"]["value"]*self.config.currentConfig["lenPipe"]["value"])/(self.config.currentConfig["photoPipe"]["value"]/100))) + \
                                        "\n"+_("Photo every") +" "+ str( round( ((float(self.speed)*self.config.currentConfig["nbPipe"]["value"]) / ((self.config.currentConfig["nbPipe"]["value"]*self.config.currentConfig["lenPipe"]["value"]) / (self.config.currentConfig["photoPipe"]["value"]/100)))*10 )/10 ) + " sec"

                Color(0.5,0.5,0.5, .6)
                Rectangle(pos = (self.size[0]-200, self.size[1] - (70 +95)), size = (200, 70))

                label = CoreLabel(text=text, font_size=30, halign='left', valign='top', padding=(5, 5))
                label.refresh()
                text = label.texture
                Color(1, 1, 1, 1)
                Rectangle(pos=(self.size[0]-200, self.size[1] - (70 +95)), size=(200, 70), texture=text)

                ratioX = (width / (self.imageWidth*100)) # Converts cm into pixels
                ratioY = (width / (self.imageHeight*100)) # Converts cm into pixels

                pipeWidth = width/50

                Color(self.pipeColor[0], self.pipeColor[1], self.pipeColor[2], self.pipeColor[3])

                if self.config.currentConfig["horizontal"]["value"]:
                    xPosition = -(width-height)/2 + (self.config.currentConfig["distOriginX"]["value"] + self.imageOrigin[0])*ratioX
                    yPosition = middle[1] - width/2 + (self.config.currentConfig["distOriginY"]["value"] + self.imageOrigin[1])*ratioY

                    Rectangle(pos = (middle[0]-height/2 + xPosition, yPosition), size = (height, pipeWidth))

                    for x in range(self.config.currentConfig["nbPipe"]["value"]-1):
                        yPosition += self.config.currentConfig["gaps"]["value"][x]*ratioY
                        Rectangle(pos = (middle[0]-height/2 + xPosition, yPosition), size = (height, pipeWidth))
                else:
                    xPosition = middle[0] - width/2 + (self.config.currentConfig["distOriginX"]["value"] + self.imageOrigin[0])*ratioX
                    yPosition = -(width-height)/2 + (self.config.currentConfig["distOriginY"]["value"] + self.imageOrigin[1])*ratioY

                    Rectangle(pos = (xPosition, middle[1]-height/2 + yPosition), size = (pipeWidth, height))

                    for x in range(self.config.currentConfig["nbPipe"]["value"]-1):
                        xPosition += self.config.currentConfig["gaps"]["value"][x]*ratioX
                        Rectangle(pos = (xPosition, middle[1]-height/2 + yPosition), size = (pipeWidth, height))

        elif self.mode == "Free":
            self.ids.libreSplitter.max_size = self.size[0] - 400
            self.zoomClamp()
            middle = (self.ids.libreDrawing.center_x, self.ids.libreDrawing.center_y)
            self.ids.libreDrawing.canvas.before.clear()

            self.ids.libreSplitter.min_size = int(round(self.size[0]/2))
            zoomedTrace = np.multiply(self.config.currentConfig["trace"]["value"], self.zoomFactor).tolist()

            self.ids.freeBack.canvas.before.clear()

            self.config.read()

            with self.ids.freeBack.canvas.before:
                Color(self.background[0], self.background[1], self.background[2], self.background[3])
                Rectangle(pos = self.pos, size = (self.size[0], self.ids.libreSplitter.size[1]))

            with self.ids.libreDrawing.canvas.before:
                width = 200 * self.zoomFactor
                Rectangle(source=self.settings.get('colors', 'imagePath'), pos = (middle[0]-width/2, middle[1]-width/2), size = (width, width))
                dist = 0

                if keyboard.is_pressed("shift"):
                    for corner in self.corners:
                        Color(0, 1, 0, 0.8)
                        Ellipse(pos=(corner[0]*self.zoomFactor+middle[0]-self.diametre/2, corner[1]*self.zoomFactor+middle[1]-self.diametre/2), size=(self.diametre, self.diametre))

                if len(zoomedTrace) > 0:
                    if len(zoomedTrace) > 4:
                        isLoop = bool(self.ids.loop.input.active)
                    else:
                        isLoop = False
                    
                    self.config.currentConfig["loop"]["value"] = isLoop

                    for i in range(int(len(zoomedTrace)/2)):
                        if (i+1)*2+1 >= len(zoomedTrace) and isLoop:
                            if self.config.currentConfig["photos"]["value"][i]: Color(self.pathHighlight[0], self.pathHighlight[1], self.pathHighlight[2], self.pathHighlight[3])
                            else: Color(self.pathColor[0], self.pathColor[1], self.pathColor[2], self.pathColor[3])
                            Line(points=[zoomedTrace[i*2]+middle[0], zoomedTrace[i*2+1]+middle[1], zoomedTrace[0]+middle[0], zoomedTrace[1]+middle[1]], width=self.lineWidth)
                            thisDist = max(distance.euclidean(self.pixelToCM(self.config.currentConfig["trace"]["value"][i*2]+middle[0], self.config.currentConfig["trace"]["value"][i*2+1]+middle[1]),
                                                        self.pixelToCM(self.config.currentConfig["trace"]["value"][0]+middle[0], self.config.currentConfig["trace"]["value"][1]+middle[1])), 0.0001)
                            dist += thisDist
                            if self.config.currentConfig["photos"]["value"][i]:
                                nb = floor(thisDist/float(self.config.currentConfig["photoPipe"]["value"]))
                                top = (thisDist-nb*float(self.config.currentConfig["photoPipe"]["value"]))/(2*thisDist)
                                ax = top * ((zoomedTrace[i*2]+middle[0]) - (zoomedTrace[0]+middle[0]))
                                ay = top * ((zoomedTrace[i*2+1]+middle[1]) - (zoomedTrace[1]+middle[1]))
                                Color(0, 0, 0)
                                for p in range(nb+1):
                                    Ellipse(pos=(zoomedTrace[0]+middle[0] + ax-self.lineWidth/2 + ((float(self.config.currentConfig["photoPipe"]["value"])/thisDist)*((zoomedTrace[i*2]+middle[0]) - (zoomedTrace[0]+middle[0])))*p,
                                                 zoomedTrace[1]+middle[1] + ay-self.lineWidth/2 + ((float(self.config.currentConfig["photoPipe"]["value"])/thisDist)*((zoomedTrace[i*2+1]+middle[1]) - (zoomedTrace[1]+middle[1])))*p), size=(self.lineWidth, self.lineWidth))

                        elif (i+1)*2+1 < len(zoomedTrace):
                            if self.config.currentConfig["photos"]["value"][i]: Color(self.pathHighlight[0], self.pathHighlight[1], self.pathHighlight[2], self.pathHighlight[3])
                            else: Color(self.pathColor[0], self.pathColor[1], self.pathColor[2], self.pathColor[3])
                            Line(points=[zoomedTrace[i*2]+middle[0], zoomedTrace[i*2+1]+middle[1], zoomedTrace[(i+1)*2]+middle[0], zoomedTrace[(i+1)*2+1]+middle[1]], width=self.lineWidth)
                            thisDist = max(distance.euclidean(self.pixelToCM(self.config.currentConfig["trace"]["value"][i*2]+middle[0], self.config.currentConfig["trace"]["value"][i*2+1]+middle[1]),
                                                        self.pixelToCM(self.config.currentConfig["trace"]["value"][(i+1)*2]+middle[0], self.config.currentConfig["trace"]["value"][(i+1)*2+1]+middle[1])), 0.0001)
                            dist += thisDist
                            if self.config.currentConfig["photos"]["value"][i]:
                                nb = floor(thisDist/float(self.config.currentConfig["photoPipe"]["value"]))
                                top = (thisDist-nb*float(self.config.currentConfig["photoPipe"]["value"]))/(2*thisDist)
                                ax = top * (zoomedTrace[i*2] - zoomedTrace[(i+1)*2])
                                ay = top * (zoomedTrace[i*2+1] - zoomedTrace[(i+1)*2+1])
                                Color(0, 0, 0)
                                for p in range(nb+1):
                                    Ellipse(pos=(zoomedTrace[(i+1)*2]+middle[0] + ax-self.lineWidth/2 + ((float(self.config.currentConfig["photoPipe"]["value"])/thisDist)*(zoomedTrace[i*2] - zoomedTrace[(i+1)*2]))*p,
                                                 zoomedTrace[(i+1)*2+1]+middle[1] + ay-self.lineWidth/2 + ((float(self.config.currentConfig["photoPipe"]["value"])/thisDist)*(zoomedTrace[i*2+1] - zoomedTrace[(i+1)*2+1]))*p), size=(self.lineWidth, self.lineWidth))
                                
                    
                    for i in range(int(len(zoomedTrace)/2)):
                        if self.lastTouched == i:
                            Color(self.nodeHighlight[0], self.nodeHighlight[1], self.nodeHighlight[2], self.nodeHighlight[3])
                            Ellipse(pos=(zoomedTrace[i*2]+middle[0]-(self.diametre+5)/2, zoomedTrace[i*2+1]+middle[1]-(self.diametre+5)/2), size=(self.diametre+5, self.diametre+5))
                        if self.config.currentConfig["actionNodes"]["value"][i]:
                            Color(self.actionNode[0], self.actionNode[1], self.actionNode[2], self.actionNode[3])
                        else:
                            Color(self.nodeColor[0], self.nodeColor[1], self.nodeColor[2], self.nodeColor[3])
                        Ellipse(pos=(zoomedTrace[i*2]+middle[0]-self.diametre/2, zoomedTrace[i*2+1]+middle[1]-self.diametre/2), size=(self.diametre, self.diametre))
                        label = CoreLabel(text=str(i+1), font_size=20)
                        label.refresh()
                        text = label.texture
                        Color(0, 0, 0, 1)
                        Ellipse(pos=(zoomedTrace[i*2]+middle[0]-self.diametre/2, zoomedTrace[i*2+1]+middle[1]-self.diametre/2), size=(self.diametre, self.diametre), texture=text)

                text = "Total time: 5 sec\nPhoto number: 10\nDistance: "+str(round(dist*10)/10)+" cm"

                Color(1,1,1, .2)
                Rectangle(pos = (self.size[0]-200, self.size[1] - (70 +95)), size = (200, 70))

                label = CoreLabel(text=text, font_size=30, halign='left', valign='top', padding=(5, 5))
                label.refresh()
                text = label.texture
                Color(1, 1, 1, 1)
                Rectangle(pos=(self.size[0]-200, self.size[1] - (70 +95)), size=(200, 70), texture=text)

        elif self.mode == "Direct":
            #self.ids.directDrawing.center_x
            realMiddle = (self.ids.directDrawing.center_x, self.ids.directDrawing.center_y)
            middle = (self.ids.directSplitter.size[0]-(self.ids.directSplitter.size[0]*(3/5))/2, self.ids.directDrawing.center_y)
            switchMiddle = ((self.ids.directSplitter.size[0]*(2/5))/2, self.ids.directDrawing.center_y)

            self.ids.directDrawing.clear_widgets()
            self.ids.directDrawing.canvas.before.clear()
            self.ids.directDrawing.canvas.after.clear()

            buttonSize = min(self.ids.directSplitter.size[0]/4, self.ids.directSplitter.size[1]/4)
            fontSize = min(self.ids.directSplitter.size[0]/20, self.ids.directSplitter.size[1]/20)

            buttons = {_("Origin"): {"value": [0, 8], "position": [0, 0]},
                        u'\u23E9': {"value": [1, 5], "position": [1, 0]},
                        u'\u23EA': {"value": [2, 5], "position": [-1, 0]},
                        u'\u23EB': {"value": [3, 6], "position": [0, 1]},
                        u'\u23EC': {"value": [4, 6], "position": [0, -1]}}

            for button in buttons:
                but = Button(text=button, font_size=fontSize, font_name=self.font,
                             pos = (middle[0]-buttonSize/2+(buttonSize+5)*buttons[button]["position"][0], middle[1]-buttonSize/2+(buttonSize+5)*buttons[button]["position"][1]),
                             size = (buttonSize, buttonSize))
                but.bind(on_press=partial(self.arduino.sendSerial, bytes([buttons[button]["value"][0]])))
                but.bind(on_release=partial(self.arduino.sendSerial, bytes([buttons[button]["value"][1]])))
                self.ids.directDrawing.add_widget(but)

            self.ids.directBack.canvas.before.clear()

            with self.ids.directBack.canvas.before:
                Color(self.background[0], self.background[1], self.background[2], self.background[3])
                Rectangle(pos = self.pos, size = (self.size[0], self.ids.directSplitter.size[1]))

            with self.ids.directDrawing.canvas.before:
                text = "X: " + str(round(float(self.arduino.systemPosition[0])/float(self.settings.get('general', 'stepToCm'))*10)/10) + " "+_("cm") + \
                        "\nY: " + str(round(float(self.arduino.systemPosition[1])/float(self.settings.get('general', 'stepToCm'))*10)/10) + " "+("cm")

                Color(1,1,1, .2)
                Rectangle(pos = (self.size[0]-200, self.size[1] - (70 +95)), size = (200, 70))

                label = CoreLabel(text=text, font_size=30, halign='left', valign='top', padding=(5, 5))
                label.refresh()
                text = label.texture
                Color(1, 1, 1, 1)
                Rectangle(pos=(self.size[0]-200, self.size[1] - (70 +95)), size=(200, 70), texture=text)

                switches = self.arduino.systemSwitchs
                for switch in switches:
                    if switches[switch]['value']: Color(0, 0, 0)
                    else: Color(1, 1, 0)
                    Ellipse(pos=(switchMiddle[0] - self.switchDiameter / 2 + switchMiddle[0]/2*switches[switch]['position'][0],
                                 switchMiddle[1] - self.switchDiameter / 2 - switchMiddle[1]/2*switches[switch]['position'][1]),
                                 size=(self.switchDiameter, self.switchDiameter))
                    
            if not self.arduino.hasDirectProgram:
                with self.ids.directDrawing.canvas.after:
                    dimensionX = self.ids.directSplitter.size[0]
                    dimensionY = self.ids.directSplitter.size[1] - 50
                    Color(1, 1, 1, 0.7)
                    Rectangle(pos=(realMiddle[0]-dimensionX/2, realMiddle[1]-dimensionY/2), size=(dimensionX, dimensionY))
                    label = CoreLabel(text=_("Click on 'Upload' before sending serial data"), font_size=100, halign='middle', valign='middle', padding=(12, 12))
                    label.refresh()
                    text = label.texture
                    Color(0, 0, 0, 1)
                    Rectangle(pos=(realMiddle[0]-dimensionX/2, realMiddle[1]-(dimensionX*(3/16))/2), size=(dimensionX, dimensionX*(3/16)), texture=text)

    def removeNode(self):
        if self.lastTouched != -1:
            del self.config.currentConfig["trace"]["value"][self.lastTouched*2+1]
            del self.config.currentConfig["trace"]["value"][self.lastTouched*2]
            del self.config.currentConfig["photos"]["value"][self.lastTouched]
            del self.config.currentConfig["actionNodes"]["value"][self.lastTouched]
            self.lastTouched = -1
            self.update_rect()

    def clickedDown(self, touch):
        if self.mode == "Free":
            x = touch.x
            y = touch.y
            zoomedTrace = np.multiply(self.config.currentConfig["trace"]["value"], self.zoomFactor).tolist()

            if self.ids.libreDrawing.collide_point(x, y):
                # Updates zooming depending on the mouse wheel
                if touch.is_mouse_scrolling:
                    dist = 0.1 if touch.button == 'scrollup' else -0.1
                    self.zoomFactor += dist
                    self.zoomClamp()
                    self.update_rect()

                # Checks if the user right clicked on a node, if yes remove it
                for i in range(int(len(zoomedTrace)/2)):
                    if hypot(zoomedTrace[i*2]+self.ids.libreDrawing.center_x - x, zoomedTrace[i*2+1]+self.ids.libreDrawing.center_y - y) <= self.diametre/2:
                        if touch.button == 'right':
                            self.config.currentConfig["actionNodes"]["value"][i] = not self.config.currentConfig["actionNodes"]["value"][i]
                            self.update_rect()
                        elif touch.button == 'left':
                            self.isDragging = i
                            self.lastTouched = i
                            self.printCoords(self.config.currentConfig["trace"]["value"][i*2], self.config.currentConfig["trace"]["value"][i*2+1])
                            self.update_rect()
                        return

                # Check if we clicked on a line or not
                for i in range(int(len(zoomedTrace)/2)-1):
                    firstPoint = (zoomedTrace[i*2]+self.ids.libreDrawing.center_x, zoomedTrace[i*2+1]+self.ids.libreDrawing.center_y)
                    secondPoint = (zoomedTrace[(i+1)*2]+self.ids.libreDrawing.center_x, zoomedTrace[(i+1)*2+1]+self.ids.libreDrawing.center_y)
                    if hitLine(firstPoint, secondPoint, (x, y), self.lineWidth):
                        if touch.button == 'right':
                            self.config.currentConfig["photos"]["value"][i] = not self.config.currentConfig["photos"]["value"][i]
                            self.lastTouched = -1
                            self.update_rect()
                            return
                        elif touch.button == 'left':
                            coordX = (x-self.ids.libreDrawing.center_x)/self.zoomFactor
                            coordY = (y-self.ids.libreDrawing.center_y)/self.zoomFactor

                            self.printCoords(coordX,coordY)

                            self.config.currentConfig["trace"]["value"].insert((i+1)*2, coordX)
                            self.config.currentConfig["trace"]["value"].insert((i+1)*2+1, coordY)
                            self.config.currentConfig["photos"]["value"].insert((i+1), False)
                            self.config.currentConfig["actionNodes"]["value"].insert((i+1), False)
                            self.lastTouched = i+1
                            self.isDragging = i+1
                            self.update_rect()
                            return
                if touch.button == 'right':
                    if bool(self.ids.loop.input.active) and len(zoomedTrace) > 1:
                        firstPoint = (zoomedTrace[len(zoomedTrace)-2]+self.ids.libreDrawing.center_x, zoomedTrace[len(zoomedTrace)-1]+self.ids.libreDrawing.center_y)
                        secondPoint = (zoomedTrace[0]+self.ids.libreDrawing.center_x, zoomedTrace[1]+self.ids.libreDrawing.center_y)
                        if hitLine(firstPoint, secondPoint, (x, y), self.lineWidth):
                            self.config.currentConfig["photos"]["value"][len(self.config.currentConfig["photos"]["value"])-1] = not self.config.currentConfig["photos"]["value"][len(self.config.currentConfig["photos"]["value"])-1]
                            self.update_rect()

                # Adds a new node where the user clicked
                if touch.button == 'left':
                    coordX = (x-self.ids.libreDrawing.center_x)/self.zoomFactor
                    coordY = (y-self.ids.libreDrawing.center_y)/self.zoomFactor

                    self.printCoords(coordX, coordY)

                    self.config.currentConfig["trace"]["value"].append(coordX)
                    self.config.currentConfig["trace"]["value"].append(coordY)
                    self.config.currentConfig["photos"]["value"].append(False)
                    self.config.currentConfig["actionNodes"]["value"].append(False)
                    self.lastTouched = len(self.config.currentConfig["photos"]["value"])-1
                    self.isDragging = len(self.config.currentConfig["photos"]["value"])-1
                    self.update_rect()
                    return

    def clickedUp(self, touch):
        if self.mode == "Free":
            if touch.button == 'left':
                self.isDragging = -1
            if self.zoomFactor == 0.05:
                self.positionClamp()
                self.update_rect()
            self.undoRedo.do([self.config.currentConfig["trace"]["value"].copy(), self.config.currentConfig["photos"]["value"].copy(), self.config.currentConfig["actionNodes"]["value"].copy()])

    def clickedMove(self, touch):
        if self.mode == "Free":
            newPosition = -1
            if touch.button == 'left' and self.isDragging != -1:
                thisX = (touch.x-self.ids.libreDrawing.center_x)/self.zoomFactor
                thisY = (touch.y-self.ids.libreDrawing.center_y)/self.zoomFactor

                if keyboard.is_pressed("ctrl") and len(self.config.currentConfig["trace"]["value"]) > 2: # To clamp relative to last one (right angles)
                    fromWhich = self.isDragging-1 % len(self.config.currentConfig["trace"]["value"])
                    previousPoint = (self.config.currentConfig["trace"]["value"][(fromWhich)*2], self.config.currentConfig["trace"]["value"][(fromWhich)*2+1])
                    dist = distance.euclidean(previousPoint, (thisX, thisY))
                    angle = round(atan2(thisY-previousPoint[1], thisX-previousPoint[0])/ (pi/4)) * (pi/4)

                    position = (cos(angle)*dist+previousPoint[0], sin(angle)*dist + previousPoint[1])
                    newPosition = (position[0], position[1])
                
                elif keyboard.is_pressed("shift"): # To clamp to the corners (origin, top-right, ...)
                    dist1 = distance.euclidean(self.corners[0], (thisX, thisY))
                    dist2 = distance.euclidean(self.corners[1], (thisX, thisY))
                    dist3 = distance.euclidean(self.corners[2], (thisX, thisY))
                    dist4 = distance.euclidean(self.corners[3], (thisX, thisY))

                    indice = np.argmin(np.array([dist1, dist2, dist3, dist4]))
                    newPosition = (self.corners[indice][0], self.corners[indice][1])

                else:
                    newPosition = (thisX, thisY)

                if newPosition != -1:
                    self.printCoords(newPosition[0], newPosition[1])

                    self.config.currentConfig["trace"]["value"][self.isDragging*2] = newPosition[0]
                    self.config.currentConfig["trace"]["value"][self.isDragging*2+1] = newPosition[1]

                    self.lastTouched = self.isDragging

                self.update_rect()

    def pixelToCM(self, X, Y):
        height = self.corners[0][1] - self.corners[1][1]
        width = self.corners[0][0] - self.corners[2][0]
        return (round(((X-self.corners[3][0])*(self.actualWidth*1000))/width)/10, round(((Y-self.corners[3][1])*(self.actualHeight*1000))/height)/10)

    def lineToPictures(self, b, a):
        """Transforms a line in a multitude of points where a picture has to be taken.

        a tuple: first point of the line (in cm).
        b tuple: second point of the line (in cm).

        returns: an array of the NEW points.
        """
        thisDist = max(distance.euclidean(a, b), 0.0001)
        newPoints = []

        nb = floor(thisDist/float(self.config.currentConfig["photoPipe"]["value"]))
        top = (thisDist-nb*float(self.config.currentConfig["photoPipe"]["value"]))/(2*thisDist)

        ax = top * (a[0] - b[0])
        ay = top * (a[1] - b[1])
        for p in range(nb+1):
            newPoints.append(round((b[0] + ax + ( (float(self.config.currentConfig["photoPipe"]["value"])/thisDist)*(a[0] - b[0]) )*p)*100)/100)
            newPoints.append(round((b[1] + ay + ( (float(self.config.currentConfig["photoPipe"]["value"])/thisDist)*(a[1] - b[1]) )*p)*100)/100)

        return newPoints

    def printCoords(self, X, Y):
        toCm = self.pixelToCM(X, Y)

        self.ids.coord.unbindThis()
        self.ids.coord.input.text = str(toCm[0]) + " : " + str(toCm[1])
        self.ids.coord.bindThis()
    
    def removeAllNodes(self):
        self.config.currentConfig["trace"]["value"] = []
        self.config.currentConfig["photos"]["value"] = []
        self.config.currentConfig["actionNodes"]["value"] = []
        self.undoRedo.do([self.config.currentConfig["trace"]["value"].copy(), self.config.currentConfig["photos"]["value"].copy(), self.config.currentConfig["actionNodes"]["value"].copy()])
        self.update_rect()

    def inputMove(self, *args):
        position = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", self.ids.coord.input.text)

        height = self.corners[0][1] - self.corners[1][1]
        width = self.corners[0][0] - self.corners[2][0]

        ratioX = width / (self.actualWidth*100)
        ratioY = height / (self.actualHeight*100)

        if len(position) == 2:
            if self.lastTouched == -1:
                self.config.currentConfig["trace"]["value"].append(float(position[0])*ratioX + self.corners[3][0])
                self.config.currentConfig["trace"]["value"].append(float(position[1])*ratioY + self.corners[3][1])
                self.config.currentConfig["photos"]["value"].append(False)
                self.config.currentConfig["actionNodes"]["value"].append(False)
                self.lastTouched = len(self.config.currentConfig["photos"]["value"]) -1
            elif self.lastTouched*2+1 < len(self.config.currentConfig["trace"]["value"]):
                self.config.currentConfig["trace"]["value"][self.lastTouched*2] = float(position[0])*ratioX + self.corners[3][0]
                self.config.currentConfig["trace"]["value"][self.lastTouched*2+1] = float(position[1])*ratioY + self.corners[3][1]

            self.update_rect()

    def positionClamp(self):
        maxPosLeft = (-self.ids.libreSplitter.size[0]/2-self.innerScreenMargin[0])/(self.zoomFactor)
        maxPosRight = (self.ids.libreSplitter.size[0]/2-self.innerScreenMargin[1])/(self.zoomFactor)
        maxPosTop = (self.ids.libreSplitter.size[1]/2-self.innerScreenMargin[2])/(self.zoomFactor)
        maxPosDown = (-self.ids.libreSplitter.size[1]/2-self.innerScreenMargin[3])/(self.zoomFactor)

        for i in range(int(len(self.config.currentConfig["trace"]["value"])/2)):
            self.config.currentConfig["trace"]["value"][i*2] = min(max(self.config.currentConfig["trace"]["value"][i*2], maxPosLeft), maxPosRight)
            self.config.currentConfig["trace"]["value"][i*2+1] = min(max(self.config.currentConfig["trace"]["value"][i*2+1], maxPosDown), maxPosTop)
                
    def zoomClamp(self):
        size = self.ids.libreSplitter.size
        worstX = 0
        worstY = 0
        worstMX = 0
        worstMY = 0
        for i in range(int(len(self.config.currentConfig["trace"]["value"])/2)):
            if self.config.currentConfig["trace"]["value"][i*2] > worstX:
                worstX = self.config.currentConfig["trace"]["value"][i*2]
            elif self.config.currentConfig["trace"]["value"][i*2] < worstMX:
                worstMX = self.config.currentConfig["trace"]["value"][i*2]
            if self.config.currentConfig["trace"]["value"][i*2+1] > worstY:
                worstY = self.config.currentConfig["trace"]["value"][i*2+1]
            elif self.config.currentConfig["trace"]["value"][i*2+1] < worstMY:
                worstMY = self.config.currentConfig["trace"]["value"][i*2+1]

        if worstX*self.zoomFactor > size[0]/2 - self.innerScreenMargin[1]:
            self.zoomFactor = (size[0]/2 - self.innerScreenMargin[1])/float(worstX)
        if worstY*self.zoomFactor > size[1]/2 - self.innerScreenMargin[2]:
            self.zoomFactor = min((size[1]/2 - self.innerScreenMargin[2])/float(worstY), self.zoomFactor)
        if worstMX*self.zoomFactor < -size[0]/2 - self.innerScreenMargin[0]:
            self.zoomFactor = min((-size[0]/2 - self.innerScreenMargin[0])/float(worstMX), self.zoomFactor)
        if worstMY*self.zoomFactor < -size[1]/2 - self.innerScreenMargin[3]:
            self.zoomFactor = min((-size[1]/2 - self.innerScreenMargin[3])/float(worstMY), self.zoomFactor)

        if 100*self.zoomFactor > size[0]/2:
            self.zoomFactor = min((size[0]/2)/float(100), self.zoomFactor)
        if 100*self.zoomFactor > size[1]/2 - 20:
            self.zoomFactor = min((size[1]/2 - 20)/float(100), self.zoomFactor)

        self.zoomFactor = max(self.zoomFactor, 0.05)
    
    def tuyeauGap(self, *args):
        if self.gaps != []:
            for gap in self.gaps:
                self.pipePanel.remove_widget(gap)

        if self.sanitize(self.ids.nbPipe.input.text) < 2:
            self.update_rect()
            return

        if bool(self.ids.sameGap.input.active):
            self.gaps = [Input(inputName=_('Gap between pipes')+" (cm)", input_filter="float", default_text=str(self.config.currentConfig["gaps"]["value"][0]), callback=self.update_rect)]
            self.pipePanel.add_widget(self.gaps[0])
        else:
            self.gaps = []
            for pipe in range(max(self.sanitize(self.ids.nbPipe.input.text), 2)-1):
                try:
                    default = str(self.config.currentConfig["gaps"]["value"][pipe])
                except:
                    default = str(self.config.currentConfig["gaps"]["value"][0])   

                self.gaps.append(Input(inputName=_('Gap between pipes ')+str(pipe+1)+"-"+str(pipe+2)+" (cm)", input_filter="float", default_text=default, callback=self.update_rect))
                self.pipePanel.add_widget(self.gaps[pipe])
        self.update_rect()

    def freeToPipe(self):
        self.ids.photoPipe.unbindThis()
        self.ids.photoPipe.input.text = str(max(self.sanitize(self.ids.freePhotoPipe.input.text), 1))
        self.ids.photoPipe.bindThis()
        self.update_rect()

    def pipeToFree(self):
        self.ids.freePhotoPipe.unbindThis()
        self.ids.freePhotoPipe.input.text = str(max(self.sanitize(self.ids.photoPipe.input.text), 1))
        self.ids.freePhotoPipe.bindThis()
        self.update_rect()        

    #TODO: transform in decorator
    def sanitize(self, number):
        """Avoids getting errors on empty inputs.

        number string||float||int: the value to sanitize.

        returns: 0 if it is NaN, otherwise the value itself.
        """
        try:
            return int(number)
        except:
            try:
                return float(number)
            except:
                return 0

    def copyToClipboard(self):
        if self.mode == "Direct":
            print("Copied")
            pyperclip.copy(str(self.arduino.systemPosition))

    def undo(self):
        last = self.undoRedo.undo([self.config.currentConfig["trace"]["value"].copy(), self.config.currentConfig["photos"]["value"].copy(), self.config.currentConfig["actionNodes"]["value"].copy()])
        if last != -1:
            self.config.currentConfig["trace"]["value"] = last[0]
            self.config.currentConfig["photos"]["value"] = last[1]
            self.config.currentConfig["actionNodes"]["value"] = last[2]
        self.update_rect()

    def easyPopup(self, title, content, auto_dismiss=True):
        if isinstance(content, str):
            content = Label(text=content)

        try: self.popup.dismiss()
        except: pass
        self.popup = Popup( title=title,
                            content=content,
                            size_hint=(None, None),
                            size=(400, 300))
        self.popup.open()
