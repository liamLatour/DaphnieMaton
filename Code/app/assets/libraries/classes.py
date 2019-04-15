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
from kivy.uix.image import Image
from kivy.uix.settings import SettingItem
from kivy.uix.button import Button

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

class SettingButtons(SettingItem):

    def __init__(self, **kwargs):
        self.register_event_type('on_release')
        self.panel = kwargs["panel"]
        super(SettingItem, self).__init__(title=kwargs["title"], desc=kwargs["desc"], section=kwargs["section"], key=kwargs["key"])#**kwargs
        for aButton in kwargs["buttons"]:
            oButton=Button(text=aButton['title'], font_size= '15sp')
            oButton.ID=aButton['id']
            self.add_widget(oButton)
            oButton.bind (on_release=self.On_ButtonPressed)
    def On_ButtonPressed(self,instance):
        self.panel.settings.dispatch('on_config_change',self.panel.config, self.section, self.key, instance.ID)

class MyLabel(Image):
    text = StringProperty('')

    def on_text(self, *_):
        l = Label(text=self.text, valign='middle', halign='justify', padding= (15, 35), markup = True)
        l.font_size = '50'
        l.texture_update()
        # Set it to image, it'll be scaled to image size automatically:
        self.texture = l.texture

class Input(BoxLayout):
    """Custom input to handle parameters.

    inputName string: the name.
    input_filter string: filter for numeric values (int, float, ...).
    default_text string: text to be displayed at startup.
    callback funct: function to call when it changes.
    inputType int: Text or switch (0 or 1).

    returns: the BoxLayout object.
    """

    inputName = StringProperty('default')
    input_filter = StringProperty(None)
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
    """Used to gather every connected devices on usb.

    returns: list of found devices on COM ports.
    """
    ports = list(serial.tools.list_ports.comports())
    arduinoPorts = {}
    for p in ports:
        match = re.search(r'COM(\d+)', str(p))
        if match:
            arduinoPorts[str(p)] = int(match.group(1))

    return arduinoPorts

def urlOpen(instance, url):
    """Opens a browser window with specified url.

    url string: the website to go to.
    """
    import webbrowser
    webbrowser.open(url, new=2)

def hitLine(lineA, lineB, point, lineWidth):
    """Checks whether the point is in line or out.

    lineA tuple: a point of the line.
    lineB tuple: another point of the line.
    point tuple: point we want to check.
    lineWidth tuple: width of the line.

    returns: True if in and False if out.
    """
    numerator = abs((lineB[1]-lineA[1])*point[0]-(lineB[0]-lineA[0])*point[1]+lineB[0]*lineA[1]-lineB[1]*lineA[0])
    denominator = sqrt(pow(lineB[1]-lineA[1], 2)+pow(lineB[0]-lineA[0], 2))
    if denominator == 0:
        denominator = 0.00001
    if numerator/denominator <= lineWidth:
        if distance.euclidean(lineA, point) < distance.euclidean(lineA, lineB) and distance.euclidean(lineB, point) < distance.euclidean(lineA, lineB):
            return True
    return False

def polToCar(center, dist, angle):
    """Converts polar coordinates to cartesian.

    center tuple: center of the local system.
    dist float: distance from the center to the point.
    angle float: angle in radian.

    returns: a tuple representing the X and Y -> (x, y)
    """
    return (cos(angle)*dist+center[0], sin(angle)*dist + center[1])
