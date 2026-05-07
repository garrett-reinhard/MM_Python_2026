from Devices.Valvebox.valvebox_python_api import valves
from Devices.AMF_valves.afm_valvebox_api import amf_valves
from Devices.HotPlate.hotplate_api import HotPlate
from Devices.SyringePump.syringe_pump_api import syring_pump
from Devices.NMR.nmr_api import NMR
from Devices.UVvis.uv_vis import uv_vis
from Devices.device_commands import command_controller
from Devices.DeviceTransport.transport_methods import NodeTree

import queue
import threading
"""
import multiprocessing
from multiprocessing import Process
from multiprocessing import Lock
from multiprocessing import Queue
"""
class Devices:
    def __init__(self,settings,components):
        self.DATA_DEBUG = settings["DATA_DEBUG"]
        if not self.DATA_DEBUG:

            self.create_devices(settings)
            self.components = components

            self.nodetree = NodeTree(components=self.components)
            self.command_issuer = command_controller(self.device_dictionary, self.nodetree)

            #Start device thread and queue
            self.q = queue.Queue()
            threading.Thread(target=self.worker, daemon=True).start()

    
    def create_devices(self, settings):
        """Create dictionary with each device desired for campaign"""
        global device_dictionary  
        device_dictionary = {}
        for device in settings["campaign"]["devices"]:
            if(settings["campaign"]["devices"][device]["is_enabled"]==True):
                device_dictionary[device] = []
                for instance in range(settings["campaign"]["devices"][device]["quantity"]):
                    if device == "valvebox":
                        print("ADDING VALVE")
                        device_dictionary[device].append((amf_valves()))
                        #device_dictionary[device].append("testing")
                    elif device == "hotplate":
                        #print(settings["campaign"]["devices"][device]["COMS"][str(instance)])
                        device_dictionary[device].append(HotPlate(settings["campaign"]["devices"][device]["COMS"][str(instance)]))
                        device_dictionary["hotplate_names"] = settings["campaign"]["devices"][device]["names"]
                        #device_dictionary[device].append("Testing")
                    elif device == "syringe_pump":
                        device_dictionary[device].append(syring_pump())
                        #device_dictionary[device].append("Testing")
                    elif device == "NMR":
                        device_dictionary[device].append(NMR(settings))
                    elif device == "uv_vis":
                        device_dictionary[device].append(uv_vis(settings))
                        pass
        self.device_dictionary = device_dictionary
    
    def worker(self):
        """Endlessly looping thread processing queue requests via run_command"""
        #May need to move create_devices() here so the thread worker has access to data?
        while True:
            task = self.q.get()
            self.run_command(task)


    def issue_command(self, command, args, key):
        """Inputs: command(str), args(list), key(lock)
        Device module acquires key, then puts the command into the queue for running
        Releases coresponding key when finished"""
        if not self.DATA_DEBUG:
            key.acquire()
            self.q.put([command, args, key])


    
    def run_command(self, args):
        """Command called to run queue requests, args =[command, inputs, key]
        releases key when the command is done running"""
        
        command = args[0]
        inputs = args[1]
        key = args[2]

        print(f"running command {command} with args {inputs}")
    
        func = self.command_issuer.get_command(command=command)
        
        func(inputs)
        key.release()
