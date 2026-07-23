import ctypes
import inspect
import clr
import subprocess
from subprocess import *
import os
import sys
import serial
clr.AddReference('.\ValveModule_DLL')

class Valve:
    """IKA RET Control Visc Class API
    When creating Must Include a COM port as a string: 'COM2' 
    This is probably super unstable right now
    For Safety Reasons Stir speed and temp set point init to 0
    Variable list:
    1: Temp Setpoint?
    2: Temp Setpoint?
    
    """
    #COM9
    def __init__ (self, port):
        self.ser = serial.Serial(
            port=port,
            parity=serial.PARITY_NONE,
            baudrate=38400,
            timeout=10,
            write_timeout=10,
            xonxoff=False
        )


    def _send_command(self, output):
        """Sends a command to the Hotplate
        String Does NOT need to be in Byte format"""
        byte_command = bytes(f"{output}\n", encoding="utf-8")
        self.ser.write(byte_command)
    def _read_response(self):
        """Read Value returned by hotplate after sending a command"""
        try:
            #Hotplate returns the value AND the variable, this only returns the value
            print(self.ser.readline().decode("utf-8").strip().split()[0])
        except:
            print("ERROR H2: Something went wrong reading a variable on a hotplate")


    #Stir Functions
    def SetStirSpeed(self, speed):
        """Set Setpoint Stir Speed of hotplate in RPM
        Acceptable ranges: 0; 50-1700"""
        
        if ((speed in range(50, 1700)) or (speed ==0)):
            self.__set_stir_speed = speed
            self._send_command(f"OUT_SP_4 {speed}")
        else:
            print("ERROR H1_S1: Speed Setpoint out of range")

    def GetCurrentStirSpeedSetpoint(self):
        """Returns Current Stir Speed Setpoint"""
        return(self.__set_stir_speed)
    
valve = Valve("COM9")
valve._send_command()