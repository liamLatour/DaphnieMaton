from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from os import listdir

kv_path = './kv/'
for kv in listdir(kv_path):
    if '.kv' in kv:
        Builder.load_file(kv_path+kv)


class Parametrage(BoxLayout):
    pass

class TutorialApp(App):  
#the kv file name will be Tutorial (name is before the "App")
    def build(self):
        return Parametrage()

TutorialApp().run()