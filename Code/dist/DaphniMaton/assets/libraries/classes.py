import re
from math import cos, pow, sin, sqrt

import serial.tools.list_ports
from kivy.clock import Clock
from kivy.properties import (ConfigParserProperty, NumericProperty,
                             ObjectProperty, StringProperty)
from kivy.uix.actionbar import ActionDropDown
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.switch import Switch
from kivy.uix.textinput import TextInput
from scipy.spatial import distance


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    path = StringProperty("C:/")

class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)
    path = StringProperty("C:/")

class PenDropDown(ActionDropDown):
    pass

class ModeDropDown(ActionDropDown):
    pass

class Input(BoxLayout):
    inputName = StringProperty('default')
    input_filter = StringProperty('default')
    default_text = StringProperty('default')
    callback = ObjectProperty(None, rebind=True)
    inputType = NumericProperty(0)

    def __init__(self, **kwargs):
        super(Input, self).__init__(**kwargs)
        if self.callback != None and self.callback != '':
            self.after_init()
        else:
            # Have to wait if declared in .kv because the properties are not set before init
            Clock.schedule_once(self.after_init)        

    def after_init(self, *args):
        self.label = Label(text=self.inputName)
        self.add_widget(self.label)

        if self.inputType == 0:
            self.input = TextInput(text=self.default_text, multiline=False, input_filter=self.input_filter)
            if self.callback != None and self.callback != '':
                self.input.bind(on_text_validate=lambda *args: self.callback())
            self.add_widget(self.input)
        elif self.inputType == 1:
            self.input = Switch(active=self.default_text=="True")
            if self.callback != None and self.callback != '':
                self.input.bind(active=lambda *args: self.callback())
            self.add_widget(self.input)

def getPorts():
    ports = list(serial.tools.list_ports.comports())
    arduinoPorts = {}
    for p in ports:
        match = re.search(r'COM(\d+)', str(p))
        if match:
            arduinoPorts[str(p)] = int(match.group(1))

    return arduinoPorts

def urlOpen(instance, value):
    import webbrowser
    webbrowser.open(value, new=2)

def hitLine(lineA, lineB, point, lineWidth):
    numerator = abs((lineB[1]-lineA[1])*point[0]-(lineB[0]-lineA[0])*point[1]+lineB[0]*lineA[1]-lineB[1]*lineA[0])
    denominator = sqrt(pow(lineB[1]-lineA[1], 2)+pow(lineB[0]-lineA[0], 2))
    if denominator == 0:
        denominator = 0.00001
    if numerator/denominator <= lineWidth:
        if distance.euclidean(lineA, point) < distance.euclidean(lineA, lineB) and distance.euclidean(lineB, point) < distance.euclidean(lineA, lineB):
            return True
    return False

def polToCar(center, dist, angle):
    return (cos(angle)*dist+center[0], sin(angle)*dist + center[1])
