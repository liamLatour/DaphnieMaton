import json
import os
import threading
import time
from os import system as osSystem

import keyboard
import serial
from kivy.clock import Clock
from kivy.uix.image import AsyncImage

from .localization import _


class Arduino:
    def __init__(self, settings, easyPopup, refresh, programs={}):
        self.hasDirectProgram = False
        self.boardBusy = False
        self.board = -1
        self.port = -1
        self.systemPosition = (0, 0)
        self.systemSwitchs = {
            'A': {'value': False, 'position': [1, -1]},
            'B': {'value': False, 'position': [1, 1]},
            'C': {'value': False, 'position': [-1, 1]},
            'D': {'value': False, 'position': [-1, -1]},
            'MA': {'value': False, 'position': [1, 0]},
            'MD': {'value': False, 'position': [-1, 0]},
        }
        self.readingClock = -1
        self.checkKeyClock = -1

        self.easyPopup = easyPopup
        self.settings = settings
        self.programs = programs
        self.refresh = refresh

    def sendSerial(self, direction, shortcut=False, urgent=False, *args):
        if self.boardBusy or self.port == -1:
            return False

        self.boardBusy = urgent

        try:
            self.board.write(direction)
        except:
            try:
                self.board = serial.Serial(str(self.port), 9600, timeout=1)
                time.sleep(2)
                self.board.write(direction)
            except:
                print("sendSerial")
                return False

        if shortcut:
            self.stopCheckKey()
            self.checkKeyClock = Clock.schedule_interval(
                self.checkKeyHolding, 0.2)

    def readFromSerial(self, *args):
        self.sendSerial(bytes([7]))
        try:
            received = json.loads(
                self.board.readline().decode("utf-8").rstrip())

            self.systemPosition = (received['X'], received['Y'])
            self.systemSwitchs['A']['value'] = received['A']
            self.systemSwitchs['B']['value'] = received['B']
            self.systemSwitchs['C']['value'] = received['C']
            self.systemSwitchs['D']['value'] = received['D']
            self.systemSwitchs['MA']['value'] = received['MA']
            self.systemSwitchs['MD']['value'] = received['MD']
            self.refresh()
        except:
            self.stopReading()
            print("readFromSerial")
            self.easyPopup(_('Disconnected'), _(
                'The system has been disconnected'))

    def stopReading(self):
        if self.readingClock != -1:
            self.readingClock.cancel()
            self.readingClock = -1

    def checkItHasDirectProgram(self):
        if self.sendSerial(bytes([9]), urgent=True) != False:
            self.hasDirectProgram = False
            try:
                response = self.board.readline().decode("utf-8").rstrip()
                print(response)
                if response == "DaphnieMaton":
                    self.hasDirectProgram = True
                    self.stopReading()
                    self.readingClock = Clock.schedule_interval(
                        self.readFromSerial, 0.2)
            except:
                print("checkItHasDirectProgram")
                self.easyPopup(_('Disconnected'), _(
                    'The system has been disconnected'))

            self.boardBusy = False

    def calibrate(self, program):
        if self.port == -1:
            self.easyPopup(_('No port detected'), _(
                'No serial port was specified'))
            return

        self.stopReading()
        if not self.hasDirectProgram:
            self.uploadProgram(program)

        self.sendSerial(bytes([10]))
        self.calibrateClock = Clock.schedule_interval(
            self.getCalibrationAsync, 0.5)

    def getCalibrationAsync(self, *args):
        if self.port == -1:
            self.calibrateClock.cancel()
            print("getCalibrationAsync top")
            self.easyPopup(_('Disconnected'), _(
                'The system has been disconnected'))
            return

        if self.board == -1:
            self.board = serial.Serial(str(self.port), 9600, timeout=1)
        elif self.board.in_waiting > 0:
            try:
                received = json.loads(
                    self.board.readline().decode("utf-8").rstrip())
                print(received)
                steps = received['Steps']
                speed = float(self.settings.get('general', 'yDist')) / \
                    (float(received['Time'])/100)  # in m.s^-1

                self.settings.set("general", "stepToCm", str(round(
                    (float(steps)/(float(self.settings.get('general', 'yDist'))-5.5))*10) / 10))
                self.settings.set("general", "speed",
                                  str(round(speed*10) / 10))
                self.settings.write()

                self.easyPopup(_('Calibration successful'), _(
                    'The DaphnieMaton has found it\'s ratio: ') + str(self.settings.get('general', 'stepToCm')) + " step/cm")

                self.calibrateClock.cancel()
                print("calibrated to " +
                      str(self.settings.get('general', 'stepToCm')))
                print("Speed is: " + str(speed) + "m.s^-1")
            except Exception as e:
                print(e)
                print("getCalibrationAsync")
                self.easyPopup(_('Disconnected'), _(
                    'The system has been disconnected'))

    def uploadProgram(self, program):
        if self.port == -1:
            self.easyPopup(_('No port detected'), _(
                'No serial port was specified'))
            return

        self.easyPopup(_('Upload'), AsyncImage(
            source='.\\assets\\logo.png', size=(100, 100)), auto_dismiss=False)
        self.stopReading()
        threading.Thread(target=lambda: self.uploadAsync(program)).start()

    def uploadAsync(self, program):
        self.boardBusy = True
        try:
            if self.board != -1:
                self.board.close()
                self.board = -1

            result = osSystem("\""+os.path.join(os.path.normpath(os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir) + "\\arduino\\arduino_debug")+"\" --verbose --board arduino:avr:mega:cpu=atmega2560 --port " +
                     str(self.port)+" --upload "+self.programs[program]["path"])

            if result == 0:
                self.hasDirectProgram = self.programs[program]["isDirectProgram"]
                print("\r\nDONE !")
                self.easyPopup(_('Success !'), _('Upload finished successfully !'))
            else:
                self.easyPopup(_('Oopsie...'), _(
                'Something went wrong, try again or report a bug') + "\nError code " + str(result))
        except Exception as e:
            self.easyPopup(_('Oopsie...'), _(
                'Something went wrong, try again or report a bug') + "\n" + str(e))
        self.boardBusy = False
        self.refresh()

    def checkKeyHolding(self, *args):
        stopX = False
        stopY = False

        if not (keyboard.is_pressed(self.settings.get('shortcuts', 'moveLeft')) or keyboard.is_pressed(self.settings.get('shortcuts', 'moveRight'))):
            stopX = True
            self.sendSerial(bytes([5]))
        if not (keyboard.is_pressed(self.settings.get('shortcuts', 'moveUp')) or keyboard.is_pressed(self.settings.get('shortcuts', 'moveDown'))):
            stopY = True
            self.sendSerial(bytes([6]))

        if stopX and stopY:
            self.stopCheckKey()

    def stopCheckKey(self):
        if self.checkKeyClock != -1:
            self.checkKeyClock.cancel()
            self.checkKeyClock = -1
