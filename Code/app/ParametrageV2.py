from io import open as openFile

import keyboard
from kivy.app import App
from kivy.config import Config
from kivy.lang import Builder
from kivy.uix.settings import SettingsWithSidebar

from assets.libraries.classes import SettingButtons, SettingColorPicker
from assets.libraries.daphnieMaton import Parametrage
from assets.libraries.localization import (change_language_to,
                                           translation_to_language_code)

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.set('kivy','window_icon','assets/logoDark.ico')

#https://stackoverflow.com/questions/34468909/how-to-make-tooltip-using-kivy

Builder.load_file('.\\main.kv')

class DaphnieMatonApp(App):
    def build(self):
        self.settings_cls = SettingsWithSidebar
        self.icon = 'assets/logoDark.png'
        self.update_language_from_config()
        self.app = Parametrage()

        self.shortcuts = {
            'save': [lambda: self.app.save(-1, -1)],
            'copy': [self.app.copyToClipboard],
            'undo': [self.app.undo]
        }

        self.configFiles = {
            ".\\assets\\settings\\config.json": 'General',
            ".\\assets\\settings\\shortcuts.json": 'Shortcuts',
            ".\\assets\\settings\\colors.json": 'Aspect'
        }

        for short in self.shortcuts:
             self.shortcuts[short].append(keyboard.add_hotkey(self.config.get('shortcuts', short), self.shortcuts[short][0]))

        return self.app

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
        config.setdefaults('colors', {
            'background': '#373737ff',
            'pipeColor': '#72f7ff',
            'imagePath': ".\\assets\\topDownView.png",
            'nodeColor': "#e0e028",
            'nodeHighlight': "#d32828",
            'pathColor': "#72f7ff",
            'pathHighlight': "#82d883"})

    def build_settings(self, settings):
        settings.register_type('buttons', SettingButtons)
        settings.register_type('color', SettingColorPicker)

        for files in self.configFiles:
            f = openFile(files, "r", encoding='utf8')
            if f.mode == 'r':
                contents = f.read()
                settings.add_json_panel(self.configFiles[files], self.config, data=contents)
    
    def on_config_change(self, config, section, key, value):
        if section == "general" and key == "language":
            change_language_to(translation_to_language_code(value))
            print("Language changed")
        if section == "general" and key == "calibrate":
            self.app.update(callibration=True, callback=self.app.callibrate)
            print("Calibrate")

        if section == "shortcuts":
            for short in self.shortcuts:
                if short == key:
                    keyboard.remove_hotkey(self.shortcuts[short][1])
                    self.shortcuts[short][1] = keyboard.add_hotkey(value, self.shortcuts[short][0])
                    return

        if section == "colors":
            self.app.updateColors()

    def update_language_from_config(self):
        config_language = self.config.get('general', 'language')
        change_language_to(translation_to_language_code(config_language))

if __name__ == '__main__':
    DaphnieMatonApp().run()
