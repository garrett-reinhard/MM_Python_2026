import ctypes
import clr
import subprocess
from subprocess import *
import os
import sys
#clr.AddReference('.\Devices\SyringePump\KEMPumpDLL')

#Temporary load point for hardware testing
clr.AddReference('.\SyringePump\KEMPumpDLL')
#clr.AddReference('KEMPumpDLL')
from KEMPumpDLL import SyringePumpDef

#test = ValveMod()
#test.Initialize(1,1)
#Contains Constructor for Default valves (starting address 1, 24 ports)
#Is used over importing DLL to all other files for clealiness and Customizable exceptions
class syring_pump:
    def __init__(self):

        self.pump = SyringePumpDef()
        self.pump_loaded = self.pump.OpenCommunications()
        self.valid_pumps =[]
        
        if(self.pump_loaded):
            for module in range(1,7):
                if self.pump.DiscoverModule(module):
                    self.valid_pumps.append(module)
                    
            self.pump.Initialize(0)
            
        else:
            sys.exit("ERROR SP1: Syringe Pumps failed to load")

    def set_port(self, module, port):
        """Set the port of the syringepump
        inputs: module, port"""
        self.pump.Port(module, port)

    def dispense(self, module, volume):
        """Dispense specified amount in ml from module
        Inputs: module, volume(ml)"""
        self.pump.Dispense(int(module), int(volume))

    def withdraw(self, module, volume):
        """Withdraw specified amount in ml from module
        Inputs: module, volume(ml)"""
        self.pump.Withdraw(int(module), int(volume))

