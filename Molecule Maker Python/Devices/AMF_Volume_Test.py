import amfTools
from amfTools import AMF, Device
from AMF_valves.amf_valvebox_api import amf_valves
from SyringePump.syringe_pump_api import syring_pump
import time
def confirm_action(prompt="Do you want to continue? (y/n): "):
    while True:
        # Get input, remove trailing space, and convert to lowercase
        answer = input(prompt).strip().lower()
        
        if answer in ('y', 'yes'):
            return True
        if answer in ('n', 'no'):
            return False
            
        print("Invalid choice. Please enter 'y' or 'n'.")

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
valve = amf_valves()

syringe_loaded = False
if confirm_action("Load syringe Pump? y/n:"):
    syringe = syring_pump()
    syringe_loaded = True


if confirm_action("Perform port testing cycle? y/n:"):
    i = 1
    while(i <9):
        valve.set_valve(0,i)
        input(f"Confirm Valve is at port {i}. Abort if not.")
        i+=1
    print ("Port testing complete, returning valve to 0")
    valve.set_valve(0,1)

if syringe_loaded and confirm_action("Perform volume testing cycle? y/n:"):
    source_port = int(input("What port on the valve is the source container?"))
    volume = int(input("How many ml per cycle to transfer?"))
    destination_port = int(input("What port on the valve is the target destination container?"))
    input("Ensure syringe is connected to center port on valve.")
    syringe_side_port =int( input ("What port is the syringe pump connected to the valve on (syringe side)"))
    loops = int(input("how many iterations to perform"))
    verify_loops = confirm_action("await user input between loops to verify volume is correct? y/n:")
    sleep_time = int(input("Input pressure equalization sleep time for syringe (Rec. Minimum 3)"))
    loop_count=0

    #Begin Loops
    syringe.set_port(0,syringe_side_port)
    while(loop_count<loops):
        valve.set_valve(0, source_port)
        syringe.withdraw(0,volume)
        time.sleep(sleep_time)

        valve.set_valve(0,destination_port)
        syringe.dispense(0,volume)
        time.sleep(sleep_time)

        if verify_loops:
            input("Please verify the volume in the output vial is correct")
        loop_count+=1
