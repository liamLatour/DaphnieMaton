import serial

ser = serial.Serial("COM5", timeout=1)
ser.write(b'0 8')