from kivy.app import App
from kivy.lang import Builder
from kivy.config import Config
from kivy.clock import Clock

from kivy.factory import Factory
from kivy.properties import ObjectProperty

from kivy.uix.actionbar import ActionDropDown
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.label import Label

from kivy.graphics import Rectangle
from kivy.graphics import Color

import serial.tools.list_ports
import json
import re
import os

# TODO: when building the save and load crashs

Config.set('kivy','window_icon','logo.ico')
Builder.load_file('main.kv')


def getPorts():
    ports = list(serial.tools.list_ports.comports())
    arduinoPorts = {}
    for p in ports:
        match = re.search(r'COM(\d+)', str(p))
        if match:
            arduinoPorts[str(p)] = int(match.group(1))

    return arduinoPorts

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)

class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)

class PenDropDown(ActionDropDown):
    pass

class Parametrage(BoxLayout):
    def __init__(self, *args, **kwargs):
        super(Parametrage, self).__init__(*args, **kwargs)
        self.params = {
            "nbPipe": 2,
            "lenPipe" : 1.2,
            "timePipe" : 10,
            "photoPipe" : 0.5
        }
        self.port = -1
        self.osPath = "ArduinoRamps1.4\\OS.hex"
        self.pen_drop_down = PenDropDown()
        Clock.schedule_once(self.binding)

    def binding(self, *args):
        self.ids.pipeDrawing.bind(pos=self.update_rect, size=self.update_rect)
        self.update_rect()

    def poplb_update(self, *args):
        self.poplb.text_size = self.popup.size

    def urlOpen(self, instance, value):
        import webbrowser
        webbrowser.open(value, new=2)

    def help(self, *args):
        self.popup = Popup(title='Aide', size_hint=(0.7, 0.7))
        self.popbox = BoxLayout()
        self.poplb = Label(text='[u][size=20]Utilisation[/size][/u]\n\n \
                            1) Regler les [b]paramètres[/b] afin qu\'ils correspondent au système réel\n \
                            2) Connectez le système à l\'[b]ordinateur[/b]\n \
                            3) Si le système n\'a pas la dernière version de l\'OS clickez sur [b]Flasher[/b]\n \
                            4) Vous pouvez maintenant clicker sur [b]Update[/b]\n \
                            5) Finalement apuyez sur le bouton de [b]démarrage[/b] pour commencer l\'aquisition\n\n\n \
                            Code disponible [ref=https://github.com/liamLatour/DaphnieMaton][color=0083ff][u]ici[/u][/color][/ref] pour signaler un bug',
                            text_size=self.popup.size,
                            strip=True,
                            valign='top',
                            padding= (15, 35),
                            markup = True)
        self.poplb.bind(on_ref_press=self.urlOpen)
        self.popup.bind(size=self.poplb_update)

        self.popbox.add_widget(self.poplb)
        self.popup.content = self.popbox
        self.popup.open()
    
    # Saving and loading system
    def dismiss_popup(self):
        self._popup.dismiss()

    def show_port(self):
        self.pen_drop_down.open(self.ids.port_button)
        self.pen_drop_down.clear_widgets()

        self.pen_drop_down.add_widget(Button(text="Aucun port", height=48, size_hint_y= None, on_release=lambda a:self.changePort(-1)))
        arduinoPorts = getPorts()
        for port in arduinoPorts:
            self.pen_drop_down.add_widget(Button(text="COM"+str(arduinoPorts[port]), height=48, size_hint_y= None, on_release=lambda a:self.changePort(arduinoPorts[port])))

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
    
    def changePort(self, nb):
        self.port = nb
        if nb>= 0:
            self.ids.port_button.text = "Port " + str(nb)
        else:
            self.ids.port_button.text = "Port"
        self.pen_drop_down.dismiss()

    def load(self, path, filename):
        
        with open(os.path.join(path, filename[0])) as stream:
            self.params = json.load(stream)
            self.ids.nbPipe.text = str(self.params["nbPipe"])
            self.ids.lenPipe.text = str(self.params["lenPipe"])
            self.ids.timePipe.text = str(self.params["timePipe"])
            self.ids.photoPipe.text = str(self.params["photoPipe"]*100)

        self.update_rect()
        self.dismiss_popup()

    def save(self, path, filename):
        with open(os.path.join(path, filename+".json"), 'w') as stream:
            stream.write(json.dumps( self.params ))

        self.dismiss_popup()


    def update(self, *args):
        print(self.params)

    def flash(self, *args):
        os.system('arduino-1.8.8\\hardware\\tools\\avr\\bin\\avrdude -Carduino-1.8.8\\hardware\\tools\\avr/etc/avrdude.conf -v -patmega2560 -cwiring -PCOM'+str(self.port)+' -b115200 -D -Uflash:w:'+self.osPath+':i')


    # Drawing on canvas
    def update_rect(self, *args):
        self.params = {
            "nbPipe": max(int(self.ids.nbPipe.text), 1),
            "lenPipe" : float(self.ids.lenPipe.text),
            "timePipe" : float(self.ids.timePipe.text),
            "photoPipe" : float(self.ids.photoPipe.text)/100,
        }

        self.ids.pipeDrawing.canvas.before.clear()

        if self.size[0] > 1.75*400:
            self.ids.canvasSplitter.min_size = max(self.params["nbPipe"] * 15 + 25, self.size[0]/2.5)
        else:
            self.ids.canvasSplitter.min_size = max(self.params["nbPipe"] * 15 + 25, 200)

        self.ids.canvasSplitter.max_size = self.size[0] - 400


        self.ids.infoLabel.pos = (self.size[0]-200, self.size[1] - 200)
        self.ids.infoLabel.text = "Temps totale: " + str(self.params["timePipe"]*self.params["nbPipe"]) + " sec" + \
                                  "\nNombre photo: " + str( round((self.params["nbPipe"]*self.params["lenPipe"])/self.params["photoPipe"])) + \
                                  "\nPhoto toutes les " + str( round( ((self.params["timePipe"]*self.params["nbPipe"]) / ((self.params["nbPipe"]*self.params["lenPipe"])/self.params["photoPipe"]))*10 )/10 ) + " sec"

        self.ids.pipeDrawing.canvas.before.add(Color(1,1,1, .2))
        self.ids.pipeDrawing.canvas.before.add(Rectangle(pos = (self.size[0]-200, self.size[1] - (70 +50)),
                                                  size = (200, 70)))

        shift = (self.params["nbPipe"] * 15) /2
        height = max(100, self.size[1]/2)
        self.ids.pipeDrawing.canvas.before.add(Color(1,1,1))

        for x in range(self.params["nbPipe"]):
            self.ids.pipeDrawing.canvas.before.add(
                Rectangle(pos = (self.ids.pipeDrawing.center_x + x*20 - shift + 2.5, self.ids.pipeDrawing.center_y-height/2),
                          size = (10, height)))


class TutorialApp(App):  
#the kv file name will be Tutorial (name is before the "App")
    def build(self):
        return Parametrage()

TutorialApp().run()