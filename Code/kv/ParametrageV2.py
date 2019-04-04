import json
import os
import threading
import time
from functools import partial
from math import hypot

import keyboard
import numpy as np
import PIL
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
from scipy.spatial import distance
from kivy.uix.settings import Settings # Sidebar

from libraries.classes import (Input, LoadDialog, ModeDropDown, PenDropDown,
                               SaveDialog, getPorts, hitLine, urlOpen)
from libraries.createFile import generateFile

#TODO: add https://kivy.org/doc/stable/api-kivy.uix.settings.html


Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
#Config.set('kivy','window_icon','logo.ico')
Builder.load_file('main.kv')

class Parametrage(BoxLayout):
    def __init__(self, *args, **kwargs):
        super(Parametrage, self).__init__(*args, **kwargs)
        self.params = {
            "nbPipe": 2,
            "lenPipe" : 1.2,
            "timePipe" : 10,
            "photoPipe" : 50,
            "constGap" : True,
            "gaps" : [20],
            "loop" : False,
            "trace" : [],
            "photos" : []
        }
        self.port = -1
        self.osPath = "ArduinoRamps1.4\\OS.hex"
        self.pen_drop_down = PenDropDown()
        self.mode_drop_down = ModeDropDown()
        self.config = ConfigParser()

        #self.setting = Settings()
        #self.setting.add_json_panel('My custom panel', self.config, 'config.json')

        self.tuyeau_panel = self.ids.tuyeauInputs
        self.libre_panel = self.ids.libreInputs
        self.direct_panel = self.ids.directInputs
        self.inputs = {}
        self.mode = "Tuyeau"
        self.font = ".\\assets\\seguisym.ttf"

        # Specifique au mode 'Libre'
        self.lineWidth = 5
        self.diametre = 20
        self.dragging = -1
        self.zoom = 1
        self.margin = [-self.diametre/2-5, self.diametre/2+5, self.diametre/2+25, -self.diametre/2-25] # Left, Right, Top, Down
        self.corners = [(88, 87.5), (88, -87.5), (-90, 87.5), (-90, -87.5)]

        # Specifique au mode 'direct'
        self.board = -1
        self.clock = -1
        self.position = (0, 0)
        self.hasGoodProgram = False

        self.tuyeauMode()
        self.directMode()
        self.libreMode()
        Clock.schedule_once(self.binding)
        keyboard.on_release_key('shift', self.update_rect)

    def binding(self, *args):
        self.ids.pipeDrawing.bind(pos=self.update_rect, size=self.update_rect)
        self.tuyeauMode()
        self.update_rect()

    def poplb_update(self, *args):
        self.poplb.text_size = self.popup.size

    def help(self, *args):
        self.popup = Popup(title='Aide', size_hint=(0.7, 0.7))
        self.popbox = BoxLayout()
        self.poplb = Label(text='[u][size=20]Utilisation[/size][/u]\n\n \
                            1) Regler les [b]paramètres[/b] afin qu\'ils correspondent au système réel\n \
                            2) Connectez le système à l\'[b]ordinateur[/b]\n \
                            3) Selectioner le [b]port[b] de l\'arduino dans le menu\n \
                            4) Vous pouvez maintenant clicker sur [b]Update[/b]\n \
                            5) Finalement apuyez sur le bouton de [b]démarrage[/b] pour commencer l\'aquisition\n\n\n \
                            Code disponible [ref=https://github.com/liamLatour/DaphnieMaton][color=0083ff][u]ici[/u][/color][/ref] pour signaler un bug',
                            text_size=self.popup.size,
                            strip=True,
                            valign='top',
                            padding= (15, 35),
                            markup = True)
        self.poplb.bind(on_ref_press=urlOpen)
        self.popup.bind(size=self.poplb_update)

        self.popbox.add_widget(self.poplb)
        self.popup.content = self.popbox
        self.popup.open()

    def show_mode(self):
        self.mode_drop_down.open(self.ids.mode_button)
        self.mode_drop_down.clear_widgets()
        
        self.mode_drop_down.add_widget(Button(text="Tuyeau", height=48, size_hint_y= None, on_release=lambda a:self.change_mode("Tuyeau")))
        self.mode_drop_down.add_widget(Button(text="Libre", height=48, size_hint_y= None, on_release=lambda a:self.change_mode("Libre")))
        self.mode_drop_down.add_widget(Button(text="Direct", height=48, size_hint_y= None, on_release=lambda a:self.change_mode("Direct")))

    def show_port(self):
        self.pen_drop_down.open(self.ids.port_button)
        self.pen_drop_down.clear_widgets()

        self.pen_drop_down.add_widget(Button(text="Aucun port", height=48, size_hint_y= None, on_release=lambda a:self.change_port(-1)))
        arduinoPorts = getPorts()
        for port in arduinoPorts:
            self.pen_drop_down.add_widget(Button(text="COM"+str(arduinoPorts[port]), height=48, size_hint_y= None, on_release=lambda a:self.change_port(arduinoPorts[port])))

    def change_port(self, nb):
        self.port = nb
        if nb>= 0:
            self.ids.port_button.text = "Port " + str(nb)
        else:
            self.ids.port_button.text = "Port"
        self.pen_drop_down.dismiss()

    # Saving and loading system
    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def show_save(self):
        content = SaveDialog(save=self.save, cancel=self.dismiss_popup)
        self._popup = Popup(title="Save file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()    

    def load(self, path, filename):
        with open(os.path.join(path, filename[0])) as stream:
            self.params = json.load(stream)

        self.change_mode("Tuyeau")
        self.dismiss_popup()

    def save(self, path, filename):
        with open(os.path.join(path, filename+".json"), 'w') as stream:
            paramsCopy = self.params.copy()
            try: paramsCopy["gaps"] = paramsCopy["gaps"].tolist()
            except: pass

            try: paramsCopy["trace"] = paramsCopy["trace"].tolist()
            except: pass

            try: paramsCopy["photos"] = paramsCopy["photos"].tolist()
            except: pass

            stream.write(json.dumps( paramsCopy ))

        self.dismiss_popup()

    def readFromSerial(self, *args):
        if self.port != -1:
            self.moveDirect(bytes([9]))
            x = self.board.readline().decode("utf-8").rstrip()
            y = self.board.readline().decode("utf-8").rstrip()
            self.position = (x, y)
            self.ids.infoLabel.text = "X: " + str(self.position[0]) + " step" + \
                                      "\nY: " + str(self.position[1]) + " step"

    def update(self, *args):
        self.popup = Popup(title='Téléversement', content=AsyncImage(source='.\\assets\\logo.png', size=(100, 100)), size_hint=(None, None), size=(400, 300), auto_dismiss=False)
        self.popup.open()
        if self.clock != -1:
            self.clock.cancel()
            self.clock = -1
        threading.Thread(target=self.updateAsync).start()
        
    def updateAsync(self):
        generateFile(self.params["trace"], self.params["photos"])
        if self.port != -1:
            try:
                self.board.close()
                self.board = -1
            except: pass
            if self.mode == "Direct":
                os.system(".\\arduino-1.8.9\\arduino_debug --board arduino:avr:mega:cpu=atmega2560 --port COM"+str(self.port)+" --upload .\\directFile\\directFile.ino")            
                self.hasGoodProgram = True
                self.update_rect()
                self.clock = Clock.schedule_interval(self.readFromSerial, 0.2)
            else:
                generateFile(self.params["trace"], self.params["photos"])
                os.system(".\\arduino-1.8.9\\arduino_debug --board arduino:avr:mega:cpu=atmega2560 --port COM"+str(self.port)+" --upload .\\currentFile\\currentFile.ino")
                self.hasGoodProgram = False
            print("DONE !")
            self.popup.dismiss()
            Popup(title='Succès !', content=Label(text='Le programme à bien été graver !'), size_hint=(None, None), size=(400, 300)).open()
        else:
            self.popup.dismiss()
            Popup(title='Absence de port', content=Label(text='Un port doit être précisé'), size_hint=(None, None), size=(400, 300)).open()

    # Drawing on canvas
    def update_rect(self, *args):
        self.mode = self.ids.lol.current_tab.text


        self.ids.canvasSplitter.max_size = self.size[0] - 400
        self.zoomClamp()
        middle = (self.ids.pipeDrawing.center_x, self.ids.pipeDrawing.center_y)
        self.ids.directDrawing.clear_widgets()
        self.ids.pipeDrawing.canvas.before.clear()
        self.ids.pipeDrawing.canvas.after.clear()

        if "nbPipe" in self.inputs and self.mode == "Tuyeau":
            gapsValue = []
            if bool(self.inputs["sameGap"].input.active):
                gapsValue = np.ones(max(int(self.inputs["nbPipe"].input.text), 1)-1) * float(self.inputs["gaps"][0].input.text)
            else:
                for gap in self.inputs["gaps"]:
                    gapsValue.append(float(gap.input.text))

            if len(gapsValue) == 0:
                gapsValue = [20]

            self.params["nbPipe"] = max(int(self.inputs["nbPipe"].input.text), 1)
            self.params["lenPipe"] = max(float(self.inputs["lenPipe"].input.text), 0.1)
            self.params["timePipe"] = float(self.inputs["timePipe"].input.text)
            self.params["photoPipe"] = max(float(self.inputs["photoPipe"].input.text), 1)
            self.params["constGap"] = bool(self.inputs["sameGap"].input.active)
            self.params["gaps"] = gapsValue

            shift = (self.params["nbPipe"] * 10 + np.sum(self.params["gaps"]))

            try:
                self.ids.canvasSplitter.min_size = max(int(round(shift+50)), 200)
            except:
                self.ids.canvasSplitter.min_size = round(self.size[0] - 400)

            with self.ids.pipeDrawing.canvas.before:
                self.ids.infoLabel.pos = (self.size[0]-200, self.size[1] - 200)
                self.ids.infoLabel.text = "Temps totale: " + str(self.params["timePipe"]*self.params["nbPipe"]) + " sec" + \
                                        "\nNombre photo: " + str( round((self.params["nbPipe"]*self.params["lenPipe"])/(self.params["photoPipe"]/100))) + \
                                        "\nPhoto toutes les " + str( round( ((self.params["timePipe"]*self.params["nbPipe"]) / ((self.params["nbPipe"]*self.params["lenPipe"])/(self.params["photoPipe"]/100)))*10 )/10 ) + " sec"

                Color(1,1,1, .2)
                Rectangle(pos = (self.size[0]-200, self.size[1] - (70 +50)), size = (200, 70))

                height = max(100, self.size[1]/2)
                Color(1,1,1)

                curX = middle[0] - shift/2

                Rectangle(pos = (curX, middle[1]-height/2), size = (10, height))

                for x in range(self.params["nbPipe"]-1):
                    curX += 10+self.params["gaps"][x]
                    Rectangle(pos = (curX, middle[1]-height/2), size = (10, height))

        elif self.mode == "Direct":
            self.ids.infoLabel.text = ""
            buttonSize = min(self.ids.canvasSplitter.size[0]/4, self.ids.canvasSplitter.size[1]/4)
            fontSize = min(self.ids.canvasSplitter.size[0]/20, self.ids.canvasSplitter.size[1]/20)

            raz = Button(text='RAZ', font_size=fontSize, pos = (middle[0]-buttonSize/2, middle[1]-buttonSize/2), size = (buttonSize, buttonSize))

            right = Button(text=u'\u23E9', font_size=fontSize, font_name=self.font, pos = (middle[0]+buttonSize+5-buttonSize/2, middle[1]-buttonSize/2), size = (buttonSize, buttonSize))
            left = Button(text=u'\u23EA', font_size=fontSize, font_name=self.font, pos = (middle[0]-buttonSize-5-buttonSize/2, middle[1]-buttonSize/2), size = (buttonSize, buttonSize))
            up = Button(text=u'\u23EB', font_size=fontSize, font_name=self.font, pos = (middle[0]-buttonSize/2, middle[1]+buttonSize+5-buttonSize/2), size = (buttonSize, buttonSize))
            down = Button(text=u'\u23EC', font_size=fontSize, font_name=self.font, pos = (middle[0]-buttonSize/2, middle[1]-buttonSize-5-buttonSize/2), size = (buttonSize, buttonSize))

            raz.bind(on_press=partial(self.moveDirect, bytes([0])))
            raz.bind(on_release=partial(self.moveDirect, bytes([10])))

            right.bind(on_press=partial(self.moveDirect, bytes([1])))
            right.bind(on_release=partial(self.moveDirect, bytes([5])))
            left.bind(on_press=partial(self.moveDirect, bytes([2])))
            left.bind(on_release=partial(self.moveDirect, bytes([6])))
            up.bind(on_press=partial(self.moveDirect, bytes([3])))
            up.bind(on_release=partial(self.moveDirect, bytes([7])))
            down.bind(on_press=partial(self.moveDirect, bytes([4])))
            down.bind(on_release=partial(self.moveDirect, bytes([8])))

            self.ids.directDrawing.add_widget(raz)

            self.ids.directDrawing.add_widget(right)
            self.ids.directDrawing.add_widget(left)
            self.ids.directDrawing.add_widget(up)
            self.ids.directDrawing.add_widget(down)

            with self.ids.pipeDrawing.canvas.before:
                self.ids.infoLabel.pos = (self.size[0]-200, self.size[1] - 200)
                self.ids.infoLabel.text = "X: " + str(self.position[0]) + " step" + \
                                        "\nY: " + str(self.position[1]) + " step"

                Color(1,1,1, .2)
                Rectangle(pos = (self.size[0]-200, self.size[1] - (70 +50)), size = (200, 70))

            if not self.hasGoodProgram:
                with self.ids.pipeDrawing.canvas.after:
                    dimensionX = self.ids.canvasSplitter.size[0]
                    dimensionY = self.ids.canvasSplitter.size[1] - 50
                    Color(1, 1, 1, 0.5)
                    Rectangle(pos=(middle[0]-dimensionX/2, middle[1]-dimensionY/2), size=(dimensionX, dimensionY))
                    label = CoreLabel(text="Clicker sur 'Update' avant", font_size=100, halign='middle', valign='middle', padding=(12, 12))
                    label.refresh()
                    text = label.texture
                    Color(0, 0, 0, 1)
                    Rectangle(pos=(middle[0]-dimensionX/2, middle[1]-(dimensionX*(3/16))/2), size=(dimensionX, dimensionX*(3/16)), texture=text)

        elif self.mode == "Libre":
            self.ids.canvasSplitter.min_size = int(round(self.size[0]/2))
            zoomedTrace = np.multiply(self.params["trace"], self.zoom).tolist()

            with self.ids.pipeDrawing.canvas.before:
                width = 200 * self.zoom
                Rectangle(source='.\\assets\\topDownView.png', pos = (middle[0]-width/2, middle[1]-width/2), size = (width, width))

                if keyboard.is_pressed("shift"):
                    for corner in self.corners:
                        Color(0, 1, 0, 0.8)
                        Ellipse(pos=(corner[0]*self.zoom+middle[0]-self.diametre/2, corner[1]*self.zoom+middle[1]-self.diametre/2), size=(self.diametre, self.diametre))

                if len(zoomedTrace) > 0:
                    if len(zoomedTrace) > 4:
                        isLoop = bool(self.inputs["loop"].input.active)
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
                        Color(1, 0.8, 0, 0.8)
                        Ellipse(pos=(zoomedTrace[i*2]+middle[0]-self.diametre/2, zoomedTrace[i*2+1]+middle[1]-self.diametre/2), size=(self.diametre, self.diametre))
                        label = CoreLabel(text=str(i+1), font_size=20)
                        label.refresh()
                        text = label.texture
                        Color(0, 0, 0, 1)
                        Ellipse(pos=(zoomedTrace[i*2]+middle[0]-self.diametre/2, zoomedTrace[i*2+1]+middle[1]-self.diametre/2), size=(self.diametre, self.diametre), texture=text)

                self.ids.infoLabel.text = ""
                Color(1, 1, 1, 0.2)
                Rectangle(pos = (self.size[0]-200, self.size[1] - (70 +50)),
                                                        size = (200, 70))

    def moveDirect(self, direction, *args):
        if self.port != -1:
            try:
                self.board.write(direction)
            except:
                self.board = serial.Serial('COM'+str(self.port), 9600, timeout=0.5)
                time.sleep(2)
                self.board.write(direction)
    
    def clickedDown(self, touch):
        if self.mode == "Libre":
            x = touch.x
            y = touch.y
            zoomedTrace = np.multiply(self.params["trace"], self.zoom).tolist()

            if self.ids.pipeDrawing.collide_point(x, y):
                for i in range(int(len(zoomedTrace)/2)):
                    if hypot(zoomedTrace[i*2]+self.ids.pipeDrawing.center_x - x, zoomedTrace[i*2+1]+self.ids.pipeDrawing.center_y - y) <= self.diametre/2:
                        if touch.button == 'right':
                            del self.params["trace"][i*2+1]
                            del self.params["trace"][i*2]
                            del self.params["photos"][i]
                            self.update_rect()
                        elif touch.button == 'left':
                            self.dragging = i
                        return
                if touch.button == 'left':
                    self.params["trace"].append((x-self.ids.pipeDrawing.center_x)/self.zoom)
                    self.params["trace"].append((y-self.ids.pipeDrawing.center_y)/self.zoom)
                    self.params["photos"].append(False)
                    self.update_rect()
                elif touch.button == 'right':
                    # Check if we clicked on a line or not
                    for i in range(int(len(zoomedTrace)/2)-1):
                        firstPoint = (zoomedTrace[i*2]+self.ids.pipeDrawing.center_x, zoomedTrace[i*2+1]+self.ids.pipeDrawing.center_y)
                        secondPoint = (zoomedTrace[(i+1)*2]+self.ids.pipeDrawing.center_x, zoomedTrace[(i+1)*2+1]+self.ids.pipeDrawing.center_y)
                        if hitLine(firstPoint, secondPoint, (x, y), self.lineWidth):
                            self.params["photos"][i] = not self.params["photos"][i]
                            self.update_rect()
                            return
                    if bool(self.inputs["loop"].input.active):
                        firstPoint = (zoomedTrace[len(zoomedTrace)-2]+self.ids.pipeDrawing.center_x, zoomedTrace[len(zoomedTrace)-1]+self.ids.pipeDrawing.center_y)
                        secondPoint = (zoomedTrace[0]+self.ids.pipeDrawing.center_x, zoomedTrace[1]+self.ids.pipeDrawing.center_y)
                        if hitLine(firstPoint, secondPoint, (x, y), self.lineWidth):
                            self.params["photos"][len(self.params["photos"])-1] = not self.params["photos"][len(self.params["photos"])-1]
                            self.update_rect()
                elif touch.is_mouse_scrolling:
                    dist = 0.1 if touch.button == 'scrollup' else -0.1
                    self.zoom += dist
                    self.zoomClamp()
                    self.update_rect()

    def clickedUp(self, touch):
        if self.mode == "Libre":
            if touch.button == 'left':
                self.dragging = -1
            if self.zoom == 0.05:
                self.positionClamp()
                self.update_rect()
    
    def clickedMove(self, touch):
        if self.mode == "Libre":
            if touch.button == 'left' and self.dragging != -1:
                thisX = (touch.x-self.ids.pipeDrawing.center_x)/self.zoom
                thisY = (touch.y-self.ids.pipeDrawing.center_y)/self.zoom

                if keyboard.is_pressed("ctrl") and len(self.params["trace"]) > 2: # To clamp relative to last one (right angles)
                    fromWhich = self.dragging-1 % len(self.params["trace"])
                    previousPoint = (self.params["trace"][(fromWhich)*2], self.params["trace"][(fromWhich)*2+1])

                    if distance.euclidean(previousPoint, (thisX, 0)) < distance.euclidean(previousPoint, (0, thisY)):
                        self.params["trace"][self.dragging*2] = previousPoint[0]
                        self.params["trace"][self.dragging*2+1] = thisY
                    else:
                        self.params["trace"][self.dragging*2] = thisX
                        self.params["trace"][self.dragging*2+1] = previousPoint[1]
                
                elif keyboard.is_pressed("shift"): # To clamp to the corners (origin, top-right, ...)
                    dist1 = distance.euclidean(self.corners[0], (thisX, thisY))
                    dist2 = distance.euclidean(self.corners[1], (thisX, thisY))
                    dist3 = distance.euclidean(self.corners[2], (thisX, thisY))
                    dist4 = distance.euclidean(self.corners[3], (thisX, thisY))

                    indice = np.argmin(np.array([dist1, dist2, dist3, dist4]))

                    self.params["trace"][self.dragging*2] = self.corners[indice][0]
                    self.params["trace"][self.dragging*2+1] = self.corners[indice][1]

                else:
                    self.params["trace"][self.dragging*2] = thisX
                    self.params["trace"][self.dragging*2+1] = thisY

                self.update_rect()

    def positionClamp(self):
        maxPosLeft = (-self.ids.canvasSplitter.size[0]/2-self.margin[0])/(self.zoom)
        maxPosRight = (self.ids.canvasSplitter.size[0]/2-self.margin[1])/(self.zoom)
        maxPosTop = (self.ids.canvasSplitter.size[1]/2-self.margin[2])/(self.zoom)
        maxPosDown = (-self.ids.canvasSplitter.size[1]/2-self.margin[3])/(self.zoom)

        for i in range(int(len(self.params["trace"])/2)):
            self.params["trace"][i*2] = min(max(self.params["trace"][i*2], maxPosLeft), maxPosRight)
            self.params["trace"][i*2+1] = min(max(self.params["trace"][i*2+1], maxPosDown), maxPosTop)
                
    def zoomClamp(self):
        size = self.ids.canvasSplitter.size
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

    def tuyeauMode(self):
        if self.clock != -1:
            self.clock.cancel()
            self.clock = -1
            
        self.tuyeau_panel.clear_widgets()

        self.inputs["nbPipe"] = Input(name='Nombre de tuyeau', input_filter="int", default_text=str(self.params["nbPipe"]), callback=self.tuyeauGap)
        self.inputs["lenPipe"] = Input(name='Taille des tuyeaux (m)', input_filter="float", default_text=str(self.params["lenPipe"]), callback=self.update_rect)
        self.inputs["timePipe"] = Input(name='Temps pour un tuyeau (sec)', input_filter="float", default_text=str(self.params["timePipe"]), callback=self.update_rect)
        self.inputs["photoPipe"] = Input(name='Centim\u00e9tre par photo', input_filter="float", default_text=str(self.params["photoPipe"]), callback=self.update_rect)
        self.inputs["sameGap"] = Input(name='Ecart constant', inputType=1, default_text=str(self.params["constGap"]), callback=self.tuyeauGap)

        self.tuyeau_panel.add_widget(self.inputs["nbPipe"])
        self.tuyeau_panel.add_widget(self.inputs["lenPipe"])
        self.tuyeau_panel.add_widget(self.inputs["timePipe"])
        self.tuyeau_panel.add_widget(self.inputs["photoPipe"])
        self.tuyeau_panel.add_widget(self.inputs["sameGap"])
        self.tuyeauGap()
    
    def tuyeauGap(self, *args):
        if "gaps" in self.inputs:
            for gap in self.inputs["gaps"]:
                self.tuyeau_panel.remove_widget(gap)

        if bool(self.inputs["sameGap"].input.active):
            self.inputs["gaps"] = [Input(name='Ecart entre tuyeau (cm)', input_filter="float", default_text=str(self.params["gaps"][0]), callback=self.update_rect)]
            self.tuyeau_panel.add_widget(self.inputs["gaps"][0])
        else:
            self.inputs["gaps"] = []
            for pipe in range(max(int(self.inputs["nbPipe"].input.text), 1)-1):
                try:
                    default = str(self.params["gaps"][pipe])
                except:
                    default = str(self.params["gaps"][0])   

                self.inputs["gaps"].append(Input(name='Ecart entre tuyeau (cm)', input_filter="float", default_text=default, callback=self.update_rect))
                self.tuyeau_panel.add_widget(self.inputs["gaps"][pipe])

        self.update_rect()
    
    def libreMode(self):
        if self.clock != -1:
            self.clock.cancel()
            self.clock = -1

        self.libre_panel.clear_widgets()

        self.inputs["loop"] = Input(name='Boucle', inputType=1, default_text=str(self.params["loop"]), callback=self.update_rect)

        self.libre_panel.add_widget(self.inputs["loop"])
        self.zoom = float('inf')
        self.zoomClamp()

    def directMode(self):
        self.direct_panel.clear_widgets()
        self.clock = Clock.schedule_interval(self.readFromSerial, 0.2)


class DaphnieMatonApp(App):
    def build(self):
        return Parametrage()

if __name__ == '__main__':
    DaphnieMatonApp().run()
