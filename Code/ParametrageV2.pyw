from kivy.app import App
from kivy.lang import Builder
from kivy.config import Config
from kivy.clock import Clock

from kivy.factory import Factory
from kivy.properties import ObjectProperty

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label

from kivy.graphics import Rectangle
from kivy.graphics import Color

import json
import os

Config.set('kivy','window_icon','kv/logo.ico')

kv_path = './kv/'
for kv in os.listdir(kv_path):
    if '.kv' in kv:
        Builder.load_file(kv_path+kv)


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)

class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)

class Parametrage(BoxLayout):
    def __init__(self, *args, **kwargs):
        super(Parametrage, self).__init__(*args, **kwargs)
        self.params = {
            "nbPipe": 2,
            "lenPipe" : 1.2,
            "timePipe" : 10,
            "photoPipe" : 0.5
        }
        Clock.schedule_once(self.binding)

    def binding(self, *args):
        self.ids.pipeDrawing.bind(pos=self.update_rect, size=self.update_rect)
        self.update_rect()

    def help(self, *args):
        popup = Popup(title='Aide', content=Label(text='Hello world'), size_hint=(0.7, 0.7))
        popup.open()
    
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
            print(self.params)

        self.update_rect()
        self.dismiss_popup()

    def save(self, path, filename):
        with open(os.path.join(path, filename+".json"), 'w') as stream:
            stream.write(json.dumps( self.params ))

        self.dismiss_popup()

    # Drawing on canvas
    def update_rect(self, *args):
        self.params = {
            "nbPipe": max(int(self.ids.nbPipe.text), 1),
            "lenPipe" : float(self.ids.lenPipe.text),
            "timePipe" : float(self.ids.timePipe.text),
            "photoPipe" : float(self.ids.photoPipe.text)/100
        }

        self.ids.pipeDrawing.canvas.before.clear()

        self.ids.canvasSplitter.min_size = max(self.params["nbPipe"] * 15 + 25, 200)
        self.ids.canvasSplitter.max_size = self.size[0] - 400

        self.ids.infoLabel.pos = (self.size[0]-200, self.size[1] - 200)
        self.ids.infoLabel.text = "Temps totale: " + str(self.params["timePipe"]*self.params["nbPipe"]) + " sec" + \
                                  "\nNombre photo: " + str( round((self.params["nbPipe"]*self.params["lenPipe"])/self.params["photoPipe"])) + \
                                  "\nPhoto toutes les " + str( round( ((self.params["timePipe"]*self.params["nbPipe"]) / ((self.params["nbPipe"]*self.params["lenPipe"])/self.params["photoPipe"]))*10 )/10 ) + " sec"

        self.ids.pipeDrawing.canvas.before.add(Color(1,1,1, .2))
        self.ids.pipeDrawing.canvas.before.add(Rectangle(pos = (self.size[0]-200, self.size[1] - 150),
                                                  size = (200, 100)))

        shift = (self.params["nbPipe"] * 15) /2
        self.ids.pipeDrawing.canvas.before.add(Color(1,1,1))

        for x in range(self.params["nbPipe"]):
            self.ids.pipeDrawing.canvas.before.add(
                Rectangle(pos = (self.ids.pipeDrawing.center_x + x*15 - shift + 2.5,
                                 self.ids.pipeDrawing.center_y-50), size = (10, 100)))


class TutorialApp(App):  
#the kv file name will be Tutorial (name is before the "App")
    def build(self):
        return Parametrage()

TutorialApp().run()