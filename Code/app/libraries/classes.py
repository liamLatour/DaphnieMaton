import json
import sys
import threading
import time

sys.argv = sys.argv if __name__ == '__main__' else [sys.argv[0]]

import keyboard
import kivy.utils as utils
import serial.tools.list_ports
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import NumericProperty, ObjectProperty, StringProperty
from kivy.uix.actionbar import ActionDropDown
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.settings import SettingItem
from kivy.uix.switch import Switch
from kivy.uix.textinput import TextInput

from .localization import _



class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    path = StringProperty("C:/")


class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)
    path = StringProperty("C:/")


class ActionChoosing(FloatLayout):
    newAction = ObjectProperty(None)
    cancel = ObjectProperty(None)
    chose = ObjectProperty(None)
    actions = StringProperty("{}")

    def __init__(self, **kwargs):
        super(ActionChoosing, self).__init__(**kwargs)
        # Have to wait if declared in .kv because the properties are not set before init
        Clock.schedule_once(self.after_init)

    def after_init(self, *args):
        self.bind(size=self.updateGrid, pos=self.updateGrid)
        self.createGrid()

    def updateGrid(self, *args):
        self.ids.box.remove_widget(self.scrollView)
        self.createGrid()

    def createGrid(self, *args):
        self.scrollView = ScrollView(size_hint=(1, 1))
        grid = CustomGrid(cols=max(round(self.size[0]/150-0.5), 1))
        actions = json.loads(self.actions)
        for action in actions:
            button = GridButton(text=str(action.replace(actions[action] + "\\", "").replace(
                ".ino", "")), path=actions[action], filename=action, chose=self.chose)
            grid.add_widget(button)
        self.scrollView.add_widget(grid)
        self.ids.box.add_widget(self.scrollView, index=1)


class GridButton(Button):
    path = StringProperty("")
    filename = StringProperty("")
    chose = ObjectProperty(None)


class CustomGrid(GridLayout):
    pass


class MenuDropDown(ActionDropDown):
    pass


class SettingButtons(SettingItem):
    def __init__(self, **kwargs):
        self.register_event_type('on_release')
        self.panel = kwargs["panel"]
        super(SettingItem, self).__init__(
            title=kwargs["title"], desc=kwargs["desc"], section=kwargs["section"], key=kwargs["key"])  # **kwargs
        for aButton in kwargs["buttons"]:
            oButton = Button(text=aButton['title'], font_size='15sp')
            oButton.ID = aButton['id']
            self.add_widget(oButton)
            oButton.bind(on_release=self.On_ButtonPressed)

    def On_ButtonPressed(self, instance):
        self.panel.settings.dispatch(
            'on_config_change', self.panel.config, self.section, self.key, instance.ID)


class SettingShortcut(SettingItem):
    popup = ObjectProperty(None, allownone=True)
    textinput = ObjectProperty(None)
    value = StringProperty("Not defined")

    def __init__(self, **kwargs):
        super(SettingShortcut, self).__init__(**kwargs)
        self.curentShortcut = Label(text=self.value)
        self.curValue = self.value
        self.add_widget(self.curentShortcut)

    def on_panel(self, instance, value):
        if value is None:
            return
        self.bind(on_release=self._create_popup)

    def _dismiss(self, *largs):
        self.running = False
        if self.textinput:
            self.textinput.focus = False
        if self.popup:
            self.popup.dismiss()
        self.popup = None

    def _validate(self, instance):
        self._dismiss()
        self.running = False
        self.value = self.curValue
        self.curentShortcut.text = self.value

    def _inputget(self, *args):
        while self.running and threading.main_thread().is_alive():
            hotkey = keyboard.read_hotkey(False)
            self.curValue = hotkey
            self.shortcutPicker.text = _(
                "Press any key combination") + "\n" + hotkey
            time.sleep(0.5)

    def _create_popup(self, instance):
        # create popup layout
        content = BoxLayout(orientation='vertical', spacing='5dp')
        self.popup = popup = Popup(
            title=self.title, content=content, size_hint=(0.7, 0.6))

        self.shortcutPicker = shortcutPicker = Label(text=_(
            "Press any key combination") + "\n" + self.value, valign='middle', halign='center')
        content.add_widget(shortcutPicker)

        # 2 buttons are created for accept or cancel the current value
        btnlayout = BoxLayout(size_hint_y=None, height='50dp', spacing='5dp')
        btn = Button(text='Ok')
        btn.bind(on_release=self._validate)
        btnlayout.add_widget(btn)
        btn = Button(text='Cancel')
        btn.bind(on_release=self._dismiss)
        btnlayout.add_widget(btn)
        content.add_widget(btnlayout)

        # all done, open the popup !
        popup.open()

        # start to listen for hotkey press
        self.running = True
        threading.Thread(target=self._inputget).start()


