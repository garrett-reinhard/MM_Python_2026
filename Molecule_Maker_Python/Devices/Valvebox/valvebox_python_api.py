import ctypes
import inspect
import clr
import subprocess
from subprocess import *
import os
import sys



clr.AddReference('.\Devices\Valvebox\ValveModule_DLL')
from ValveModule_DLL import ValveMod
class valves:
    def __init__(self):
        self.valve_object = ValveMod()
        self.valves_loaded = False
        valves_loaded = self.valve_object.Initialize(1,24)
        if valves_loaded == False:
            sys.exit("ERROR V1: Valves failed to load. \n try plugging in valves first+running to init")
                     
    def set_valve(self, valve, port):
         self.valve_object.Port(valve, port)
