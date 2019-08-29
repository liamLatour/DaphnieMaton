import configparser
import ctypes
import os
import traceback
from io import open as openFile

import keyboard
from kivy.app import App
from kivy.config import Config
from kivy.lang import Builder
from kivy.uix.settings import SettingsWithSidebar

import libraries.classes as SpecialSettings
import libraries.daphnieMaton as daphnieMaton
from libraries.localization import (change_language_to,
                                    translation_to_language_code)

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.set('kivy', 'window_icon', 'assets/logoDark.ico')

# https://stackoverflow.com/questions/34468909/how-to-make-tooltip-using-kivy

Builder.load_file('.\\main.kv')


class DaphnieMatonApp(App):
    def build(self):
        self.settings_cls = SettingsWithSidebar
        self.icon = 'assets/logoDark.png'
        self.update_language_from_config()
        self.app = daphnieMaton.Parametrage()

        self.shortcuts = {
            'save': [lambda: self.app.save(-1, -1)],
            'saveas': [self.app.show_save],
            'open': [self.app.show_load],
            'new': [lambda: self.app.newFile(True)],

            'undo': [lambda: self.app.undo(-1)],
            'redo': [lambda: self.app.undo(1)],
            'clear': [self.app.removeAllNodes],
            'suppr': [self.app.removeNode],

            'copy': [self.app.copyToClipboard],
            'moveRight': [lambda: self.app.arduino.sendSerial(bytes([1]), shortcut=True)],
            'moveLeft': [lambda: self.app.arduino.sendSerial(bytes([2]), shortcut=True)],
            'moveUp': [lambda: self.app.arduino.sendSerial(bytes([3]), shortcut=True)],
            'moveDown': [lambda: self.app.arduino.sendSerial(bytes([4]), shortcut=True)]
        }
        
        self.configFiles = {
            "settings\\config.json": 'General',
            "settings\\shortcuts.json": 'Shortcuts',
            "settings\\colors.json": 'Aspect',
            "settings\\hidden.json": 'Hidden',
        }

        for short in self.shortcuts:
            if len(self.shortcuts[short]) == 2:
                self.shortcuts[short].append(keyboard.add_hotkey(self.config.get(
                    'shortcuts', short), self.shortcuts[short][0], suppress=False, trigger_on_release=False))
                self.shortcuts[short].append(keyboard.add_hotkey(self.config.get(
                    'shortcuts', short), self.shortcuts[short][1], suppress=False, trigger_on_release=True))
            else:
                self.shortcuts[short].append(keyboard.add_hotkey(self.config.get(
                    'shortcuts', short), self.shortcuts[short][0], suppress=False))

        return self.app

    def build_config(self, config):
        config.setdefaults('general', {
            'arduinoPath': 'C:\\',
            'savePath': 'C:\\',
            'stepToCm': 100,
            'yDist': 100,
            'speed': 7,
            'autoSave': 5,
            'language': "English",
            'hidden': False})
        config.setdefaults('shortcuts', {
            'save': 'ctrl+s',
            'saveas': 'ctrl+shift+s',
            'open': 'ctrl+o',
            'new': 'ctrl+n',

            'undo': 'ctrl+z',
            'redo': 'ctrl+y',
            'clear': 'ctrl+x',
            'suppr': 'suppr',
            'corner': 'shift',
            'angle': 'ctrl',

            'copy': 'ctrl+c',
            'moveLeft': 'left',
            'moveRight': 'right',
            'moveUp': 'up',
            'moveDown': 'down'})
        config.setdefaults('colors', {
            'background': '#373737ff',
            'pipeColor': '#72f7ff',
            'imagePath': ".\\assets\\topDownView.png",
            'lineWidth': 5,
            'nodeDiam': 20,
            'nodeColor': "#e0e028",
            'nodeHighlight': "#d32828",
            'actionNode': "#59ff00",
            'pathColor': "#72f7ff",
            'pathHighlight': "#82d883",
            'switchDiam': 30})
        config.setdefaults('hidden', {
            'action': '{}',
            'version': '1.1',
            'starting': 'Pipe',
            'imWidth': 1.38,
            'imHeight': 1.4,
            'acWidth': 1.144,
            'acHeight': 1.1,
            'origin': '(17, 17.2)'})

    def build_settings(self, settings):
        settings.register_type('buttons', SpecialSettings.SettingButtons)
        settings.register_type('color', SpecialSettings.SettingColorPicker)
        settings.register_type('shortcut', SpecialSettings.SettingShortcut)

        show = False
        
        if os.path.exists(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'daphniematon.ini')):
            config = configparser.ConfigParser()
            config.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'daphniematon.ini'))
            try:
                show = bool(int(config['general']['hidden']))
            except:
                show = config['general']['hidden'] == True

        for files in self.configFiles:
            if self.configFiles[files] == "Hidden" and not show:
                continue
            f = openFile(os.path.join(os.path.dirname(os.path.realpath(__file__)), files), "r", encoding='utf8')
            if f.mode == 'r':
                contents = f.read()
                settings.add_json_panel(
                    self.configFiles[files], self.config, data=contents)

    def on_config_change(self, config, section, key, value):
        if section == "general" and key == "language":
            change_language_to(translation_to_language_code(value))
            print("Language changed")
        if section == "general" and key == "calibrate":
            self.app.arduino.calibrate(program="Direct")
            print("Calibrate")

        if section == "shortcuts":
            for short in self.shortcuts:
                if short == key:
                    if len(self.shortcuts[short]) == 4:
                        keyboard.remove_hotkey(self.shortcuts[short][2])
                        self.shortcuts[short][2] = keyboard.add_hotkey(
                            value, self.shortcuts[short][0], suppress=False, trigger_on_release=False)
                        self.shortcuts[short][3] = keyboard.add_hotkey(
                            value, self.shortcuts[short][1], suppress=False, trigger_on_release=True)
                    else:
                        keyboard.remove_hotkey(self.shortcuts[short][1])
                        self.shortcuts[short][1] = keyboard.add_hotkey(
                            value, self.shortcuts[short][0], suppress=False)
                    return

        if section == "colors":
            self.app.updateColors()

    def update_language_from_config(self):
        config_language = self.config.get('general', 'language')
        change_language_to(translation_to_language_code(config_language))


if __name__ == '__main__':
    try:
        DaphnieMatonApp().run()
    except Exception as e:
        traceback.print_tb(e.__traceback__)
        ctypes.windll.user32.MessageBoxW(
            0, u"An error occured: \n" + str(e), u"DaphnieMaton Error", 0)
