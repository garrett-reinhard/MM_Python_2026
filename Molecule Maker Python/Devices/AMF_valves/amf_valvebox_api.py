
from subprocess import *
import amfTools
from amfTools import AMF, Device
#test = ValveMod()
#test.Initialize(1,1)
#Contains Constructor for Default valves (starting address 1, 24 ports)
#Is used over importing DLL to all other files for clealiness and Customizable exceptions
class amf_valves:
    def __init__(self):
        amf_list =amfTools.util.getProductList()
        self.valve_list = []
        for i in range(len(amf_list)):
            amf : amfTools.AMF = None
            amf = amfTools.AMF(amf_list[i])
            self.valve_list.append(amf)

            print(f"Connected to product {amf.getType()} on port {amf.getSerialPort()}\n")
            amf.home()
            #amf = amfTools.AMF(list_amf[0])  
        print(self.valve_list)
    def set_valve(self, valve, port):
        """Set valve to specified port (1=8)"""
        self.valve_list[valve-1].valveMove(port)