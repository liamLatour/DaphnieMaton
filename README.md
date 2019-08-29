![logo](https://github.com/liamLatour/DaphnieMaton/blob/master/Images/daphnie.png)
# DaphnieMaton

The DaphnieMaton is a two-axis system to film continously and in a pre-created custom path.
Originally made to watch for the evolution of a Daphnie population in different tubes (testing for temperature), it can be used for all sorts of autonomous systemes and can also be mounted with something else than a camera.

## Getting Started

- [Download](https://github.com/liamLatour/DaphnieMaton/releases/latest) the installer
- [Download](https://www.arduino.cc/en/Main/Software) the latest version of the arduino software
- Install the DaphnieMaton software
- Read the help messages to get started
- Click 'upload' and voilà !

### Prerequisites

To build from source you'll need:
  - [Kivy](https://kivy.org/#download)
  - PySerial ```pip install pyserial```
  - keyboard ```pip install keyboard```
  - [NumPy and SciPy](https://scipy.org/install.html)
  - Pyperclip ```pip install pyperclip```
  - Gettext ```pip install python-gettext```
  - [PyInstaller](https://www.pyinstaller.org/) - To build an executable

### Building on top

In order to make the 'head' do something you need to create a separate arduino programm (.ino) without 'setup' and 'loop' function. You also have to create a fucntion named 'action' that the 'head' will run each time it is asked to.
Minimalistic example:
```C++
void action(){
  pinMode(13, OUTPUT);    // You are obliged to call this every time since there is no setup()
  digitalWrite(13, HIGH); // In case you want to remember what state the LED is in, you can use EEPROM
}
```

## Built With

* [Kivy](https://kivy.org) - The gui framework used
* [PyInstaller](https://www.pyinstaller.org/) - Software used to create the executable

## Contributing

Just submit a pull request specifying which part is affected and if it is an enhancement or a bug fix

## Authors

* **Louis Quaire--Merlin** - *student at Blaise-Pascal*
* **Liam Latour** - *student at Blaise-Pascal*

## Acknowledgments
* [Kniteditor](https://blog.fossasia.org/tag/language-localization/) by Fossasia for the translation template
* [Alexander Wolf](https://gist.github.com/AWolf81) for the [ColorPicker](https://gist.github.com/AWolf81/421976e65099d3e58a32) type in the Settings
* Thica for the [Button](https://github.com/kivy/kivy/wiki/Buttons-in-Settings-panel) type in the Settings
