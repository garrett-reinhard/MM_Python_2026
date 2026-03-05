from Devices.NMR.qmcontrol.qmcontrol.__main_pulse__ import main as run_pulse
import threading


class NMR:
    """Class for running NMR scans.  uses the main function calls from qmcontrol
    Needs to be set up to close the UI when a scan is done.  Additional settings
    can be added as desired for scan settings.  currently always takes average scan
    and not individual"""
    def __init__(self, global_settings):
    
        self.settings = {}
        #Path to Shim File
        self.settings["shim_file"] = "./Devices/NMR/shims/shim_file.json"

        self.settings["save_directory"] = global_settings["directories"]["root"]


    def scan(self, file_name):
        self.settings["file_name"] = file_name
        run_pulse(self.settings)
        #scanning = threading.Thread(target=run_pulse, args=self.settings)
        #scanning.start()
        #scanning.join()
        print("done scanning :D")