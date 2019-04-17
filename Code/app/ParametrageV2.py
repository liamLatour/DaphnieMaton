import re
import threading
import time
from functools import partial
from io import open as openFile
from json import dumps as jsDumps
from json import load as jsLoad
from math import atan2, hypot, pi
from os import system as osSystem
from os.path import join as osJoinPath

import keyboard
import numpy as np
import pyperclip
import serial
from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config, ConfigParser
from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.settings import SettingsWithSidebar
from scipy.spatial import distance

from assets.libraries.classes import (Input, LoadDialog, ModeDropDown,
                                      PenDropDown, SaveDialog, getPorts,
                                      hitLine, polToCar, urlOpen, MyLabel, SettingButtons)
from assets.libraries.createFile import generateFile
from assets.libraries.localization import (_, change_language_to,
                                           translation_to_language_code)

from assets.helpMsg import pipeHelp, freeHelp, directHelp
import assets.libraries.undoRedo as UndoRedo

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.set('kivy','window_icon','..\\..\\Images\\kivyLogo.ico')


#https://stackoverflow.com/questions/47729340/how-to-change-default-kivy-logo-with-another-image-logo

Builder.load_file('.\\main.kv')

class Parametrage(BoxLayout):
    def __init__(self, *args, **kwargs):
        super(Parametrage, self).__init__(*args, **kwargs)
        self.settings = App.get_running_app().config
        self.params = {
            "nbPipe": 2,
            "lenPipe" : 1.2,
            "photoPipe" : 50,
            "distOriginX" : 50,
            "distOriginY" : 50,
            "sameGap" : True,
            "gaps" : [20],
            "loop" : False,
            "trace" : [],
            "photos" : []
        }
        self.speed = 8.6 # m per minutes
        self.imageWidth = 1.4 # in meter
        self.imageHeight = 1.4 # in meter
        self.actualWidth = 1.144 # in meter
        self.actualHeight = 1.1 # in meter
        self.imageOrigin = (17, 17.2) # in cm

        self.port = -1
        self.pen_drop_down = PenDropDown()
        self.mode_drop_down = ModeDropDown()

        self.tuyeau_panel = self.ids.tuyeauInputs
        self.gaps = []
        self.mode = "Pipe"
        self.font = ".\\assets\\seguisym.ttf"

        # Specifique au mode 'Free'
        self.lineWidth = 5
        self.diametre = 20
        self.dragging = -1
        self.lastTouched = -1
        self.zoom = 1
        self.margin = [-self.diametre/2-5, self.diametre/2+5, self.diametre/2+25, -self.diametre/2-25] # Left, Right, Top, Down
        self.corners = [(88, 82), (88, -72), (-75, 82), (-75, -72)] # Right-Top, Right-Down, Left-Top, Left-Down

        # Specifique au mode 'direct'
        self.board = -1
        self.clock = -1
        self.position = (0, 0)
        self.hasGoodProgram = False

        Clock.schedule_once(self.binding)
        Clock.schedule_interval(partial(self.save, -1, -1), int(self.settings.get('general', 'autoSave'))*60)
        keyboard.on_release_key('shift', self.update_rect)
        self.filePath = -1
        self.fileName = _("configuration")

    def binding(self, *args):
        self.ids.pipeDrawing.bind(size=self.update_rect, pos=self.update_rect)
        self.ids.directDrawing.bind(size=self.update_rect, pos=self.update_rect)
        self.ids.libreDrawing.bind(size=self.update_rect, pos=self.update_rect)
        self.ids.changeTab.bind(on_touch_up = self.changedTab)

        self.tuyeauGap()

    def poplb_update(self, *args):
        self.poplb.text_size = self.popup.size

    def help(self, *args):
        try: self.popup.dismiss()
        except: pass

        self.popup = Popup(title=_('Help'), size_hint=(0.7, 0.7))
        self.popbox = BoxLayout()

        if self.mode == "Pipe":
            self.poplb = MyLabel(text=pipeHelp)#Label(text=pipeHelp, text_size=self.popup.size, strip=True, valign='middle', halign='center', padding= (15, 35), markup = True)
        elif self.mode == "Free":
            self.poplb = MyLabel(text=freeHelp)
        elif self.mode == "Direct":
            self.poplb = MyLabel(text=directHelp)

        self.poplb.bind(on_ref_press=urlOpen)
        self.popup.bind(size=self.poplb_update)

        self.popbox.add_widget(self.poplb)
        self.popup.content = self.popbox
        self.popup.open()

    def show_port(self):
        self.pen_drop_down.open(self.ids.port_button)
        self.pen_drop_down.clear_widgets()

        self.pen_drop_down.add_widget(Button(text=_("No port"), height=48, size_hint_y= None, on_release=lambda a:self.change_port(-1)))
        arduinoPorts = getPorts()
        for port in arduinoPorts:
            self.pen_drop_down.add_widget(Button(text="COM"+str(arduinoPorts[port]), height=48, size_hint_y= None, on_release=lambda a:self.change_port(arduinoPorts[port])))

    def change_port(self, nb):
        self.port = nb
        if nb>= 0:
            self.ids.port_button.text = _("Port") + " " + str(nb)

            self.moveDirect(bytes([9]))
            if self.board != -1:
                response = self.board.readline().decode("utf-8").rstrip()
                if response == "DaphnieMaton":
                    self.hasGoodProgram = True
                    self.clock = Clock.schedule_interval(self.readFromSerial, 0.2)
                    self.update_rect()

        else:
            self.ids.port_button.text = _("Port")
        self.pen_drop_down.dismiss()

    # Saving and loading system
    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self):
        if self.filePath != -1:
            content = LoadDialog(load=self.load, cancel=self.dismiss_popup, path=self.filePath)
        else:
            content = LoadDialog(load=self.load, cancel=self.dismiss_popup, path=self.settings.get('general', 'savePath'))
        self._popup = Popup(title=_("Load file"), content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def show_save(self):
        content = SaveDialog(save=self.save, cancel=self.dismiss_popup, path=self.settings.get('general', 'savePath'))
        self._popup = Popup(title=_("Save file"), content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def load(self, path, filename):
        try:
            self.filePath = path
            self.fileName = filename[0].replace(".json", "")
            with open(osJoinPath(path, filename[0])) as stream:
                self.params = jsLoad(stream)
                for param in self.params:
                    try:
                        self.ids[param].unbindThis()
                        self.ids[param].input.text = str(self.params[param])
                        self.ids[param].input.active = bool(self.params[param])
                        self.ids[param].bindThis()
                    except: pass

            self.tuyeauGap()
            self.dismiss_popup()
        except:
            print("wrong file")

    def save(self, path, filename, *args):
        if path == -1:
            if self.filePath == -1:
                print("no path")
                return
            else:
                path = self.filePath
                filename = self.fileName

        self.filePath = path
        self.fileName = filename

        with open(osJoinPath(path, filename+".json"), 'w') as stream:
            paramsCopy = self.params.copy()

            for item in paramsCopy: # Converts numpy arrays into python list
                try: paramsCopy[item] = paramsCopy[item].tolist()
                except: pass

            stream.write(jsDumps( paramsCopy ))

        self.dismiss_popup()

    def readFromSerial(self, *args):
        if self.port != -1:
            self.moveDirect(bytes([7]))
            x = self.board.readline().decode("utf-8").rstrip()
            y = self.board.readline().decode("utf-8").rstrip()
            self.position = (x, y)
            self.update_rect()

    def getCallibrationAsync(self, *args):
        if self.port != -1 and self.board != -1:
            if self.board.in_waiting > 0:
                data_str = self.board.readline().decode("utf-8").rstrip()
                self.settings.set("general", "stepToCm", str(data_str))
                self.settings.write()
                self.callibrateClock.cancel()
                self.popup.dismiss()
                Popup(title=_('Callibration successful'), content=Label(text=_('The DaphnieMaton has found it\'s ratio: ') + str(data_str) + " step/cm"), size_hint=(None, None), size=(400, 300)).open()
                print("Callibrated to " + str(data_str))

    def callibrate(self):
        if self.port != -1:
            self.moveDirect(bytes([10]))
            self.callibrateClock = Clock.schedule_interval(self.getCallibrationAsync, 0.5)

    def update(self, callibration=False, callback=None, *args):
        self.popup = Popup(title=_('Upload'), content=AsyncImage(source='.\\assets\\logo.png', size=(100, 100)), size_hint=(None, None), size=(400, 300), auto_dismiss=False)
        self.popup.open()
        if self.clock != -1:
            self.clock.cancel()
            self.clock = -1

        threading.Thread(target=lambda: self.updateAsync(callibration=callibration, callback=callback)).start()

    def updateAsync(self, callibration, callback):
        try:
            arduinoPath = self.settings.get('general', 'arduinoPath')
            if self.port != -1:
                try:
                    self.board.close()
                    self.board = -1
                except: pass

                if callibration:
                    osSystem(arduinoPath + "\\arduino_debug --board arduino:avr:mega:cpu=atmega2560 --port COM"+str(self.port)+" --upload .\\assets\\directFile\\directFile.ino")            
                    self.hasGoodProgram = True
                    self.update_rect()

                elif self.mode == "Pipe":
                    parcours = self.generatePathFromPipe()
                    genFile = generateFile(parcours[0], parcours[1])
                    f = open(".\\assets\\currentFile\\currentFile.ino","w+")
                    f.write(genFile)
                    f.close()
                    osSystem(arduinoPath + "\\arduino_debug --board arduino:avr:mega:cpu=atmega2560 --port COM"+str(self.port)+" --upload .\\assets\\currentFile\\currentFile.ino")
                    self.hasGoodProgram = False

                elif self.mode == "Free":
                    genFile = generateFile(self.params["trace"], self.params["photos"])
                    f = open(".\\assets\\currentFile\\currentFile.ino","w+")
                    f.write(genFile)
                    f.close()
                    osSystem(arduinoPath + "\\arduino_debug --board arduino:avr:mega:cpu=atmega2560 --port COM"+str(self.port)+" --upload .\\assets\\currentFile\\currentFile.ino")
                    self.hasGoodProgram = False

                elif self.mode == "Direct":
                    osSystem(arduinoPath + "\\arduino_debug --board arduino:avr:mega:cpu=atmega2560 --port COM"+str(self.port)+" --upload .\\assets\\directFile\\directFile.ino")            
                    self.hasGoodProgram = True
                    self.update_rect()
                    self.clock = Clock.schedule_interval(self.readFromSerial, 0.2)

                print("DONE !")
                self.popup.dismiss()
                Popup(title=_('Success !'), content=Label(text=_('Upload finished successfully !')), size_hint=(None, None), size=(400, 300)).open()
                if callback != None:
                    callback()
            else:
                self.popup.dismiss()
                Popup(title=_('No port detected'), content=Label(text=_('No serial port was specified')), size_hint=(None, None), size=(400, 300)).open()
        except Exception as e:
            self.popup.dismiss()
            Popup(title=_('Oopsie...'), content=Label(text=_('Something went wrong, try again or report a bug') + "\n" + str(e)), size_hint=(None, None), size=(400, 300)).open()

    def changedTab(self, *args):
        self.mode = self.ids.tabbedPanel.current_tab.name

        if self.clock != -1:
            self.clock.cancel()
            self.clock = -1

        self.zoom = float('inf')

        if self.mode == "Direct":
            self.moveDirect(bytes([9]))
            if self.board != -1:
                response = self.board.readline().decode("utf-8").rstrip()
                if response == "DaphnieMaton":
                    self.hasGoodProgram = True
                    self.clock = Clock.schedule_interval(self.readFromSerial, 0.2)

        self.update_rect()

    def generatePathFromPipe(self, copy=False):
        """Converts the pipe parameters to a path.

        copy bool: copy in Free mode or not

        return: the converted path
        """
        path = []
        photos = []

        length = self.params["lenPipe"]
        origin = self.corners[3]
        height = self.corners[0][1] - self.corners[1][1]
        width = self.corners[0][0] - self.corners[2][0]

        ratioX = width / (self.actualWidth*100)
        ratioY = height / (self.actualHeight)

        curX = origin[0] + self.params["distOriginX"]*ratioX
        deltaY = origin[1] + self.params["distOriginY"]*ratioY

        path.append(curX)
        path.append(deltaY)
        photos.append(True)
        path.append(curX)
        path.append(deltaY + length*ratioY)
        photos.append(False)

        for x in range(self.params["nbPipe"]-1):
            curX += self.params["gaps"][x]*ratioX
            path.append(curX)
            path.append(deltaY)
            photos.append(True)
            path.append(curX)
            path.append(deltaY + length*ratioY)
            photos.append(False)

        if copy:
            self.params["trace"] = path
            self.params["photos"] = photos

        return (path, photos)

    # Drawing on canvas
    def update_rect(self, *args):
        self.mode = self.ids.tabbedPanel.current_tab.name

        if self.mode == "Pipe":
            middle = (self.ids.pipeDrawing.center_x, self.ids.pipeDrawing.center_y)
            self.ids.pipeDrawing.canvas.before.clear()

            gapsValue = []
            if bool(self.ids.sameGap.input.active):
                gapsValue = np.ones(max(self.sanitize(self.ids.nbPipe.input.text), 1)-1) * self.sanitize(self.gaps[0].input.text)
            else:
                for gap in self.gaps:
                    gapsValue.append(max(self.sanitize(gap.input.text), 0))

            if len(gapsValue) == 0:
                gapsValue = [20]

            self.params["nbPipe"] = max(self.sanitize(self.ids.nbPipe.input.text), 1)
            self.params["lenPipe"] = max(self.sanitize(self.ids.lenPipe.input.text), 0.1)
            self.params["photoPipe"] = max(self.sanitize(self.ids.photoPipe.input.text), 1)
            self.params["distOriginX"] = self.sanitize(self.ids.distOriginX.input.text)
            self.params["distOriginY"] = self.sanitize(self.ids.distOriginY.input.text)
            self.params["sameGap"] = self.ids.sameGap.input.active
            self.params["gaps"] = gapsValue

            if self.params["nbPipe"] <= 2:
                self.ids.sameGap.hide()
            else:
                self.ids.sameGap.show()

            self.ids.pipeSplitter.max_size = self.size[0] - 400
            self.ids.pipeSplitter.min_size = int(round(self.size[0]/2))

            with self.ids.pipeDrawing.canvas.before:
                width = min(self.ids.pipeSplitter.size[0]-50, self.ids.pipeSplitter.size[1]-50)
                height = self.params["lenPipe"]/self.imageHeight *width

                Rectangle(source='.\\assets\\topDownView.png', pos = (middle[0]-width/2, middle[1]-width/2), size = (width, width))

                text = _("Total time") + ": " + str(round(self.speed*self.params["nbPipe"]/100)*100) + " sec" + \
                                        "\n"+_("Photo number") + ": " + str( round((self.params["nbPipe"]*self.params["lenPipe"])/(self.params["photoPipe"]/100))) + \
                                        "\n"+_("Photo every") +" "+ str( round( ((self.speed*self.params["nbPipe"]) / ((self.params["nbPipe"]*self.params["lenPipe"])/(self.params["photoPipe"]/100)))*10 )/10 ) + " sec"

                Color(1,1,1, .2)
                Rectangle(pos = (self.size[0]-200, self.size[1] - (70 +95)), size = (200, 70))

                label = CoreLabel(text=text, font_size=30, halign='left', valign='top', padding=(5, 5))
                label.refresh()
                text = label.texture
                Color(1, 1, 1, 1)
                Rectangle(pos=(self.size[0]-200, self.size[1] - (70 +95)), size=(200, 70), texture=text)

                ratioX = (width / (self.imageWidth*100)) # Converts cm into pixels
                ratioY = (width / (self.imageHeight*100)) # Converts cm into pixels

                curX = middle[0] - width/2 + (self.params["distOriginX"] + self.imageOrigin[0])*ratioX
                deltaY = -(width-height)/2 + (self.params["distOriginY"] + self.imageOrigin[1])*ratioY

                pipeWidth = width/50

                Rectangle(pos = (curX, middle[1]-height/2 + deltaY), size = (pipeWidth, height))

                for x in range(self.params["nbPipe"]-1):
                    curX += self.params["gaps"][x]*ratioX
                    Rectangle(pos = (curX, middle[1]-height/2 + deltaY), size = (pipeWidth, height))

        elif self.mode == "Free":
            self.ids.libreSplitter.max_size = self.size[0] - 400
            self.zoomClamp()
            middle = (self.ids.libreDrawing.center_x, self.ids.libreDrawing.center_y)
            self.ids.libreDrawing.canvas.before.clear()

            self.ids.libreSplitter.min_size = int(round(self.size[0]/2))
            zoomedTrace = np.multiply(self.params["trace"], self.zoom).tolist()

            with self.ids.libreDrawing.canvas.before:
                width = 200 * self.zoom
                Rectangle(source='.\\assets\\topDownView.png', pos = (middle[0]-width/2, middle[1]-width/2), size = (width, width))

                if keyboard.is_pressed("shift"):
                    for corner in self.corners:
                        Color(0, 1, 0, 0.8)
                        Ellipse(pos=(corner[0]*self.zoom+middle[0]-self.diametre/2, corner[1]*self.zoom+middle[1]-self.diametre/2), size=(self.diametre, self.diametre))

                if len(zoomedTrace) > 0:
                    if len(zoomedTrace) > 4:
                        isLoop = bool(self.ids.loop.input.active)
                    else:
                        isLoop = False
                    
                    self.params["loop"] = isLoop

                    for i in range(int(len(zoomedTrace)/2)):
                        if (i+1)*2+1 >= len(zoomedTrace) and isLoop:
                            if self.params["photos"][i]: Color(1, 0.31, 1, 0.5)
                            else: Color(0, 0.31, 1, 0.5)
                            Line(points=[zoomedTrace[i*2]+middle[0], zoomedTrace[i*2+1]+middle[1], zoomedTrace[0]+middle[0], zoomedTrace[1]+middle[1]], width=self.lineWidth)
                        
                        elif (i+1)*2+1 < len(zoomedTrace):
                            if self.params["photos"][i]: Color(1, 0.31, 1, 0.5)
                            else: Color(0, 0.31, 1, 0.5)
                            Line(points=[zoomedTrace[i*2]+middle[0], zoomedTrace[i*2+1]+middle[1], zoomedTrace[(i+1)*2]+middle[0], zoomedTrace[(i+1)*2+1]+middle[1]], width=self.lineWidth)
                    
                    for i in range(int(len(zoomedTrace)/2)):
                        if self.lastTouched == i:
                            Color(1, 0, 0, 0.8)
                            Ellipse(pos=(zoomedTrace[i*2]+middle[0]-(self.diametre+5)/2, zoomedTrace[i*2+1]+middle[1]-(self.diametre+5)/2), size=(self.diametre+5, self.diametre+5))
                        Color(1, 0.8, 0, 1)
                        Ellipse(pos=(zoomedTrace[i*2]+middle[0]-self.diametre/2, zoomedTrace[i*2+1]+middle[1]-self.diametre/2), size=(self.diametre, self.diametre))
                        label = CoreLabel(text=str(i+1), font_size=20)
                        label.refresh()
                        text = label.texture
                        Color(0, 0, 0, 1)
                        Ellipse(pos=(zoomedTrace[i*2]+middle[0]-self.diametre/2, zoomedTrace[i*2+1]+middle[1]-self.diametre/2), size=(self.diametre, self.diametre), texture=text)

                text = ""

                Color(1,1,1, .2)
                Rectangle(pos = (self.size[0]-200, self.size[1] - (70 +95)), size = (200, 70))

                label = CoreLabel(text=text, font_size=30, halign='left', valign='top', padding=(5, 5))
                label.refresh()
                text = label.texture
                Color(1, 1, 1, 1)
                Rectangle(pos=(self.size[0]-200, self.size[1] - (70 +95)), size=(200, 70), texture=text)

        elif self.mode == "Direct":
            middle = (self.ids.directDrawing.center_x, self.ids.directDrawing.center_y)
            self.ids.directDrawing.clear_widgets()
            self.ids.directDrawing.canvas.before.clear()
            self.ids.directDrawing.canvas.after.clear()

            buttonSize = min(self.ids.directSplitter.size[0]/4, self.ids.directSplitter.size[1]/4)
            fontSize = min(self.ids.directSplitter.size[0]/20, self.ids.directSplitter.size[1]/20)

            raz = Button(text=_('Origin'), font_size=fontSize, pos = (middle[0]-buttonSize/2, middle[1]-buttonSize/2), size = (buttonSize, buttonSize))

            right = Button(text=u'\u23E9', font_size=fontSize, font_name=self.font, pos = (middle[0]+buttonSize+5-buttonSize/2, middle[1]-buttonSize/2), size = (buttonSize, buttonSize))
            left = Button(text=u'\u23EA', font_size=fontSize, font_name=self.font, pos = (middle[0]-buttonSize-5-buttonSize/2, middle[1]-buttonSize/2), size = (buttonSize, buttonSize))
            up = Button(text=u'\u23EB', font_size=fontSize, font_name=self.font, pos = (middle[0]-buttonSize/2, middle[1]+buttonSize+5-buttonSize/2), size = (buttonSize, buttonSize))
            down = Button(text=u'\u23EC', font_size=fontSize, font_name=self.font, pos = (middle[0]-buttonSize/2, middle[1]-buttonSize-5-buttonSize/2), size = (buttonSize, buttonSize))

            raz.bind(on_release=partial(self.moveDirect, bytes([8])))

            right.bind(on_press=partial(self.moveDirect, bytes([1])))
            right.bind(on_release=partial(self.moveDirect, bytes([5])))
            left.bind(on_press=partial(self.moveDirect, bytes([2])))
            left.bind(on_release=partial(self.moveDirect, bytes([5])))
            up.bind(on_press=partial(self.moveDirect, bytes([3])))
            up.bind(on_release=partial(self.moveDirect, bytes([6])))
            down.bind(on_press=partial(self.moveDirect, bytes([4])))
            down.bind(on_release=partial(self.moveDirect, bytes([6])))

            self.ids.directDrawing.add_widget(raz)

            self.ids.directDrawing.add_widget(right)
            self.ids.directDrawing.add_widget(left)
            self.ids.directDrawing.add_widget(up)
            self.ids.directDrawing.add_widget(down)

            with self.ids.directDrawing.canvas.before:
                text = "X: " + str(self.position[0]) + " "+_("step") + \
                        "\nY: " + str(self.position[1]) + " "+("step")

                Color(1,1,1, .2)
                Rectangle(pos = (self.size[0]-200, self.size[1] - (70 +95)), size = (200, 70))

                label = CoreLabel(text=text, font_size=30, halign='left', valign='top', padding=(5, 5))
                label.refresh()
                text = label.texture
                Color(1, 1, 1, 1)
                Rectangle(pos=(self.size[0]-200, self.size[1] - (70 +95)), size=(200, 70), texture=text)

            if not self.hasGoodProgram:
                with self.ids.directDrawing.canvas.after:
                    dimensionX = self.ids.directSplitter.size[0]
                    dimensionY = self.ids.directSplitter.size[1] - 50
                    Color(1, 1, 1, 0.7)
                    Rectangle(pos=(middle[0]-dimensionX/2, middle[1]-dimensionY/2), size=(dimensionX, dimensionY))
                    label = CoreLabel(text=_("Click on 'Upload' before sending serial data"), font_size=100, halign='middle', valign='middle', padding=(12, 12))
                    label.refresh()
                    text = label.texture
                    Color(0, 0, 0, 1)
                    Rectangle(pos=(middle[0]-dimensionX/2, middle[1]-(dimensionX*(3/16))/2), size=(dimensionX, dimensionX*(3/16)), texture=text)

    def moveDirect(self, direction, *args):
        if self.port != -1:
            try:
                self.board.write(direction)
            except:
                self.board = serial.Serial('COM'+str(self.port), 9600, timeout=0.5)
                time.sleep(2)
                self.board.write(direction)
    
    def clickedDown(self, touch):
        if self.mode == "Free":
            x = touch.x
            y = touch.y
            zoomedTrace = np.multiply(self.params["trace"], self.zoom).tolist()

            if self.ids.libreDrawing.collide_point(x, y):
                for i in range(int(len(zoomedTrace)/2)):
                    if hypot(zoomedTrace[i*2]+self.ids.libreDrawing.center_x - x, zoomedTrace[i*2+1]+self.ids.libreDrawing.center_y - y) <= self.diametre/2:
                        if touch.button == 'right':
                            del self.params["trace"][i*2+1]
                            del self.params["trace"][i*2]
                            del self.params["photos"][i]
                            self.lastTouched = -1
                            self.update_rect()
                        elif touch.button == 'left':
                            self.dragging = i
                        return
                if touch.button == 'left':
                    coordX = (x-self.ids.libreDrawing.center_x)/self.zoom
                    coordY = (y-self.ids.libreDrawing.center_y)/self.zoom

                    height = self.corners[0][1] - self.corners[1][1]
                    width = self.corners[0][0] - self.corners[2][0]

                    self.ids.coord.unbindThis()
                    self.ids.coord.input.text = str(round(((coordX-self.corners[3][0])*(self.actualWidth*1000))/width)/10) + " : " + str(round(((coordY-self.corners[3][1])*(self.actualHeight*1000))/height)/10)
                    self.ids.coord.bindThis()

                    self.params["trace"].append(coordX)
                    self.params["trace"].append(coordY)
                    self.params["photos"].append(False)
                    self.lastTouched = len(self.params["photos"])-1
                    self.dragging = len(self.params["photos"])-1
                    self.update_rect()
                    return
                elif touch.button == 'right':
                    self.lastTouched = -1
                    # Check if we clicked on a line or not
                    for i in range(int(len(zoomedTrace)/2)-1):
                        firstPoint = (zoomedTrace[i*2]+self.ids.libreDrawing.center_x, zoomedTrace[i*2+1]+self.ids.libreDrawing.center_y)
                        secondPoint = (zoomedTrace[(i+1)*2]+self.ids.libreDrawing.center_x, zoomedTrace[(i+1)*2+1]+self.ids.libreDrawing.center_y)
                        if hitLine(firstPoint, secondPoint, (x, y), self.lineWidth):
                            self.params["photos"][i] = not self.params["photos"][i]
                            self.update_rect()
                            return
                    if bool(self.ids.loop.input.active):
                        firstPoint = (zoomedTrace[len(zoomedTrace)-2]+self.ids.libreDrawing.center_x, zoomedTrace[len(zoomedTrace)-1]+self.ids.libreDrawing.center_y)
                        secondPoint = (zoomedTrace[0]+self.ids.libreDrawing.center_x, zoomedTrace[1]+self.ids.libreDrawing.center_y)
                        if hitLine(firstPoint, secondPoint, (x, y), self.lineWidth):
                            self.params["photos"][len(self.params["photos"])-1] = not self.params["photos"][len(self.params["photos"])-1]
                            self.update_rect()
                elif touch.is_mouse_scrolling:
                    dist = 0.1 if touch.button == 'scrollup' else -0.1
                    self.zoom += dist
                    self.zoomClamp()
                    self.update_rect()

    def clickedUp(self, touch):
        if self.mode == "Free":
            if touch.button == 'left':
                self.dragging = -1
            if self.zoom == 0.05:
                self.positionClamp()
                self.update_rect()
            UndoRedo.do([self.params["trace"].copy(), self.params["photos"].copy()])
    
    def clickedMove(self, touch):
        if self.mode == "Free":
            newPosition = -1
            if touch.button == 'left' and self.dragging != -1:
                thisX = (touch.x-self.ids.libreDrawing.center_x)/self.zoom
                thisY = (touch.y-self.ids.libreDrawing.center_y)/self.zoom

                if keyboard.is_pressed("ctrl") and len(self.params["trace"]) > 2: # To clamp relative to last one (right angles)
                    fromWhich = self.dragging-1 % len(self.params["trace"])
                    previousPoint = (self.params["trace"][(fromWhich)*2], self.params["trace"][(fromWhich)*2+1])
                    dist = distance.euclidean(previousPoint, (thisX, thisY))
                    angle = round(atan2(thisY-previousPoint[1], thisX-previousPoint[0])/ (pi/4)) * (pi/4)

                    position = polToCar(previousPoint, dist, angle)
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
                    height = self.corners[0][1] - self.corners[1][1]
                    width = self.corners[0][0] - self.corners[2][0]

                    self.ids.coord.unbindThis()
                    self.ids.coord.input.text = str(round(((newPosition[0]-self.corners[3][0])*(self.actualWidth*1000))/width)/10) + " : " + str(round(((newPosition[1]-self.corners[3][1])*(self.actualHeight*1000))/height)/10)
                    self.ids.coord.bindThis()

                    self.params["trace"][self.dragging*2] = newPosition[0]
                    self.params["trace"][self.dragging*2+1] = newPosition[1]

                    self.lastTouched = self.dragging

                self.update_rect()

    def removeAllNodes(self):
        self.params["trace"] = []
        self.params["photos"] = []
        UndoRedo.do([self.params["trace"].copy(), self.params["photos"].copy()])
        self.update_rect()

    def inputMove(self, *args):
        position = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", self.ids.coord.input.text)

        height = self.corners[0][1] - self.corners[1][1]
        width = self.corners[0][0] - self.corners[2][0]

        ratioX = width / (self.actualWidth*100)
        ratioY = height / (self.actualHeight*100)

        if len(position) == 2:
            if self.lastTouched == -1:
                self.params["trace"].append(float(position[0])*ratioX + self.corners[3][0])
                self.params["trace"].append(float(position[1])*ratioY + self.corners[3][1])
                self.params["photos"].append(False)
                self.lastTouched = len(self.params["photos"]) -1
            elif self.lastTouched*2+1 < len(self.params["trace"]):
                self.params["trace"][self.lastTouched*2] = float(position[0])*ratioX + self.corners[3][0]
                self.params["trace"][self.lastTouched*2+1] = float(position[1])*ratioY + self.corners[3][1]

            self.update_rect()

    def positionClamp(self):
        maxPosLeft = (-self.ids.libreSplitter.size[0]/2-self.margin[0])/(self.zoom)
        maxPosRight = (self.ids.libreSplitter.size[0]/2-self.margin[1])/(self.zoom)
        maxPosTop = (self.ids.libreSplitter.size[1]/2-self.margin[2])/(self.zoom)
        maxPosDown = (-self.ids.libreSplitter.size[1]/2-self.margin[3])/(self.zoom)

        for i in range(int(len(self.params["trace"])/2)):
            self.params["trace"][i*2] = min(max(self.params["trace"][i*2], maxPosLeft), maxPosRight)
            self.params["trace"][i*2+1] = min(max(self.params["trace"][i*2+1], maxPosDown), maxPosTop)
                
    def zoomClamp(self):
        size = self.ids.libreSplitter.size
        worstX = 0
        worstY = 0
        worstMX = 0
        worstMY = 0
        for i in range(int(len(self.params["trace"])/2)):
            if self.params["trace"][i*2] > worstX:
                worstX = self.params["trace"][i*2]
            elif self.params["trace"][i*2] < worstMX:
                worstMX = self.params["trace"][i*2]
            if self.params["trace"][i*2+1] > worstY:
                worstY = self.params["trace"][i*2+1]
            elif self.params["trace"][i*2+1] < worstMY:
                worstMY = self.params["trace"][i*2+1]

        if worstX*self.zoom > size[0]/2 - self.margin[1]:
            self.zoom = (size[0]/2 - self.margin[1])/float(worstX)
        if worstY*self.zoom > size[1]/2 - self.margin[2]:
            self.zoom = min((size[1]/2 - self.margin[2])/float(worstY), self.zoom)
        if worstMX*self.zoom < -size[0]/2 - self.margin[0]:
            self.zoom = min((-size[0]/2 - self.margin[0])/float(worstMX), self.zoom)
        if worstMY*self.zoom < -size[1]/2 - self.margin[3]:
            self.zoom = min((-size[1]/2 - self.margin[3])/float(worstMY), self.zoom)

        if 100*self.zoom > size[0]/2:
            self.zoom = min((size[0]/2)/float(100), self.zoom)
        if 100*self.zoom > size[1]/2 - 20:
            self.zoom = min((size[1]/2 - 20)/float(100), self.zoom)

        self.zoom = max(self.zoom, 0.05)
    
    def tuyeauGap(self, *args):
        if self.gaps != []:
            for gap in self.gaps:
                self.tuyeau_panel.remove_widget(gap)

        if self.sanitize(self.ids.nbPipe.input.text) < 2:
            return

        if bool(self.ids.sameGap.input.active):
            self.gaps = [Input(inputName=_('Gap between pipes')+" (cm)", input_filter="float", default_text=str(self.params["gaps"][0]), callback=self.update_rect)]
            self.tuyeau_panel.add_widget(self.gaps[0])
        else:
            self.gaps = []
            for pipe in range(max(self.sanitize(self.ids.nbPipe.input.text), 2)-1):
                try:
                    default = str(self.params["gaps"][pipe])
                except:
                    default = str(self.params["gaps"][0])   

                self.gaps.append(Input(inputName=_('Gap between pipes ')+str(pipe+1)+"-"+str(pipe+2)+" (cm)", input_filter="float", default_text=default, callback=self.update_rect))
                self.tuyeau_panel.add_widget(self.gaps[pipe])
        self.update_rect()

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
                try:
                    return bool(number)
                except:
                    return 0

    def copyToClipboard(self):
        if self.mode == "Direct":
            print("Copied")
            pyperclip.copy(str(self.position))

    def undo(self):
        last = UndoRedo.undo([self.params["trace"].copy(), self.params["photos"].copy()])
        if last != -1:
            self.params["trace"] = last[0]
            self.params["photos"] = last[1]
        self.update_rect()

class DaphnieMatonApp(App):
    def build_config(self, config):
        config.setdefaults('general', {
            'arduinoPath': 'C:\\',
            'savePath': 'C:\\',
            'stepToCm': 100,
            'autoSave': 5,
            'language': "English"})
        config.setdefaults('shortcuts', {
            'save': 'ctrl+s',
            'copy': 'ctrl+c',
            'undo': 'ctrl+z'})

    def build(self):
        self.settings_cls = SettingsWithSidebar
        #self.use_kivy_settings = False
        self.icon = '..\\Images\\kivyLogo.png'
        self.update_language_from_config()
        self.app = Parametrage()
        self.save = keyboard.add_hotkey(self.config.get('shortcuts', 'save'), self.app.save, args=[-1, -1])
        self.copy = keyboard.add_hotkey(self.config.get('shortcuts', 'copy'), self.app.copyToClipboard)
        self.help = keyboard.add_hotkey(self.config.get('shortcuts', 'undo'), self.app.undo)

        return self.app

    def update_language_from_config(self):
        config_language = self.config.get('general', 'language')
        change_language_to(translation_to_language_code(config_language))

    def build_settings(self, settings):
        settings.register_type('buttons', SettingButtons)
        f = openFile(".\\assets\\config.json", "r", encoding='utf8')
        if f.mode == 'r':
            contents = f.read()
            settings.add_json_panel(_('General'), self.config, data=contents)

        f = openFile(".\\assets\\shortcuts.json", "r", encoding='utf8')
        if f.mode == 'r':
            contents = f.read()
            settings.add_json_panel(_('Shortcuts'), self.config, data=contents)
    
    def on_config_change(self, config, section, key, value):
        if section == "general" and key == "language":
            change_language_to(translation_to_language_code(value))
            print("Language changed")
        if section == "general" and key == "calibrate":
            self.app.update(callibration=True, callback=self.app.callibrate)
            print("Calibrate")

        if section == "shortcuts" and key == "save":
            keyboard.remove_hotkey(self.save)
            self.save = keyboard.add_hotkey(value, self.app.save, args=[-1, -1])
        if section == "shortcuts" and key == "copy":
            keyboard.remove_hotkey(self.copy)
            self.copy = keyboard.add_hotkey(value, self.app.copyToClipboard)
        if section == "shortcuts" and key == "help":
            keyboard.remove_hotkey(self.help)
            self.help = keyboard.add_hotkey(value, self.app.undo)

if __name__ == '__main__':
    DaphnieMatonApp().run()