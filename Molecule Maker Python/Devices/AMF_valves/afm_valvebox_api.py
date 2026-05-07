import ctypes
import clr
import subprocess
from subprocess import *
import os
import sys
import amfTools
from amfTools import AMF, Device
#test = ValveMod()
#test.Initialize(1,1)
#Contains Constructor for Default valves (starting address 1, 24 ports)
#Is used over importing DLL to all other files for clealiness and Customizable exceptions
class amf_valves:
    def __init__(self):
        self.valve_list = list(AMF)
        for valve in amfTools.util.getProductList():
            self.valve_list.append(AMF(product=valve))
        
    def set_valve(self, valve, port):
        self.valve_list[valve-1].valveMoveTo(port)