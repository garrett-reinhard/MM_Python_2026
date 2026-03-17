import threading
import os
import time

    


class NMR:
    """Class for running NMR scans.  uses the main function calls from qmcontrol
    Needs to be set up to close the UI when a scan is done.  Additional settings
    can be added as desired for scan settings.  currently always takes average scan
    and not individual"""
    def __init__(self, global_settings):
        
        self.settings = {}
        #Path to Shim File
        self.settings["shim_file"] = r"./Devices/NMR/shims/shim_file.json"
        #self.nmr_control = nmr_thread()
    

        

    def scan(self, file_name, save_directory, shim_file=None):
        ROOTPATH = os.getcwd()
        """Take NMR scan\nInputs: Filename, directory"""
        TRIGGER_PATH = r'.\Devices\scan_trigger.txt'
        print("RUNNING SCAN")
        
        self.settings["file_name"] = file_name
        self.settings["save_directory"] = save_directory
        if shim_file == None:
            shim_file = self.settings["shim_file"]
        else:
            shim_file= shim_file
        #Ensure file path matches TRIGGER_DIRECTORY in qmcontrol.py!
        with open(TRIGGER_PATH, 'w') as f:
            f.write("scan\n")
            f.write(f"{file_name}\n")
            f.write(f"{ROOTPATH}{save_directory[1:]}\n") 
            f.write(f"{ROOTPATH}{shim_file[1:]}\n")  

        #QMcontrol module delete trigger file when scan completed
        while os.path.exists(TRIGGER_PATH):
            print("scan not completed, sleeping 10")
            time.sleep(10)
        print("Scan completed")

        #TODO:
        #verify_scan
        #if verify = bad
        #move scan to bad scan folder for analysis
        #rescan with same parameters
       

    def shim(self, file_name, save_directory, shim_file=None):
            ROOTPATH = r"../../../" # ROOTPATH is relative to the QMagnetics software run.py
            """Take NMR scan\nInputs: Filename, directory"""
            TRIGGER_PATH = r'.\Devices\NMR\scan_trigger.txt'
            print("RUNNING SHIM")
            
            self.settings["file_name"] = file_name
            self.settings["save_directory"] = save_directory
            #Set Starting shim if present
            if shim_file == None:
                shim_file = self.settings["shim_file"]
            else:
                shim_file= shim_file

            #Ensure file path matches TRIGGER_DIRECTORY in qmcontrol.py!
            with open(TRIGGER_PATH, 'w') as f:
                f.write("shim\n")
                f.write(f"{file_name}\n")
                f.write(f"{ROOTPATH}{save_directory[1:]}\n") 
                f.write(f"{ROOTPATH}{shim_file[1:]}\n")  

            #QMcontrol module delete trigger file when scan completed
            while os.path.exists(TRIGGER_PATH):
                print("shim not completed, sleeping 10")
                time.sleep(10)
            print("Scan completed")

            #TODO:
            #verify_scan
            #if verify = bad
            #move scan to bad scan folder for analysis
            #rescan with same parameters