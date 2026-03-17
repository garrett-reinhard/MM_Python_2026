import ctypes
import clr
import subprocess
from subprocess import *
import os
import sys

#test = ValveMod()
#test.Initialize(1,1)
#Contains Constructor for Default valves (starting address 1, 24 ports)
#Is used over importing DLL to all other files for clealiness and Customizable exceptions
class uv_vis:
    def __init__(self):
        self.uv_server = '' #variable for server

                     
    def scan(self, filename):
         #Insert call to UVVis dll to run scan here

         pass
    def process(self):
        #function for processing the data into neat I vs freq data, return dict so that NMR functions can be copied
        pass