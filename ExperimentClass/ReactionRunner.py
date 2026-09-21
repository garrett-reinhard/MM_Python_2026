from Devices.DeviceClass import Devices
import queue
import threading
import statistics
import copy
import threading
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
from ExperimentClass.DataProcessing import ScanData
from ExperimentClass.PeakClass import Peak
import plotly.express as px
from ExperimentClass.Planners.EDBO import EDBOplus
from ExperimentClass.Experiment import Reaction


class ReactionRunner:
    """Class for each parrallel reaction"""
    def __init__ (self, devices):
        #DEBUG VARS
        self.DEBUG_PLOTS = False #Placeholder for plotting things during data processing
        self.DEBUG = True
        self.DEBUG_SCAN_NUMBER = -1

        self.solution_reference_dictionary = json.load(open("./CampaignSetup/solution_references.json"))
        """Dictionary containing all available solution reference PPM values || A word of caution: the spelling and capitilization MUST be exact matches"""

        #Toggle to just Shim the NMR and nothing else; ensure valveboxes and syringes are disabled in settings
        self.NMR_RUNNER = False
        
        #USER-MANAGED VARS
        self.Devices = devices

        self.shim_source = "Chlorine" #TODO pull from startup script
        
        self.ppm_reference = 0 #TODO pull from startup script

        #VARS FOR SOFTWARE CONTROL
        self.ACCEPTABLE_SHIM_LINEWIDTH = 0.01
        self.MINIMUM_TIME = 5 #Minimum measurement interval; is default & is used to decide if reaction is done
        self.MAXIMUM_TIME = 3600 #Max measurement interval; larger measurement intervals get reduced to this value
        self.REACTION_KILL_TIME = 999999 #Time at which a reaction is deemed complete even if not finished
        self.REACTION_COMPLETE_THRESHOLD = 0.0005 #Rate of increase that the systems considers the reaction complete at. TODO: calculate based on init. points
        self.shim_linewidth = 0
        self.scan_number = 0
        self.shim_file = None
        self.shim_count = 0 # Used to track active shim file
        self.baseline_volume = 0

        
    def start_reaction(self, reaction: Reaction, results, result_index):
        """Runs in Thread\n places a list of [time, yield, reaction_obj] at place index"""
        self.key = threading.Lock()
        self.key.acquire()
        self.reaction: Reaction = reaction
        self.create_commands()
        self.run_commands()   
        
        self.hold_until_complete(self.reaction) #Gets reaction datapoint to feed into analyzer
        results[result_index] = [self.final_time, self.final_yield, self.reaction]



    def hold_until_complete(self, reaction: Reaction):
        """Defines a dictionary for the reaction and marks reaction start time\n
        Takes a scan at T=0 and runs processing_scan_data after each iteration to process all scans for the reaction"""

        reaction.start_time = round(time.time(), 2)
        self.DEBUG_SCAN_NUMBER = -1
        while not reaction.reaction_finished: 
            good_scan = False
            bad_scan_count = 0

            #run scan until good
            while not good_scan:
                self.current_runtime = self.reaction_runtime(reaction)
                scan_name = f"scan_{reaction.scan_number}_time_{self.current_runtime}"
                scan_filepath = f"{reaction.save_folder}/{scan_name}_ave.jdx"
                self.key.release()
                self.Devices.issue_command("MeasureVial", [self.current_vial,scan_name,reaction.save_folder, self.shim_file], self.key)
                self.key.acquire()

                # check if scan is good; process and reduce data
                good_scan, scan_data, scan_dictionary = read_NMR(scan_filepath, offset=self.solution_reference_dictionary[self.next_solvent.lower()]) # scan data has PPM and intensity
                scan_data.ppm = offset_nmr_data(scan_data.ppm, scan_data.intensities, self.ppm_reference)


                #Check conditions for rescanning - TODO: remove continue comments when done with testing.
                scan_linewidth = get_shim_linewidth(scan_data.ppm, scan_data.intensities, self.ppm_reference)
                print(f"Scan Linewidth: {scan_linewidth}")
                if not good_scan:
                    if bad_scan_count < 3:
                        print(f"bad scan: noise.\n reset number {bad_scan_count}")
                        continue
                    else:
                        print("CAUTION: REPETATIVE FAILED SCANS. \nAwaiting User Input to attempt a Shim")
                        bad_scan_count = 0
                        self.shim_experiment()
                        continue

                if scan_linewidth < self.ACCEPTABLE_SHIM_LINEWIDTH:
                    print(f"Linewidth too large ({scan_linewidth}); attempting shimming. . .")
                    self.shim_experiment()
                    bad_scan_count = 0
                    good_scan = False
                #PLOT: NMR scan
                plt.plot(scan_data.ppm, scan_data.intensities, marker='o', markersize =0.5)
                os.makedirs(f"{reaction.save_folder}/nmr_plots",exist_ok=True)
                plt.savefig(f"{reaction.save_folder}/nmr_plots/{self.current_runtime}_data_good_scan{str(good_scan)}_linewidth_{scan_linewidth}_.png")
                
            #process scan/compare to previous scans
            reaction.peaks, spectrum_fit = peak_finding(scan_data, good_peaks=reaction.peaks)
            if reaction.scan_number == 0:
                reaction.starting_volume = sum(spectrum_fit)
            reaction.scan_number += 1

            #Update All peaks' information
            os.makedirs(f"{reaction.save_folder}/peak_info",exist_ok=True)
            
            for peak in reaction.peaks:
                peak.measurement_times.append(self.current_runtime)
                peak.save_folder = f"{reaction.save_folder}/peak_info"
                peak.starting_volume = reaction.starting_volume
                peak.measurement_concentrations.append(peak.integrated_areas[-1]/peak.starting_volume)
                peak.update_score()
                peak.plot_score()
                peak.plot_fits()
            
            #Create Measurement Object for this measurement
            new_measurement = Measurement()
            new_measurement.scan_filepath = scan_filepath
            new_measurement.scan_name =scan_name
            new_measurement.scan_data =  scan_data#Has intensity and PPM catagories
            new_measurement.scan_dictionary = scan_dictionary
            reaction.measurements.append(new_measurement) 
            
            #Predict if reaction is completed
            sleep_time = self.predict_reaction_endtime(reaction)
            if not reaction.reaction_finished:
                time.sleep(sleep_time)
            else:
                print(f"reaction complete! total runtime: {reaction.final_reaction_time}")

            
            
    def predict_reaction_endtime(self, reaction: Reaction):
        """Peak identification + end point analyzer\n
        Process a reactions scans.  Return time to wait and determine if end point has been reached here\n
       Uses self.reactions[current_reaction] as primary source of data, treats entry  -1 as yet to be processed data"""
        predicted_times = []
        cumulative_yield = 0

        #Predict end time based on all product and reactant peaks
        for peak in reaction.peaks:
            if peak.type == "product":
                time_prediction = product_predict_endtime( peak.measurement_times,peak.measurement_concentrations,self.REACTION_COMPLETE_THRESHOLD, reaction.save_folder, peak.plot_name)
                if time_prediction > 0: #Easy way to verify quality of the prediction
                    predicted_times.append(time_prediction)
                    peak.predicted_times.append(time_prediction)
                    peak.times_with_predictions.append(self.current_runtime)
                    cumulative_yield += peak.measurement_concentrations[-1]
                    peak.plot_predicted_times()

            elif peak.type == "reactant":
                time_prediction = reactant_predict_endtime( peak.measurement_times,peak.measurement_concentrations, self.REACTION_COMPLETE_THRESHOLD, reaction.save_folder, peak.plot_name)
                if time_prediction > 0:
                    peak.times_with_predictions.append(self.current_runtime)
                    peak.predicted_times.append(time_prediction)
                    predicted_times.append(time_prediction)
                    peak.plot_predicted_times()

        if predicted_times != []:
            
            #Update most recent measurements product yield
            #current_time = self.reaction_runtime(reaction)
            average_prediction =  statistics.mean(predicted_times)
            reaction.measurements[-1].product_yield = cumulative_yield
            reaction.product_yield = cumulative_yield
            
            reaction.measurements[-1].ted_time = average_prediction
            print(f"Predicted Times:\n{predicted_times}")
            print(f"Average Predicted Time:\n{statistics.mean(predicted_times)}")



            # If Already past endtime return 0 and complete
            if self.current_runtime+self.MINIMUM_TIME > average_prediction:
                reaction.reaction_finished = True
                reaction.final_reaction_time = self.current_runtime
                self.final_yield = reaction.product_yield
                self.final_time =reaction.final_reaction_time
                
                return 0
        
            #If the sleeptime is longer than max_wait; wait max wait
            sleep_time = (average_prediction - self.current_runtime) / 2
            print(f"Sleep Time: {sleep_time}")
            if self.DEBUG:
                print(f"DEBUG MODE ENABLED: MIN TIME {self.MINIMUM_TIME}")
                return (self.MINIMUM_TIME)
            if sleep_time > self.MAXIMUM_TIME:
                return self.MAXIMUM_TIME
            return (sleep_time)
        
        #If no data return minimum time (useful at start of reaction)
        else:
            print("no results yet, waiting default time.")
            return(self.MINIMUM_TIME)

    def shim_experiment(self):
        """Shim to a preset shim_source solvent in components.json
        Returns True when system is shimmed"""
        print("Begining Shim")
        failed_shim_count = 0
        good_shim = False
        while not good_shim:
            shim_name = self.reaction.save_folder + f"_shim_{self.shim_count}.json"
            shim_directory = r"./save_data/shims"

            self.key.release()
            self.Devices.issue_command("Shim", [self.shim_source, shim_name, shim_directory, self.shim_file], self.key)
            self.key.acquire()

            self.shim_file = f"{shim_directory}/{shim_name}"
            self.shim_result = f"result_{shim_name}_ave.jdx"
            self.shim_result_filepath =f"{shim_directory}/{self.shim_result}"
            
            good_scan, shim_data, scan_dictionary = read_NMR(self.shim_result_filepath)
            shim_linewidth = get_shim_linewidth(shim_data.ppm,shim_data.intensities, self.ppm_reference)
            self.shim_count += 1

            if (good_scan == False) or (shim_linewidth>self.ACCEPTABLE_SHIM_LINEWIDTH):
                print(f"Bad Shim; good?{good_scan}; linewidth={shim_linewidth}")

                failed_shim_count +=1
            elif failed_shim_count > 3:
                input("Shimming error! multiple failed shim's attempted, halting to avoid missaligning magnets. awaiting user input to continue")
            else:
                good_shim = True
        return True

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


    def create_commands(self):
        """Create the commands to transfer the components determined by EDBO into a reaction vial, also sets solvent shift"""
        command_list = ["TRANSFER", "TRANSFER"]

        #Transfer Solvent args: Chlorine EXPERIMENT_VIAL 5 syringe_1
        transfer_solv_args = [self.reaction.solvent, self.reaction.current_vial, self.reaction.solvent_volume, self.reaction.syringe]
        #Transfer reagent
        transfer_reagent_args = [self.reaction.next_reagent, self.reaction.current_vial, self.reaction.next_reagent_volume, self.reaction.syringe]
        #Merge
        cmd_arg_list = [transfer_solv_args, transfer_reagent_args]

        #Bind to commands run by run_commands
        self.commands = command_list
        self.command_args = cmd_arg_list


    def run_commands(self):
        """Run commands bount to self.commands sequentially"""
        for index, command in enumerate(self.commands):
            self.key.release()
            self.Devices.issue_command(self.commands[index], self.command_args[index], self.key)
            #Wait for Devices to release thread.  Can implement a locked/sleep loop to run other things while waiting
            self.key.acquire()
    

    def reaction_runtime(self, reaction: Reaction):
        if not self.DEBUG:
            return(abs(round(time.time()- reaction.start_time, 2)))
        else:
            self.DEBUG_SCAN_NUMBER += 1
            return self.DEBUG_SCAN_NUMBER





class Measurement:
    """This class EXCLUSIVELY holds data from a measurement for easier management and autofill ability"""
    def __init__(self):
        self.scan_filepath = ""
        """Holds the filepath to the JDX file"""

        self.scan_name = ""
        """The name of the measurement: scan_number+elapsed_time"""

        self.scan_data = ScanData 
        """ScanData Class with intensity and PPM info"""

        self.scan_dictionary = None
        """Contains Extra info extracted when reading the JDX file"""

        self.product_yield = 0
        """calculated concentration of all product peaks in this measurement"""

        self.predicted_time = None
        """Predicted completion time of reaction based on this measurement.  If no prediction made is None"""
        

