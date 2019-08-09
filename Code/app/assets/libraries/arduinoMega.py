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
    def __init__(self, settings, easyPopup, programs={}):
        self.hasDirectProgram = False
        self.boardBusy = False
        self.board = -1
        self.port = -1
        self.systemPosition = (0, 0)
        self.systemSwitchs = {
            'A': False,
            'B': False,
            'C': False,
            'D': False,
            'MA': False,
            'MD': False,
        }
        self.readingClock = -1
        self.checkKeyClock = -1

        self.easyPopup = easyPopup
        self.settings = settings
        self.programs = programs

    def readFromSerial(self, *args):
        if self.port != -1:
            self.sendSerial(bytes([7]))
            try:
                received = json.loads(self.board.readline().decode("utf-8").rstrip())

                self.systemPosition = (received['X'], received['Y'])
                self.systemSwitchs['A'] = received['A']
                self.systemSwitchs['B'] = received['B']
                self.systemSwitchs['C'] = received['C']
                self.systemSwitchs['D'] = received['D']
                self.systemSwitchs['MA'] = received['MA']
                self.systemSwitchs['MD'] = received['MD']
            except:
                if self.readingClock != -1:
                    self.readingClock.cancel()
                    self.readingClock = -1

                self.easyPopup(_('Disconnected'), _('The system has been disconnected'))

    def checkItHasDirectProgram(self):
        self.sendSerial(bytes([9]), urgent=True)
        if self.board != -1:
            try:
                response = self.board.readline()
                print(response)
            except:
                self.easyPopup(_('Disconnected'), _('The system has been disconnected'))

            self.boardBusy = False
            response = response.decode("utf-8").rstrip()
            if response == "DaphnieMaton":
                self.hasDirectProgram = True
                self.readingClock = Clock.schedule_interval(self.readFromSerial, 0.2)
                return True
            else:
                return False
        self.boardBusy = False

    def getCalibrationAsync(self, *args):
        if self.port != -1 and self.board != -1:
            if self.board.in_waiting > 0:
                try:
                    received = json.loads(self.board.readline().decode("utf-8").rstrip())
                    print(received)
                    steps = received['Steps']
                    speed = float(self.settings.get('general', 'yDist'))/(float(received['Time'])/100) # in m.s^-1

                    self.settings.set("general", "stepToCm", str(round((float(steps)/(float(self.settings.get('general', 'yDist'))-5.5))*10) / 10))
                    self.settings.set("general", "speed", str(round(speed*10) / 10))
                    self.settings.write()

                    self.easyPopup(_('Calibration successful'), _('The DaphnieMaton has found it\'s ratio: ') + str(self.settings.get('general', 'stepToCm')) + " step/cm")

                    print("calibrated to " + str(self.settings.get('general', 'stepToCm')))
                    print("Speed is: " + str(speed) + "m.s^-1")
                except Exception as e:
                    print(e)
                    self.easyPopup(_('Disconnected'), _('The system has been disconnected'))
                self.calibrateClock.cancel()
                self.calibrateClock = -1
        elif self.board == -1:
            print("new board")
            self.board = serial.Serial(str(self.port), 9600, timeout=1)
        
    def calibrate(self, program):
        self.uploadProgram(program)
        
        if self.port != -1:
            self.boardBusy = False # to be sure to launch the command
            self.sendSerial(bytes([10]))
            self.calibrateClock = Clock.schedule_interval(self.getCalibrationAsync, 0.5)

    def uploadProgram(self, program):
        if not os.path.isfile(self.settings.get('general', 'arduinoPath') + '/arduino_debug.exe'):
            self.easyPopup(_('Arduino dir missing'), _('The specified arduino path is not correct \n (under Option -> Arduino.exe path)'))
            return

        self.easyPopup(_('Upload'), AsyncImage(source='.\\assets\\logo.png', size=(100, 100)), auto_dismiss=False)
        """
        if self.readingClock != -1:
            self.readingClock.cancel()
            self.readingClock = -1
        """
        threading.Thread(target=lambda: self.uploadAsync(program)).start()

    def uploadAsync(self, program):
        self.boardBusy = True

        try:
            if self.port != -1:
                try:
                    self.board.close()
                    self.board = -1
                except: pass

                self.hasDirectProgram = self.programs[program]["isDirectProgram"]

                osSystem(self.settings.get('general', 'arduinoPath') + "\\arduino_debug --board arduino:avr:mega:cpu=atmega2560 --port "+str(self.port)+" --upload "+self.programs[program]["path"])            
                
                print("DONE !")
                self.easyPopup(_('Success !'), _('Upload finished successfully !'))
            else:
                self.easyPopup(_('No port detected'), _('No serial port was specified'))
        except Exception as e:
            self.easyPopup(_('Oopsie...'), _('Something went wrong, try again or report a bug') + "\n" + str(e))
        self.boardBusy = False

    def sendSerial(self, direction, shortcut=False, urgent=False, *args):
        if self.boardBusy:
            print("Cannot")
            print(direction)
            return
        if urgent:
            self.boardBusy = True
        if self.port != -1:
            try:
                self.board.write(direction)
            except:
                try:
                    self.board = serial.Serial(str(self.port), 9600, timeout=1)
                    time.sleep(2)
                    self.board.write(direction)
                except:
                    if not self.boardBusy:
                        self.easyPopup(_('Disconnected'), _('The system has been disconnected'))

            if shortcut == True:
                if self.checkKeyClock != -1:
                    self.checkKeyClock.cancel()
                    self.checkKeyClock = -1
                self.checkKeyClock = Clock.schedule_interval(self.checkKeyHolding, 0.2)

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
            if self.checkKeyClock != -1:
                self.checkKeyClock.cancel()
                self.checkKeyClock = -1
