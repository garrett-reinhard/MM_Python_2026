import ctypes
import clr
import subprocess
from subprocess import *
import os
import sys

clr.AddReference('.\ValveModule_DLL')
from ValveModule_DLL import ValveMod

test = ValveMod()
test.InitializePort = 1
valves_loaded = test.Initialize(1,0)
"""
print(inspect.getsource(test.__init__))
methods = inspect.getmembers(test)
for name, method in methods:
    try:
        print(f"{name}: {inspect.signature(method)}")
    except:
        print("tail")
        """
#Contains Constructor for Default valves (starting address 1, 24 ports)
#Is used over importing DLL to all other files for clealiness and Customizable exceptions
print(test.get_InitializationPort(5))
class valves:
    def __init__(self):
        self.valve_object = ValveMod()
        self.valves_loaded = False
        
        valves_loaded = self.valve_object.Initialize(5,2)
        if valves_loaded == False:
            sys.exit("ERROR V1: Valves failed to load. \n try plugging in valves first+running to init")
                     
    def set_valve(self, valve, port):
         self.valve_object.Port(valve, port)
