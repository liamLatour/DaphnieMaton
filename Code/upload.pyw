# To find the serial port
import serial.tools.list_ports
import re

ports = list(serial.tools.list_ports.comports())

for p in ports:
    match = re.search('COM(\d+)', str(p))
    if match:
        print(int(match.group(1)))
    print(p)

# To flash a .hex
import os
port = 14
os.system('arduino-1.8.8\\hardware\\tools\\avr\\bin\\avrdude -Carduino-1.8.8\\hardware\\tools\\avr/etc/avrdude.conf -v -patmega2560 -cwiring -PCOM'+str(port)+' -b115200 -D -Uflash:w:testFlash\\testFlash.ino.hex:i')

