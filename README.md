![logo](https://github.com/liamLatour/DaphnieMaton/blob/master/Images/logoV2.svg)
# DaphnieMaton

The DaphnieMaton is a two-axis system to film continously and in a pre-created custom path.
Originally made to watch for the evolution of a Daphnie population in different tubes (testing for temperature), it can be used for all sorts of autonomous systemes and can also be mounted with something else than a camera.

## Getting Started

- Clone the repo and open "DaphnieMaton.exe"
- Connect the arduino Mega to an usb port and select it under "Port" section in the menu
- Change the designed path to suit your needs
- Click 'update' and voilà !

### Prerequisites

To build from source you'll need:
  - [Kivy](https://kivy.org/#download)
  - pyserial ```pip install pyserial```

### Building on top

Not implemented yet

## To be added
- Settings:
  - arduino.exe path
  - shortcuts
  - colors
  - default save path
- Ctrl+S so save without reselecting path
- When opened change 'Save' to 'Save as' (remove .json when saving file to avoid .json.json)
- Make 'Help' relevant to the current pannel
- Language
- Delta to the origin for "tube" mode

## Built With

* [Kivy](https://kivy.org) - The gui framework used

## Contributing

Just submit a pull request specifying which part is affected and if it is an enhancement or a bug fix

## Authors

* **Louis Quaire--Merlin** - *student at Blaise-Pascal*
* **Liam Latour** - *student at Blaise-Pascal*