class SettingColorPicker(SettingItem):
    popup = ObjectProperty(None, allownone=True)
    textinput = ObjectProperty(None)
    value = StringProperty("#FFFFFF")

    def __init__(self, **kwargs):
        super(SettingColorPicker, self).__init__(**kwargs)
        self.curentColour = Label(
            text=self.value, color=utils.get_color_from_hex(self.value))
        self.add_widget(self.curentColour)

    def on_panel(self, instance, value):
        if value is None:
            return
        self.bind(on_release=self._create_popup)

    def _dismiss(self, *largs):
        if self.textinput:
            self.textinput.focus = False
        if self.popup:
            self.popup.dismiss()
        self.popup = None

    def _validate(self, instance):
        self._dismiss()
        value = utils.get_hex_from_color(self.colorpicker.color)
        self.curentColour.color = self.colorpicker.color
        self.curentColour.text = value
        self.value = value

    def _create_popup(self, instance):
        # create popup layout
        content = BoxLayout(orientation='vertical', spacing='5dp')
        popup_width = 0.95 * Window.width
        self.popup = popup = Popup(
            title=self.title, content=content, size_hint=(None, 0.9), width=popup_width)

        self.colorpicker = colorpicker = ColorPicker(
            color=utils.get_color_from_hex(self.value))
        colorpicker.bind(on_color=self._validate)

        self.colorpicker = colorpicker
        content.add_widget(colorpicker)

        # 2 buttons are created for accept or cancel the current value
        btnlayout = BoxLayout(size_hint_y=None, height='50dp', spacing='5dp')
        btn = Button(text='Ok')
        btn.bind(on_release=self._validate)
        btnlayout.add_widget(btn)
        btn = Button(text='Cancel')
        btn.bind(on_release=self._dismiss)
        btnlayout.add_widget(btn)
        content.add_widget(btnlayout)

        popup.open()

class Input(BoxLayout):
    """Custom input to handle parameters.

    inputName string: the name.
    input_filter string: filter for numeric values (int, float, ...).
    default_text string: text to be displayed at startup.
    callback funct: function to call when it changes.
    inputType int: Text, switch or button (0, 1 or 2).

    returns: the BoxLayout object.
    """

    inputName = StringProperty('default')
    input_filter = StringProperty(None)
    boundaries = ObjectProperty([float('-inf'), float('inf')])
    default_text = StringProperty('default')
    callback = ObjectProperty(None, rebind=True)
    inputType = NumericProperty(0)

    def __init__(self, **kwargs):
        super(Input, self).__init__(**kwargs)
        if self.callback is not None and self.callback != '':
            self.after_init()
        else:
            # Have to wait if declared in .kv because the properties are not set before init
            Clock.schedule_once(self.after_init)

    def after_init(self, *args):
        self.label = Label(text=self.inputName)
        self.add_widget(self.label)

        if self.callback is not None and self.callback != '':
            self.toCall = lambda *args: self.callback()
        else:
            self.toCall = lambda: print("no callback")

        if self.inputType == 0:
            self.input = TextInput(
                text=self.default_text, multiline=False, input_filter=self.input_filter)
        elif self.inputType == 1:
            self.input = Switch(active=self.default_text == "True")
        elif self.inputType == 2:
            self.input = Button(text=self.default_text)
        self.bindThis()
        self.add_widget(self.input)

    def bindThis(self, *args):
        if self.inputType == 0:
            self.input.bind(text=self.toCall)
        elif self.inputType == 1:
            self.input.bind(active=self.toCall)
        elif self.inputType == 2:
            self.input.bind(on_press=self.toCall)

    def unbindThis(self, *args):
        if self.inputType == 0:
            self.input.unbind(text=self.toCall)
        elif self.inputType == 1:
            self.input.unbind(active=self.toCall)
        elif self.inputType == 2:
            self.input.unbind(on_press=self.toCall)

    def write(self, value, *args):
        self.unbindThis()
        if self.inputType == 0:
            self.input.text = str(value)
        elif self.inputType == 1:
            self.input.active = bool(value)
        self.bindThis()

    def read(self, *args):
        if self.inputType == 0:
            return self.sanitize(self.input.text)
        elif self.inputType == 1:
            return self.input.active

    def sanitize(self, number):
        """Avoids getting errors on empty inputs.

        number string||float||int: the value to sanitize.

        returns: 0 if it is NaN, otherwise the value itself.
        """
        try:
            number = int(number)
        except:
            try:
                number = float(number)
            except:
                number = 0
        return max(min(number, self.boundaries[1]), self.boundaries[0])

    def hide(self, *args):
        self.height = '0'
        self.remove_widget(self.label)
        self.remove_widget(self.input)

    def show(self, *args):
        self.height = '30'
        if self.label.parent is None and self.input.parent is None:
            self.add_widget(self.label)
            self.add_widget(self.input)
