from Devices.Valvebox.valvebox_python_api import valves
#from ika.magnetic_stirrer_devin import MagneticStirrer
from Devices.SyringePump.syringe_pump_api import syring_pump
from Devices.DeviceTransport.transport_methods import NodeTree
import time
"""This file is where you add new commands
    Add the command name and function as a dict. entry
    Then, define the function bellow (please document things as added)
    
    Commands starting with _ are dev commands and are not intended for user use
    Standards: Always Take device_dictionary(dict), command(str), and arguments(list(str))"""
class command_controller: 
    def __init__(self, device_dictionary, node_dictionary):
        #Device Dictionary holds all device info
        self.device_dictionary = device_dictionary

        #node_tree handles connections - for editing path finding see transport_methods.py
        self.node_tree = node_dictionary
        self.cleaning_volume = 5
        self.clean_routine = self._get_clean_routine()
        #INSERT COMMANDS HERE
        self.COMMANDS = {
        "SET_VALVE": self.SetValve,
        "SET_TEMP": self.SetTemp,
        "SET_PUMP": self.SetSyringe,
        "TRANSFER": self.Transfer,
        "_SET_VALVE_PATH": self._set_valve_path,
        "_SET_EXPERIMENT_VIAL": self._set_experiment_vial,
        "MeasureVial":self.MeasureVial,
        "Shim":self.Shim,
        "Null_Shim":self.Null_Shim,
        "UVMeasureVial":self.UVMeasureVial

    }
    ###DEFINE COMMANDS HERE###
    def _get_clean_routine(self):
        """Creates list of components to use for cleaning"""
        cleaning_list = []
        components = self.node_tree.GetComponents()
        for component in components:
            if "cleaning" in components[component]:
                for cleaning_step_number in components[component]["cleaning"]:
                    cleaning_list.append(tuple(cleaning_step_number, component))

        cleaning_list = sorted(cleaning_list)
        self.clean_routine = [a[1] for a in cleaning_list] 
            

    def Shim(self, args):
        """Args: Vial_to_shim, Save_directory, File_name, shim_file(optional)"""
        syringe = self.node_tree.GetComponents()["NMR"]["syringe"]
        waste_volume = self.node_tree.GetComponents()["NMR"]["waste_volume"]
        shim_volume = self.node_tree.GetComponents()["NMR"]["shim_volume"]

        source,scan_name, directory = args[0:3]
        if len(args) > 3:
            shim_file = args[-1]
        else:
            shim_file =None

        #Move Shim Material to NMR
        self._extract([source, syringe, shim_volume])
        self._dispense([syringe, "waste", waste_volume]) # Remove air
        self._set_valve_path(["NMR", source]) # Set path from NMR back to source vial
        self._dispense([syringe, "NMR", shim_volume]) #Push Through NMR

        #Run Shim and Take a measurement of the shim liquid for LW calculation
        self.device_dictionary["NMR"][0].shim(scan_name,directory,shim_file)
        scan_name = f"result_{scan_name}"
        self.device_dictionary["NMR"][0].scan(scan_name,directory,shim_file)
        self._dispense([syringe, "NMR", shim_volume]) 

        self.clean(syringe)

    def Null_Shim(self, args):
        "Just starts the NMR shimming, no valve movement"
        scan_name, directory = args[0:3]

        #Run Shim and Take a measurement of the shim liquid for LW calculation
        self.device_dictionary["NMR"][0].shim(scan_name,directory)

    def UVMeasureVial(self, args):
        """Measure a vial using the UV vis\n
        [source, scan_name, scan_directory] """

    def SetValve(self, args):
        """Args=[int, int]\n
               =[Valve, Port]"""
        
        self.device_dictionary["valvebox"][0].set_valve(valve=int(args[0]), port=int(args[1]))

    def SetTemp(self, args):
        """Args=[str, double]\n
        =[hotplate Name, temperature]"""
        com_port = self.device_dictionary["hotplate_names"][args[0]]

        self.device_dictionary["hotplate"][int(com_port)].SetTemp(float(args[1]))
        self.node_tree.SetHotplate(args[0], args[1])

    def SetSyringe(self, args):
        """Set Specified syringe Pump to Port\n
        args= pump(int), port(int)"""

        self.device_dictionary["syringe_pump"][0].set_port(int(args[0]),int(args[1]))

    def Transfer(self, args):
        """Transfer specified amount from component 1 to component 2
        Input: source, target, volume, syringe"""
        
        source = args[0]
        target = args[1]
        volume = args[2]
        syringe = args[3]
        #print(F"Transfering {volume}ml from {source} to {target}")
        self._extract([source, syringe, volume])
        self._dispense([syringe, target, volume])
    
    def MeasureVial(self, args):
        """Transfer from target vial to NMR syringe pump:  push into Nmr, scan, then cycle fluid back to source\n
        args: [source, scan_name, scan_directory, shim_file(opt.)]\n
        Notes: NMR must be connected to syringe specified in components.json
        Notes: Returns fluid
        todo: calibrate amount extracted"""
        #print(f"measuring vial with args {args}")
        syringe = self.node_tree.GetComponents()["NMR"]["syringe"] #TODO:implement in json file
        
        withdraw_volume = self.node_tree.GetComponents()["NMR"]["withdraw_volume"]
        waste_volume = self.node_tree.GetComponents()["NMR"]["waste_volume"]
        measure_volume = float(withdraw_volume)-float(waste_volume)
        source,scan_name, directory = args[0:3]
        if len(args) > 3:
            shim_file = args[-1]
        else:
            shim_file =None

        #TODO: Seperate NMR into NMR; NMR_INPUT; NMR_OUTPUT items in components.json to allow for transfer between nodes for NMR cleaning
        self._extract([source, syringe, withdraw_volume])
        self._dispense([syringe, source, waste_volume]) # Remove air - switch source to "waste" if desired
        self._set_valve_path(["NMR_OUT", source]) # Set path from NMR back to source vial
        self._dispense([syringe, "NMR", measure_volume]) #Push Through NMR

        #TODO, may need to adjust nmr.scan to save correctly
        self.device_dictionary["NMR"][0].scan(scan_name,directory,shim_file) #Run the Scan 
        self.clean(syringe)

   
    def clean(self, syringe):
        for cleaning_agent in self.clean_routine:
            self._extract([cleaning_agent, syringe, self.cleaning_volume])
            self._set_valve_path(["NMR_OUT", "waste"]) # Set path from NMR back to source vial
            self._dispense([syringe, "NMR", self.cleaning_volume]) #Push Through NMR


    ###HELPER FUNCTIONS - USE TO RUN USER FRONT FUNCTIONS###    
    def _set_experiment_vial(self, args):
        """args: measurement_name\n
        Finds the first unused vial and sets it's name/properties to be called by an experiment\n
        TODO: need a way to mark a vial as done to free up hotplate"""

        """
        Vial Component Breakdown:
        hotplate_temp: false -> set to temperature to indicate hotplate is active
        used: false - > used to indicate if the vial is being used for a reaction (current or previous)
        complete: false -> set to true when a reaction is complete to indicate hotplate openness
        """

        requested_temp = args[1]

        #File to create for passing info to Experiment
        indicator_file = args[2]
        already_heated, hotplate_name, temperature = self.node_tree.set_experiment_vial(args[0], args[1])

        if already_heated:

            with open(indicator_file, 'w') as f:
                f.write(f"{temperature}\n{hotplate_name}")


                
        else:
            self.SetTemp(hotplate_name, temperature)

            with open(indicator_file, 'w') as f:
                f.write(f"{temperature}\n{hotplate_name}")
          



    def _set_valve_path(self, args):
        """Set valves to connect components"""
        print(f"Set_valve_paths: {args}")
        path = self.node_tree._find_path(args[0], args[1])
        print(path)
        for step in path:
            
            if("syringe" in str(step[0]) ):
                self.SetSyringe([int(self.node_tree.GetComponents()[step[0]]["syringe_number"]), int(step[1])])
                #print(f"Setting Syringe {step[0][-1]} to port {step[1]}")
            else:
                self.SetValve([step[0],step[1]])
                #print(f"Setting Valve {step[0]} to port {step[1]}")
    def _extract(self, args):
        """Extract desired amount (ml) from specified source to specified syringe. sleeps 5 seconds to allow pressure to equalize
        Input: syringe, source, volume"""
        #print(f"Extract: {args}")
        volume = args[2]
        target = args[0] #1 If these are swapped cant find path but also thats the fix for all sub
        source = args[1] # 0
        
        #print("Extract Source: " + source)
    
        #print(f"Extract: set path from {target} to {source}")
        self._set_valve_path([target, source])
        self.device_dictionary["syringe_pump"][0].withdraw(int(source[-1]), int(volume))
        time.sleep(5)

    def _dispense(self, args):
        """dispense desired amount (ml) from specified syringe to specified component
        input: syringe, target, volume"""
        #print(f"Dispense: {args}")
        volume = args[2]
        target = args[1]
        source = args[0]
        #print(f"Dispense args: {args}")
        #print(int(source[-1]))
        #print("Dispense Source: " + source)
        #input()
        self._set_valve_path([source, target])
        self.device_dictionary["syringe_pump"][0].dispense(int(source[-1]), int(volume))

    def hold_until_complete(self, vial, initial_time):
        """Run sequencial scans on given vial, runs 1 scan initially, then waits initial time
        Input: Vial name, initial time"""
        print("NYI: hold until complete")

    def get_command (self, command):
        return (self.COMMANDS[command])
    
    def issue_commands(self, campaign_commands):
        """First Generates the COMMANDS dictionary/functions
        Then, passes each command in the command_dict and executes with coresponding args
        inputs: command_dict(keys:commands, arguments)\n"""

        for command_num, command in enumerate(campaign_commands["commands"]):
            self.COMMANDS[command](campaign_commands["arguments"][command_num])



