import ctypes
import json
import math
import os
import re
import threading
from ast import literal_eval as make_tuple
from os.path import join as osJoinPath

import keyboard
import kivy.utils as utils
import numpy as np
import pyperclip
from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from scipy.spatial import distance

from .arduinoMega import Arduino
from .classes import (ActionChoosing, Input, LoadDialog, MenuDropDown,
                      SaveDialog, MyLabel)
from .config import Config
from .createFile import generateFile
from .helpMsg import helpMsg
from .localization import _
from .undoRedo import UndoRedo
from .utilityFunctions import checkUpdates, getPorts, hitLine, urlOpen


class Parametrage(BoxLayout):
    def __init__(self, *args, **kwargs):
        super(Parametrage, self).__init__(*args, **kwargs)
        self.settings = App.get_running_app().config
        self.font = ".\\assets\\seguisym.ttf"
        self.mode = self.settings.get('hidden', 'starting')  # Stores the current mode
        self.portDropDown = MenuDropDown()
        self.fileDropDown = MenuDropDown()
        self.undoRedo = UndoRedo()
        self.arduino = Arduino(self.settings, self.easyPopup, self.update_rect, programs={
            "Direct":
            {"isDirectProgram": True, "path": osJoinPath(os.path.normpath(os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir), "directFile\\directFile.ino")},
            "Current":
            {"isDirectProgram": False, "path": osJoinPath(os.path.normpath(os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir), "currentFile\\currentFile.ino")}})

        self.imageWidth = float(self.settings.get('hidden', 'imWidth'))  # in meter
        self.imageHeight = float(self.settings.get('hidden', 'imHeight'))  # in meter
        self.actualWidth = float(self.settings.get('hidden', 'acWidth'))  # in meter
        self.actualHeight = float(self.settings.get('hidden', 'acHeight'))  # in meter
        self.imageOrigin = make_tuple(self.settings.get('hidden', 'origin'))  # in cm
        self.popup = -1

        # Specific to the mode 'Pipe'
        self.pipePanel = self.ids.tuyeauInputs
        self.gaps = []

        # Specific to the mode 'Free'
        self.lineWidth = float(self.settings.get('colors', 'lineWidth'))
        self.diametre = float(self.settings.get('colors', 'nodeDiam'))
        self.isDragging = -1
        self.lastTouched = -1
        self.zoomFactor = 1
        self.innerScreenMargin = [-self.diametre/2-5, self.diametre/2+5, self.diametre/2+25, -self.diametre/2-25]  # Left, Right, Top, Down
        self.corners = [(88, 82), (88, -72), (-75, 82), (-75, -72)]  # Right-Top, Right-Down, Left-Top, Left-Down

        # Specific to the mode 'direct'
        self.switchDiameter = float(self.settings.get('colors', 'switchDiam'))

        Clock.schedule_once(self.binding)
        Clock.schedule_interval(lambda a: self.save(-1, -1), int(self.settings.get('general', 'autoSave')*60))

        keyboard.on_release_key(self.settings.get('shortcuts', 'corner'), self.update_rect)

    def binding(self, *args):
        self.ids.pipeDrawing.bind(size=self.update_rect, pos=self.update_rect)
        self.ids.directDrawing.bind(size=self.update_rect, pos=self.update_rect)
        self.ids.libreDrawing.bind(size=self.update_rect, pos=self.update_rect)
        self.ids.changeTab.bind(on_touch_up=self.changedTab)
        self.config = Config({
            "nbPipe": {"value": 2, "inputs": [self.ids.nbPipe]},
            "lenPipe": {"value": 0.9, "inputs": [self.ids.lenPipe]},
            "photoPipe": {"value": 10, "inputs": [self.ids.photoPipe]},
            "distOriginX": {"value": 5, "inputs": [self.ids.distOriginX]},
            "distOriginY": {"value": 5, "inputs": [self.ids.distOriginY]},
            "sameGap": {"value": True, "inputs": [self.ids.sameGap]},
            "horizontal": {"value": False, "inputs": [self.ids.horizontal]},
            "gaps": {"value": [20], "inputs": []},
            "loop": {"value": True, "inputs": [self.ids.loop]},
            "trace": {"value": [], "inputs": []},
            "photos": {"value": [], "inputs": []},
            "actionNodes": {"value": [], "inputs": []}
        },
            self.cmToPixel,
            self.pixelToCM
        )
        self.updateColors(refresh=False)

        self.freePic = Rectangle(source=self.settings.get('colors', 'imagePath'), pos=(0, 0), size=(100, 100))
        self.ids.libreDrawing.canvas.before.add(self.freePic)

        self.pipePic = Rectangle(source=self.settings.get('colors', 'imagePath'), pos=(0, 0), size=(100, 100))
        self.ids.pipeDrawing.canvas.before.add(self.pipePic)

        self.newFile(True)

        checkUpdates(self.settings.get('hidden', 'version'), self.easyPopup)

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

    def help(self, *args):
        self.easyPopup(_('Help'), helpMsg[self.mode])

    def newFile(self, refresh, *args):
        self.filePath = -1
        self.fileName = _("configuration")
        self.config.reset()

        if refresh:
            self.tuyeauGap()

    def about_panel(self):
        self.easyPopup(_('About'), helpMsg["About"])

    def show_file(self):
        self.fileDropDown.open(self.ids.fileButton)
        self.fileDropDown.clear_widgets()

        self.fileDropDown.add_widget(Button(text=_("New"), height=48, size_hint_y=None, on_release=lambda a: self.newFile(True)))
        if self.filePath != -1:
            self.fileDropDown.add_widget(Button(text=_("Save"), height=48, size_hint_y=None, on_release=lambda a: self.save(-1, -1)))
        self.fileDropDown.add_widget(Button(text=_("Save as"), height=48, size_hint_y=None, on_release=self.show_save))
        self.fileDropDown.add_widget(Button(text=_("Open"), height=48, size_hint_y=None, on_release=self.show_load))

    def show_port(self):
        self.portDropDown.open(self.ids.port_button)
        self.portDropDown.clear_widgets()

        self.portDropDown.add_widget(Button(text=_("No port"), height=48, size_hint_y=None, on_release=lambda a: self.change_port(-1)))
        arduinoPorts = getPorts()
        for port in arduinoPorts:
            self.portDropDown.add_widget(Button(text=port, height=48, size_hint_y=None, on_release=lambda a, port=port: self.change_port(port)))

    def change_port(self, port):
        self.arduino.port = port
        self.ids.port_button.text = _("Port")
        if port != -1:
            self.ids.port_button.text = _("Port") + " " + port
            threading.Thread(target=lambda: self.arduino.checkItHasDirectProgram()).start()

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
        except Exception as e:
            ctypes.windll.user32.MessageBoxW(0, u"An error occured: \n" + str(e), u"Wrong File Error", 0)
        self.dismiss_popup()

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
                                 suppress=self.suppressAction,
                                 actions=self.settings.get('hidden', 'action'),
                                 cancel=lambda: self.easyPopup(_('Upload aborted'), _('Upload has been aborted')))
        self.easyPopup(_("Action program"), content)

    def suppressAction(self, filename):
        current = json.loads(self.settings.get('hidden', 'action'))
        del current[str(filename)]
        self.settings.set('hidden', 'action', str(json.dumps(current)))
        self.settings.write()
        return current

    def newAction(self):
        content = LoadDialog(load=lambda path, filename: self.addAction(path, filename))
        self.actionPopup = Popup(title=_("New action program"), content=content, size_hint=(0.9, 0.9))
        content.cancel = self.actionPopup.dismiss
        self.actionPopup.open()

    def addAction(self, path, filename):
        if ".ino" not in filename[0]:
            ctypes.windll.user32.MessageBoxW(0, u"An error occured: \n The file has to be '.ino'", u"Wrong File Error", 0)
            return

        current = json.loads(self.settings.get('hidden', 'action'))
        current[str(filename[0])] = path
        self.settings.set('hidden', 'action', str(json.dumps(current)))
        self.settings.write()

        self.actionPopup.dismiss()

        threading.Thread(target=lambda: self.uploadPath(path=path, filename=filename[0])).start()

    def uploadPath(self, path, filename):
        trace = self.config.currentConfig["trace"]["value"]
        pictures = self.config.currentConfig["photos"]["value"]
        actionNodes = self.config.currentConfig["actionNodes"]["value"]
        loop = self.config.currentConfig["loop"]["value"]

        if self.mode == "Pipe":
            trace, pictures, actionNodes = self.config.generatePathFromPipe()
            loop = True

        unraveld = self.config.unravelPath(trace, pictures, actionNodes)

        genFile = generateFile(unraveld[0], unraveld[1], float(self.settings.get('general', 'stepToCm')), loop, str(osJoinPath(path, filename)))
        f = open(osJoinPath(os.path.normpath(os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir), "currentFile\\currentFile.ino"), "w+")
        f.write(genFile)
        f.close()

        self.arduino.uploadProgram("Current")

    def changedTab(self, *args):
        self.mode = self.ids.tabbedPanel.current_tab.name
        self.zoomFactor = float('inf')
        self.arduino.stopReading()

        if self.mode == "Direct" and self.arduino.port != -1:
            print("changedTab")
            self.arduino.checkItHasDirectProgram()

        self.update_rect()

    def update_rect(self, *args):
        self.mode = self.ids.tabbedPanel.current_tab.name

        if self.mode == "Pipe":
            middle = (self.ids.pipeDrawing.center_x, self.ids.pipeDrawing.center_y)
            self.ids.pipeDrawing.canvas.clear()
            self.ids.pipeBack.canvas.before.clear()

            self.config.read(self.gaps)
            self.ids.sameGap.show()

            if self.config.currentConfig["nbPipe"]["value"] <= 2:
                self.ids.sameGap.hide()

            self.ids.pipeSplitter.max_size = self.size[0] - 400
            self.ids.pipeSplitter.min_size = int(round(self.size[0]/2))

            with self.ids.pipeBack.canvas.before:
                Color(self.background[0], self.background[1], self.background[2], self.background[3])
                Rectangle(pos=self.pos, size=(self.size[0], self.ids.pipeSplitter.size[1]))

            width = min(self.ids.pipeSplitter.size[0]-50, self.ids.pipeSplitter.size[1]-50)
            self.pipePic.pos = (middle[0]-width/2, middle[1]-width/2)
            self.pipePic.size = (width, width)

            with self.ids.pipeDrawing.canvas:
                height = self.config.currentConfig["lenPipe"]["value"]/self.imageHeight*width

                time, dist, every, number = self.config.pathStats(False, self.settings.get('general', 'speed'))
                text = _("Total time") + ": " + str(time) + " sec" + \
                    "\n"+_("Photo number") + ": " + str(number) + \
                    "\n"+_("Photo every") + ": " + str(every) + " sec"

                Color(0.5, 0.5, 0.5, .6)
                Rectangle(pos=(self.size[0]-200, self.size[1] - (70+95)), size=(200, 70))

                label = CoreLabel(text=text, font_size=30, halign='left', valign='top', padding=(5, 5))
                label.refresh()
                text = label.texture
                Color(1, 1, 1, 1)
                Rectangle(pos=(self.size[0]-200, self.size[1] - (70+95)), size=(200, 70), texture=text)

                ratioX = (width / (self.imageWidth*100))  # Converts cm into pixels
                ratioY = (width / (self.imageHeight*100))  # Converts cm into pixels

                pipeWidth = width/50

                Color(self.pipeColor[0], self.pipeColor[1], self.pipeColor[2], self.pipeColor[3])

                if self.config.currentConfig["horizontal"]["value"]:
                    xPosition = -(width-height)/2 + (self.config.currentConfig["distOriginX"]["value"] + self.imageOrigin[0])*ratioX
                    yPosition = middle[1] - width/2 + (self.config.currentConfig["distOriginY"]["value"] + self.imageOrigin[1])*ratioY

                    Rectangle(pos=(middle[0]-height/2 + xPosition, yPosition), size=(height, pipeWidth))

                    for x in range(self.config.currentConfig["nbPipe"]["value"]-1):
                        yPosition += self.config.currentConfig["gaps"]["value"][x]*ratioY
                        Rectangle(pos=(middle[0]-height/2 + xPosition, yPosition), size=(height, pipeWidth))
                else:
                    xPosition = middle[0] - width/2 + (self.config.currentConfig["distOriginX"]["value"] + self.imageOrigin[0])*ratioX
                    yPosition = -(width-height)/2 + (self.config.currentConfig["distOriginY"]["value"] + self.imageOrigin[1])*ratioY

                    Rectangle(pos=(xPosition, middle[1]-height/2 + yPosition), size=(pipeWidth, height))

                    for x in range(self.config.currentConfig["nbPipe"]["value"]-1):
                        xPosition += self.config.currentConfig["gaps"]["value"][x]*ratioX
                        Rectangle(pos=(xPosition, middle[1]-height/2 + yPosition), size=(pipeWidth, height))

        elif self.mode == "Free":
            self.ids.libreSplitter.max_size = self.size[0] - 400
            self.zoomClamp()
            middle = (self.ids.libreDrawing.center_x, self.ids.libreDrawing.center_y)
            self.ids.libreDrawing.canvas.clear()

            self.ids.libreSplitter.min_size = int(round(self.size[0]/2))
            zoomedTrace = np.multiply(self.config.currentConfig["trace"]["value"], self.zoomFactor).tolist()

            self.ids.freeBack.canvas.before.clear()

            self.config.read()

            with self.ids.freeBack.canvas.before:
                Color(self.background[0], self.background[1], self.background[2], self.background[3])
                Rectangle(pos=self.pos, size=(self.size[0], self.ids.libreSplitter.size[1]))

            width = 200 * self.zoomFactor
            self.freePic.pos = (middle[0]-width/2, middle[1]-width/2)
            self.freePic.size = (width, width)

            with self.ids.libreDrawing.canvas:
                dist = 0
                if keyboard.is_pressed(self.settings.get('shortcuts', 'corner')):
                    for corner in self.corners:
                        Color(0, 1, 0, 0.8)
                        Ellipse(pos=(corner[0]*self.zoomFactor+middle[0]-self.diametre/2, corner[1]*self.zoomFactor+middle[1]-self.diametre/2), size=(self.diametre, self.diametre))

                isLoop = False
                goto = len(zoomedTrace)-1
                if len(zoomedTrace) > 2:
                    isLoop = bool(self.ids.loop.input.active)
                    if isLoop:
                        goto += 1

                self.config.currentConfig["loop"]["value"] = isLoop

                for i in range(goto):
                    nextPoint = (i+1) % len(zoomedTrace)
                    Color(self.pathColor[0], self.pathColor[1], self.pathColor[2], self.pathColor[3])
                    if self.config.currentConfig["photos"]["value"][i]:
                        Color(self.pathHighlight[0], self.pathHighlight[1], self.pathHighlight[2], self.pathHighlight[3])

                    Line(points=[zoomedTrace[i][0]+middle[0], zoomedTrace[i][1]+middle[1], zoomedTrace[nextPoint][0]+middle[0], zoomedTrace[nextPoint][1]+middle[1]], width=self.lineWidth)
                    thisDist = max(distance.euclidean(self.pixelToCM(self.config.currentConfig["trace"]["value"][i]), self.pixelToCM(self.config.currentConfig["trace"]["value"][nextPoint])), 0.0001)
                    dist += thisDist
                    if self.config.currentConfig["photos"]["value"][i]:
                        nb = math.floor(thisDist/float(self.config.currentConfig["photoPipe"]["value"]))
                        top = (thisDist-nb*float(self.config.currentConfig["photoPipe"]["value"]))/(2*thisDist)
                        ax = top * (zoomedTrace[i][0] - zoomedTrace[nextPoint][0])
                        ay = top * (zoomedTrace[i][1] - zoomedTrace[nextPoint][1])
                        Color(0, 0, 0)
                        for p in range(nb+1):
                            Ellipse(pos=(zoomedTrace[nextPoint][0]+middle[0] + ax-self.lineWidth/2 + ((float(self.config.currentConfig["photoPipe"]["value"])/thisDist)*(zoomedTrace[i][0] - zoomedTrace[nextPoint][0]))*p,
                                         zoomedTrace[nextPoint][1]+middle[1] + ay-self.lineWidth/2 + ((float(self.config.currentConfig["photoPipe"]["value"])/thisDist)*(zoomedTrace[i][1] - zoomedTrace[nextPoint][1]))*p),
                                    size=(self.lineWidth, self.lineWidth))

                for i in range(len(zoomedTrace)):
                    if self.lastTouched == i:
                        Color(self.nodeHighlight[0], self.nodeHighlight[1], self.nodeHighlight[2], self.nodeHighlight[3])
                        Ellipse(pos=(zoomedTrace[i][0]+middle[0]-(self.diametre+5)/2, zoomedTrace[i][1]+middle[1]-(self.diametre+5)/2),
                                size=(self.diametre+5, self.diametre+5))
                    Color(self.nodeColor[0], self.nodeColor[1], self.nodeColor[2], self.nodeColor[3])
                    if self.config.currentConfig["actionNodes"]["value"][i]:
                        Color(self.actionNode[0], self.actionNode[1], self.actionNode[2], self.actionNode[3])

                    Ellipse(pos=(zoomedTrace[i][0]+middle[0]-self.diametre/2, zoomedTrace[i][1]+middle[1]-self.diametre/2),
                            size=(self.diametre, self.diametre))
                    label = CoreLabel(text=str(i+1), font_size=20)
                    label.refresh()
                    text = label.texture
                    Color(0, 0, 0, 1)
                    Ellipse(pos=(zoomedTrace[i][0]+middle[0]-self.diametre/2, zoomedTrace[i][1]+middle[1]-self.diametre/2),
                            size=(self.diametre, self.diametre), texture=text)


                time, dist, every, number = self.config.pathStats(True, self.settings.get('general', 'speed'))
                text = _("Total time") + ": " + str(time) + " sec" + \
                    "\n"+_("Distance") + ": " + str(dist) + " cm" + \
                    "\n"+_("Photo number") + ": " + str(number)

                Color(1, 1, 1, .2)
                Rectangle(pos=(self.size[0]-200, self.size[1] - (70+95)), size=(200, 70))

                label = CoreLabel(text=text, font_size=30, halign='left', valign='top', padding=(5, 5))
                label.refresh()
                text = label.texture
                Color(1, 1, 1, 1)
                Rectangle(pos=(self.size[0]-200, self.size[1] - (70+95)), size=(200, 70), texture=text)

        elif self.mode == "Direct":
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
                       u'\u23EC': {"value": [4, 6], "position": [0, -1]},
                       u'\u23EB': {"value": [3, 6], "position": [0, 1]}
                       }

            for button in buttons:
                but = Button(text=button, font_size=fontSize, font_name=self.font,
                             pos=(middle[0]-buttonSize/2+(buttonSize+5)*buttons[button]["position"][0], middle[1]-buttonSize/2+(buttonSize+5)*buttons[button]["position"][1]),
                             size=(buttonSize, buttonSize))
                but.bind(on_press=lambda a, b=bytes([buttons[button]["value"][0]]): self.arduino.sendSerial(b))
                but.bind(on_release=lambda a, d=bytes([buttons[button]["value"][1]]): self.arduino.sendSerial(d))
                self.ids.directDrawing.add_widget(but)

            self.ids.directBack.canvas.before.clear()

            with self.ids.directBack.canvas.before:
                Color(self.background[0], self.background[1], self.background[2], self.background[3])
                Rectangle(pos=self.pos, size=(self.size[0], self.ids.directSplitter.size[1]))

            with self.ids.directDrawing.canvas.after:
                text = "X: " + str(round(float(self.arduino.systemPosition[0])/float(self.settings.get('general', 'stepToCm'))*10)/10) + " "+_("cm") + \
                    "\nY: " + str(round(float(self.arduino.systemPosition[1])/float(self.settings.get('general', 'stepToCm'))*10)/10) + " "+("cm")

                Color(1, 1, 1, .2)
                Rectangle(pos=(self.size[0]-200, self.size[1] - (70+95)), size=(200, 70))

                label = CoreLabel(text=text, font_size=30, halign='left', valign='top', padding=(5, 5))
                label.refresh()
                text = label.texture
                Color(1, 1, 1, 1)
                Rectangle(pos=(self.size[0]-200, self.size[1] - (70+95)), size=(200, 70), texture=text)

                switches = self.arduino.systemSwitchs
                for switch in switches:
                    Color(1, 1, 0)
                    if switches[switch]['value']:
                        Color(0, 0, 0)

                    Ellipse(pos=(switchMiddle[0] - self.switchDiameter / 2 + switchMiddle[0]/2*switches[switch]['position'][0],
                                 switchMiddle[1] - self.switchDiameter / 2 - switchMiddle[1]/2*switches[switch]['position'][1]),
                            size=(self.switchDiameter, self.switchDiameter))

                if not self.arduino.hasDirectProgram:
                    dimensionX = self.ids.directSplitter.size[0]
                    dimensionY = self.ids.directSplitter.size[1] - 50
                    Color(1, 1, 1, 0.7)
                    Rectangle(pos=(realMiddle[0]-dimensionX/2, realMiddle[1]-dimensionY/2), size=(dimensionX, dimensionY))
                    label = CoreLabel(text=_("Click on 'Upload' before sending serial data"), font_size=100, halign='middle', valign='middle', padding=(12, 12))
                    label.refresh()
                    text = label.texture
                    Color(0, 0, 0, 1)
                    Rectangle(pos=(realMiddle[0]-dimensionX/2, realMiddle[1]-(dimensionX*(3/16))/2), size=(dimensionX, dimensionX*(3/16)), texture=text)

    def clickedDown(self, touch):
        x = touch.x
        y = touch.y

        if self.ids.libreDrawing.collide_point(x, y) and self.mode == "Free":
            zoomedTrace = np.multiply(self.config.currentConfig["trace"]["value"], self.zoomFactor).tolist()

            # Updates zooming depending on the mouse wheel
            if touch.is_mouse_scrolling:
                self.zoomFactor += 0.1 if touch.button == 'scrollup' else -0.1
                self.update_rect()

            # Checks if the user right clicked on a node, if yes remove it
            for i in range(len(zoomedTrace)):
                if math.hypot(zoomedTrace[i][0]+self.ids.libreDrawing.center_x - x, zoomedTrace[i][1]+self.ids.libreDrawing.center_y - y) <= self.diametre/2:
                    if touch.button == 'right':
                        self.config.currentConfig["actionNodes"]["value"][i] = not self.config.currentConfig["actionNodes"]["value"][i]
                        self.update_rect()
                    elif touch.button == 'left':
                        self.isDragging = i
                        self.lastTouched = i
                        self.printCoords(self.config.currentConfig["trace"]["value"][i])
                        self.update_rect()
                    return

            # Check if we clicked on a line or not
            for i in range(len(zoomedTrace)-1):
                firstPoint = (zoomedTrace[i][0]+self.ids.libreDrawing.center_x, zoomedTrace[i][1]+self.ids.libreDrawing.center_y)
                secondPoint = (zoomedTrace[i+1][0]+self.ids.libreDrawing.center_x, zoomedTrace[i+1][1]+self.ids.libreDrawing.center_y)
                if hitLine(firstPoint, secondPoint, (x, y), self.lineWidth):
                    if touch.button == 'right':
                        self.config.currentConfig["photos"]["value"][i] = not self.config.currentConfig["photos"]["value"][i]
                        self.lastTouched = -1
                        self.update_rect()
                        return
                    elif touch.button == 'left':
                        coordX = (x-self.ids.libreDrawing.center_x)/self.zoomFactor
                        coordY = (y-self.ids.libreDrawing.center_y)/self.zoomFactor

                        self.printCoords((coordX, coordY))

                        self.config.currentConfig["trace"]["value"].insert(i+1, [coordX, coordY])
                        self.config.currentConfig["photos"]["value"].insert((i+1), False)
                        self.config.currentConfig["actionNodes"]["value"].insert((i+1), False)
                        self.lastTouched = i+1
                        self.isDragging = i+1
                        self.update_rect()
                        return

            if touch.button == 'right' and bool(self.ids.loop.input.active) and len(zoomedTrace) > 1:
                firstPoint = (zoomedTrace[len(zoomedTrace)-1][0]+self.ids.libreDrawing.center_x, zoomedTrace[len(zoomedTrace)-1][1]+self.ids.libreDrawing.center_y)
                secondPoint = (zoomedTrace[0][0]+self.ids.libreDrawing.center_x, zoomedTrace[0][1]+self.ids.libreDrawing.center_y)
                if hitLine(firstPoint, secondPoint, (x, y), self.lineWidth):
                    self.config.currentConfig["photos"]["value"][len(self.config.currentConfig["photos"]["value"])-1] = not self.config.currentConfig["photos"]["value"][len(self.config.currentConfig["photos"]["value"])-1]
                    self.update_rect()

            # Adds a new node where the user clicked
            if touch.button == 'left':
                coordX = (x-self.ids.libreDrawing.center_x)/self.zoomFactor
                coordY = (y-self.ids.libreDrawing.center_y)/self.zoomFactor

                self.printCoords((coordX, coordY))

                self.config.currentConfig["trace"]["value"].append([coordX, coordY])
                self.config.currentConfig["photos"]["value"].append(False)
                self.config.currentConfig["actionNodes"]["value"].append(False)
                self.lastTouched = len(self.config.currentConfig["photos"]["value"])-1
                self.isDragging = len(self.config.currentConfig["photos"]["value"])-1
                self.update_rect()

    def clickedUp(self, touch):
        if self.mode == "Free":
            if self.zoomFactor == 0.05 and self.isDragging != -1:
                self.positionClamp(self.isDragging)
                self.update_rect()
            self.isDragging = -1
            self.undoRedo.do([self.config.currentConfig["trace"]["value"].copy(), self.config.currentConfig["photos"]["value"].copy(), self.config.currentConfig["actionNodes"]["value"].copy()])

    def clickedMove(self, touch):
        if self.mode == "Free" and touch.button == 'left' and self.isDragging != -1:
            thisX = (touch.x-self.ids.libreDrawing.center_x)/self.zoomFactor
            thisY = (touch.y-self.ids.libreDrawing.center_y)/self.zoomFactor
            newPosition = (thisX, thisY)

            if keyboard.is_pressed(self.settings.get('shortcuts', 'angle')) and len(self.config.currentConfig["trace"]["value"]) > 0:  # To clamp relative to last one
                fromWhich = self.isDragging-1 % len(self.config.currentConfig["trace"]["value"])
                previousPoint = (self.config.currentConfig["trace"]["value"][fromWhich][0], self.config.currentConfig["trace"]["value"][fromWhich][1])
                dist = distance.euclidean(previousPoint, (thisX, thisY))
                angle = round(math.atan2(thisY-previousPoint[1], thisX-previousPoint[0])/(math.pi/4)) * (math.pi/4)

                newPosition = (math.cos(angle)*dist+previousPoint[0], math.sin(angle)*dist + previousPoint[1])

            elif keyboard.is_pressed(self.settings.get('shortcuts', 'corner')):  # To clamp to the corners (origin, top-right, ...)
                dist1 = distance.euclidean(self.corners[0], (thisX, thisY))
                dist2 = distance.euclidean(self.corners[1], (thisX, thisY))
                dist3 = distance.euclidean(self.corners[2], (thisX, thisY))
                dist4 = distance.euclidean(self.corners[3], (thisX, thisY))

                indice = np.argmin(np.array([dist1, dist2, dist3, dist4]))
                newPosition = self.corners[indice]

            self.printCoords(newPosition)

            self.config.currentConfig["trace"]["value"][self.isDragging] = newPosition
            self.lastTouched = self.isDragging

            self.update_rect()

    def removeNode(self):
        if self.lastTouched != -1:
            del self.config.currentConfig["trace"]["value"][self.lastTouched]
            del self.config.currentConfig["photos"]["value"][self.lastTouched]
            del self.config.currentConfig["actionNodes"]["value"][self.lastTouched]
            self.lastTouched = -1
            self.update_rect()

    def removeAllNodes(self):
        self.config.currentConfig["trace"]["value"] = []
        self.config.currentConfig["photos"]["value"] = []
        self.config.currentConfig["actionNodes"]["value"] = []
        self.undoRedo.do([self.config.currentConfig["trace"]["value"].copy(), self.config.currentConfig["photos"]["value"].copy(), self.config.currentConfig["actionNodes"]["value"].copy()])
        self.update_rect()

    def positionClamp(self, i):
        maxPosLeft = (-self.ids.libreSplitter.size[0]/2-self.innerScreenMargin[0])/(self.zoomFactor)
        maxPosRight = (self.ids.libreSplitter.size[0]/2-self.innerScreenMargin[1])/(self.zoomFactor)
        maxPosTop = (self.ids.libreSplitter.size[1]/2-self.innerScreenMargin[2])/(self.zoomFactor)
        maxPosDown = (-self.ids.libreSplitter.size[1]/2-self.innerScreenMargin[3])/(self.zoomFactor)

        self.config.currentConfig["trace"]["value"][i] = (min(max(self.config.currentConfig["trace"]["value"][i][0], maxPosLeft), maxPosRight),
                                                          min(max(self.config.currentConfig["trace"]["value"][i][1], maxPosDown), maxPosTop))

    def zoomClamp(self):
        size = self.ids.libreSplitter.size
        if len(self.config.currentConfig["trace"]["value"]) > 0:
            worstX = np.amax(np.hsplit(np.array(self.config.currentConfig["trace"]["value"]), 2)[0])
            worstY = np.amax(np.hsplit(np.array(self.config.currentConfig["trace"]["value"]), 2)[1])
            worstMX = np.amin(np.hsplit(np.array(self.config.currentConfig["trace"]["value"]), 2)[0])
            worstMY = np.amin(np.hsplit(np.array(self.config.currentConfig["trace"]["value"]), 2)[1])

            if worstX*self.zoomFactor > size[0]/2 - self.innerScreenMargin[1]:
                self.zoomFactor = (size[0]/2 - self.innerScreenMargin[1])/float(worstX)
            if worstY*self.zoomFactor > size[1]/2 - self.innerScreenMargin[2]:
                self.zoomFactor = min((size[1]/2 - self.innerScreenMargin[2])/float(worstY), self.zoomFactor)
            if worstMX*self.zoomFactor < -size[0]/2 - self.innerScreenMargin[0]:
                self.zoomFactor = min((-size[0]/2 - self.innerScreenMargin[0])/float(worstMX), self.zoomFactor)
            if worstMY*self.zoomFactor < -size[1]/2 - self.innerScreenMargin[3]:
                self.zoomFactor = min((-size[1]/2 - self.innerScreenMargin[3])/float(worstMY), self.zoomFactor)

        self.zoomFactor = min((size[0]/2)/float(100), self.zoomFactor)
        self.zoomFactor = min((size[1]/2 - 20)/float(100), self.zoomFactor)
        self.zoomFactor = max(self.zoomFactor, 0.05)

    def pixelToCM(self, point):
        height = self.corners[0][1] - self.corners[1][1]
        width = self.corners[0][0] - self.corners[2][0]
        x = ((point[0]-self.corners[3][0])*self.actualWidth*100)/width
        y = ((point[1]-self.corners[3][1])*self.actualHeight*100)/height
        return (x, y)

    def cmToPixel(self, point):
        height = self.corners[0][1] - self.corners[1][1]
        width = self.corners[0][0] - self.corners[2][0]
        x = (point[0]*width)/(self.actualWidth*100)+self.corners[3][0]
        y = (point[1]*height)/(self.actualHeight*100)+self.corners[3][1]
        return (x, y)

    def printCoords(self, point):
        toCm = self.pixelToCM(point)
        self.ids.coord.write(str(round(toCm[0]*10)/10) + " : " + str(round(toCm[1]*10)/10))

    def inputMove(self, *args):
        position = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", self.ids.coord.input.text)

        height = self.corners[0][1] - self.corners[1][1]
        width = self.corners[0][0] - self.corners[2][0]

        ratioX = width / (self.actualWidth*100)
        ratioY = height / (self.actualHeight*100)

        if len(position) == 2:
            if self.lastTouched == -1:
                self.config.currentConfig["trace"]["value"].append((float(position[0])*ratioX + self.corners[3][0], float(position[1])*ratioY + self.corners[3][1]))
                self.config.currentConfig["photos"]["value"].append(False)
                self.config.currentConfig["actionNodes"]["value"].append(False)
                self.lastTouched = len(self.config.currentConfig["photos"]["value"])-1
            else:
                self.config.currentConfig["trace"]["value"][self.lastTouched] = (float(position[0])*ratioX + self.corners[3][0], float(position[1])*ratioY + self.corners[3][1])

            self.update_rect()

    def tuyeauGap(self, *args):
        for gap in self.gaps:
            self.pipePanel.remove_widget(gap)

        if self.ids.nbPipe.read() < 2:
            self.update_rect()
            return

        if bool(self.ids.sameGap.input.active):
            self.gaps = [Input(inputName=_('Gap between pipes')+" (cm)", input_filter="float", default_text=str(self.config.currentConfig["gaps"]["value"][0]), callback=self.update_rect)]
            self.pipePanel.add_widget(self.gaps[0])
        else:
            self.gaps = []
            for pipe in range(max(self.ids.nbPipe.read(), 2)-1):
                default = str(self.config.currentConfig["gaps"]["value"][0])
                if pipe < len(self.config.currentConfig["gaps"]["value"]):
                    default = str(self.config.currentConfig["gaps"]["value"][pipe])

                self.gaps.append(Input(inputName=_('Gap between pipes ')+str(pipe+1)+"-"+str(pipe+2)+" (cm)", input_filter="float", default_text=default, callback=self.update_rect))
                self.pipePanel.add_widget(self.gaps[pipe])
        self.update_rect()

    def freeToPipe(self):
        self.ids.photoPipe.write(self.ids.freePhotoPipe.read())
        self.update_rect()

    def pipeToFree(self):
        self.ids.freePhotoPipe.write(self.ids.photoPipe.read())
        self.update_rect()

    def copyToClipboard(self):
        if self.mode == "Direct":
            pyperclip.copy(str(self.arduino.systemPosition))

    def undo(self, direction):
        last = self.undoRedo.undo(direction)
        self.config.currentConfig["trace"]["value"] = last[0].copy()
        self.config.currentConfig["photos"]["value"] = last[1].copy()
        self.config.currentConfig["actionNodes"]["value"] = last[2].copy()
        self.update_rect()

    def easyPopup(self, title, content, auto_dismiss=True):
        if isinstance(content, str):
            content = MyLabel(text=content)
            content.bind(on_ref_press=urlOpen)

        if self.popup != -1:
            self.popup.dismiss()

        self.popup = Popup(title=title,
                           content=content,
                           size_hint=(0.7, 0.7),
                           auto_dismiss=auto_dismiss)
        self.popup.open()
