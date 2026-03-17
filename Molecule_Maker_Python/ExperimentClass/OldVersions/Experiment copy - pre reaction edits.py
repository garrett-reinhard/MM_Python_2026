from Devices.DeviceClass import Devices
import queue
import threading
import statistics
"""
import multiprocessing
from multiprocessing import Process
from multiprocessing import Lock
from multiprocessing import Queue
"""
from Devices.DeviceClass import Devices
from  Devices.device_commands import command_controller
import time
from ExperimentClass.DataProcessing import *
from ExperimentClass.PeakClass import Peak
import plotly.express as px
class Experiment:
    """Class for each individual experiment.
        Init with device class and setup params pulled from main campaign
        reading input files"""
    def __init__ (self, devices, setup_dictionary):
        #DEBUG VARS
        self.DEBUG_PLOTS = False #Placeholder for plotting things during data processing
        self.DEBUG = False
        self.DEBUG_SCAN_NUMBER = -1

        #Toggle to just Shim the NMR and nothing else; ensure valveboxes and syringes are disabled in settings
        self.NMR_RUNNER = True
        
        #USER-MANAGED VARS
        self.Devices = devices
        self.current_vial = "EXPERIMENT_VIAL"
        self.next_temperature = 20 #Starting temp in C
        self.solution_reference = setup_dictionary["solution_reference"]
        self.shim_source = "Chlorine" #TODO pull from startup script
        self.info = setup_dictionary
        self.reactions = []
        self.peaks = []
        
        self.ppm_reference = 0 #TODO pull from startup script

        #VARS FOR SOFTWARE CONTROL
        self.ACCEPTABLE_SHIM_LINEWIDTH = 0.2
        self.DEFAULT_WAIT_TIME = 900 #Standard wait time in seconds before fitting algorithm has estimated finish times
        self.MAX_WAIT_TIME = 3600 #Max duration a reaction will run before terminating.
        self.shim_linewidth = 0
        self.scan_number = 0
        self.shim_file = None
        self.shim_count = 0 # Used to track active shim file
        self.baseline_volume = 0

    def _curate_commands(self):
        """Change all commands to accomodate any changes (like experiment vial)"""
        for idx, arg_list in enumerate(self.command_args):
            for index, arg in enumerate(arg_list):
                if (arg == self.current_vial):
                    self.command_args[idx][index] = self.next_vial
                arg.replace(self.current_vial, self.next_vial)

    def current_time(self):
        if not self.DEBUG:
            return(abs(round(time.time()- self.reactions[self.current_reaction]["start_time"], 2)))
        else:
            self.DEBUG_SCAN_NUMBER += 1
            return self.DEBUG_SCAN_NUMBER
        
    def set_vial(self, requested_temperature):
        """Send commands to the device driver to allocate a vial for this reaction+key"""
        set_vial_command = "_SET_EXPERIMENT_VIAL"
        set_vial_args = [self.next_vial, requested_temperature]
        print(self.next_vial)

        self.key.release()
        self.Devices.issue_command(set_vial_command, set_vial_args, self.key) #TODO: need a way to mark a vial as done to free up hotplate
        self.key.acquire()

        self._curate_commands()
        self.current_vial = self.next_vial
        self.next_vial =

    def hold_until_complete(self):
        """Defines a dictionary for the reaction and marks reaction start time\n
        Takes a scan at T=0 and runs processing_scan_data after each iteration to process all scans for the reaction"""
        self.reaction_finished = False
        self.reactions[self.current_reaction]["measurements"]= []
        self.reactions[self.current_reaction]["start_time"] = round(time.time(), 2)
        self.reactions[self.current_reaction]["peaks"] = []
        self.reactions[self.current_reaction]["product_peaks"] = []
        while not self.reaction_finished:
            
            self.reactions[self.current_reaction]["save_folder"]= self.info["reaction_folders"][self.current_reaction]
            scan_save_point =self.reactions[self.current_reaction]["save_folder"]

            good_scan = False
            bad_scan_count = 0
            #run scan until good
            while not good_scan:
                current_time = self.current_time()
                scan_name = f"scan_{self.scan_number}_time_{current_time}"
                self.key.release()
                self.Devices.issue_command("MeasureVial", [self.current_vial,scan_name,self.reactions[self.current_reaction]["save_folder"], self.shim_file], self.key)
                self.key.acquire()

                scan_filepath = f"{scan_save_point}/{scan_name}_ave.jdx"

                # check if scan is good; process and reduce data
                good_scan, scan_data, scan_dictionary = read_NMR(scan_filepath, offset=self.solution_reference) # scan data has PPM and intensity
                scan_data["PPM"] = offset_nmr_data(scan_data['PPM'], scan_data["intensity"], self.ppm_reference)

                #Check conditions for rescanning - TODO: remove continue comments when done with testing.
                scan_linewidth = get_shim_linewidth(scan_data["PPM"], scan_data["intensity"], self.ppm_reference)
                if not good_scan:
                    if bad_scan_count < 3:
                        print(f"bad scan: noise.\n reset number {bad_scan_count}")
                        continue
                    else:
                        print("CAUTION: REPETATIVE FAILED SCANS. \nAwaiting User Input to attempt a Shim")
                        #input()
                        bad_scan_count = 0
                        self.shim_experiment()
                        continue
                    #os.remove(scan_filepath)
                if scan_linewidth < self.ACCEPTABLE_SHIM_LINEWIDTH:
                    print(f"Linewidth too large ({scan_linewidth}); attempting shimming. . .")
                    self.shim_experiment()
                    bad_scan_count = 0
                    good_scan = False
                    #continue

                plt.plot(scan_data["PPM"], scan_data["intensity"], marker='o', markersize =0.5)
                plt.savefig(f"./{self.current_time()}_data_good_scan{str(good_scan)}_linewidth_{scan_linewidth}_.png")
                
            #process scan/compare to previous scans
            self.reactions[self.current_reaction].peaks, spectrum_fit = peak_finding(scan_data, good_peaks=self.reactions[self.current_reaction].peaks)
            if self.scan_number == 0:
                self.starting_volume = sum(spectrum_fit)
            self.scan_number += 1


            for peak in self.reactions[self.current_reaction].peaks:
                peak.measurement_times.append(current_time)
                peak.measurement_concentrations.append
                peak.update_score()
                peak.plot_score()
                peak.plot_fits()
                print(f"{peak.center} , {peak.score}")
            #input()
            
            new_measurement = Measurement()
            new_measurement.scan_filepath = scan_filepath
            new_measurement.scan_name =scan_name
            new_measurement.scan_data =  scan_data#Has intensity and PPM catagories
            new_measurement.scan_dictionary = scan_dictionary
            self.reactions[self.current_reaction].measurements.append(new_measurement) 
            
            
            time.sleep(self.process_scan_data())
            #Decide if complete
            #Return Total time run
            
            
    def process_scan_data(self):
        """Peak identification + end point analyzer\n
        Process a reactions scans.  Return time to wait and determine if end point has been reached here\n
       Uses self.reactions[current_reaction] as primary source of data, treats entry  -1 as yet to be processed data"""
        predicted_times = []
        cumulative_yield = 0
        for peak in self.reactions[self.current_reaction]["peaks"]:
            peak.measurement_concentrations.append(peak.integrals[-1]/self.starting_volume)
            
            if peak.type == "product":
                time_prediction = product_90p_time(peak.measurement_concentrations, peak.measurement_times)
                predicted_times.append(time_prediction)
                cumulative_yield += peak.measurement_concentrations[-1]

            #elif peak.type == "reactant":
            #   time_prediction = reactant_90p_time(peak.measurement_concentrations, peak.measurement_times)

        if predicted_times != []:
            print(f"Predicted Times:\n{predicted_times}")
            print(f"Average Predicted Time:\n{statistics.mean(predicted_times)}")
            if self.current_time() <   
            wait_time = statistics.mean(predicted_times)/2

            self.reactions[self.current_reaction].measurements[-1].product_yield = cumulative_yield
            self.reactions[self.current_reaction].measurements[-1].predicted_time = wait_time
            if self.DEBUG:
                print(f"DEBUG MODE ENABLED: WAIT TIME {wait_time}")
                return (wait_time)
            else:
                return (wait_time)
        else:
            print("no results yet, waiting default time.")
            return(self.DEFAULT_WAIT_TIME)

    def shim_experiment(self):
        """Shim to a preset shim_source solvent in components.json
        Returns True when system is shimmed"""
        failed_shim_count = 0
        shim_name = self.info["experiment_name"] + f"_shim_{self.shim_count}.json"
        shim_directory = r"./save_data/shims"

        self.key.release()
        self.Devices.issue_command("Shim", [self.shim_source, shim_name, shim_directory, self.shim_file], self.key)
        self.key.acquire()

        self.shim_file = f"{shim_directory}/{shim_name}"
        self.shim_result = f"result_{shim_name}_ave.jdx"
        self.shim_result_filepath =f"{shim_directory}/{self.shim_result}"
        
        good_scan, shim_data, scan_dictionary = read_NMR(self.shim_result_filepath)
        shim_linewidth = get_shim_linewidth(shim_data['PPM'],shim_data['intensity'], self.ppm_reference)
        self.shim_count += 1

        if (good_scan == False) or (shim_linewidth>self.ACCEPTABLE_SHIM_LINEWIDTH):
            print(f"Bad Shim; good?{good_scan}; linewidth={shim_linewidth}")

            #return False
        return True
        #TODO Implement shim-value check and default fit paramater checks
        #Needs to do the following
        #Take a fake measurement
        #Fit gaussian
        #Return linewidth
    def AutoShim(self):
        """Continuosly run shims forever"""
        shimming_complete = False
        while not shimming_complete:
            
            shim_status = self.shim_experiment()
            while not shim_status:
                self.shim_experiment()
            time.sleep(60) #Edit this for sleep time between shims
            
    def OVERRIDE_EXPERIMENT_SHIM(self):
        """Prevents any experimental executions and simply runs  shims with default names forever"""
        shim_number = 1
        while True:
            shim_name =f"shim_{str(shim_number)}.jdx"
            self.key.release()
            self.Devices.issue_command("Null_Shim",[shim_name, "."], self.key)
                #Wait for Devices to release thread.  Can implement a locked/sleep loop to run other things while waiting
            self.key.acquire()
            shim_number +=1

    def get_yield():
        pass

    def analyzer_process(self):
        """NYI: implement specific analyzer features here \n Returns next temperature to test"""
        #Create DF from self.reactions list
        #Run EDBO+
        #Get next Datapoint tempo
        pass

    def run_commands(self):
        """Run commands bount to self.commands sequentially"""
        for index, command in enumerate(self.commands):
            self.key.release()
            self.Devices.issue_command(self.commands[index], self.command_args[index], self.key)
            #Wait for Devices to release thread.  Can implement a locked/sleep loop to run other things while waiting
            self.key.acquire()

    def start_experiment(self):
        self.key = threading.Lock()
        self.key.acquire()

        if self.NMR_RUNNER:
            self.OVERRIDE_EXPERIMENT_SHIM()


        #Log start of experiment, sleep for insurnace
        t = {self.info["experiment_name"]}
        print(f"Starting experiment {t}")
        time.sleep(5)

        #Prep commands from list
        self.commands = self.info["commands"]
        self.command_args = self.info["command_arguments"]

        for reaction_number in range(int(self.info["reactions"])):
            self.reactions.append(Reaction)

            self.current_reaction = reaction_number #Declaring this prevents needing to pass args to the data processing functions.  Makes the flow easier to read
            self.next_vial = self.info["experiment_name"]+f"reaction_{reaction_number}"
            
            self.set_vial(self.next_temperature)
            self.run_commands()   
            
            self.hold_until_complete() #Gets reaction datapoint to feed into analyzer
            self.next_temperature = self.analyzer_process()


class Measurement:
    """This class EXCLUSIVELY holds data from a measurement for easier management and autofill ability"""
    def __init__(self):
        self.scan_filepath = ""
        """Holds the filepath to the JDX file"""

        self.scan_name = ""
        """The name of the measurement: scan_number+elapsed_time"""

        self.scan_data = None 
        """Dictionary with processed data: Keys =  intensity and PPM """

        self.scan_dictionary = None
        """Contains Extra info extracted when reading the JDX file"""

        self.product_yield = 0
        """calculated concentration of all product peaks in this measurement"""

        self.predicted_time = None
        """Predicted completion time of reaction based on this measurement.  If no prediction made is None"""
        

class Reaction:
    """This class EXCLUSIVELY holds information on a reaction for easier management and autofill ability"""
    def __init__(self):
        self.start_time = float
        """Start time of the reaction rounded to 2 decimals"""

        self.measurements = []
        """List containing every measurement instance for this reaction"""

        self.peaks = []
        """List of all recorded peaks for this reaction"""

        self.product_peaks = []
        """List of all peaks that have been defined as products"""

        self.reactant_peaks = []
        """List of all peaks that have been defined as products"""

        self.save_folder = ""
        """Save folder for all data related to this reaction"""

        self.predicted_time = None
        """Predicted completion time of reaction based on this measurement.  If no prediction made is None"""
        
        self.starting_volume = float
        """The volume of the reaction at t=0\n Integrated peak area at t=0"""
            
        self.temperature = float
        """Temperature of this reaction \n Used in Analyzer/Planner"""

        self.final_reaction_time = float
        """The final duration of this reaction to reach completion\n Used in Analyzer/Planner"""

        self.reaction_finished = False
        """Is the reaction complete (Bool)"""