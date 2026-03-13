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

        self.scan_number = 0
        """Number of times this reaction has been measured in the NMR"""

        self.product_yield = 0
        """Final yield of products based on final measurement time"""
        self.reagent = ""
        """Reagent in this reaction"""
        self.solvent = ""
        """Solvent in this reaction"""
        self.hotplate = ""
        """Hotplate this reaction took place on"""




class Experiment:
    """Class for each individual experiment.
        Init with device class and setup params pulled from main campaign
        reading input files"""
    def __init__ (self, devices):
        #DEBUG VARS
        self.DEBUG_PLOTS = False #Placeholder for plotting things during data processing
        self.DEBUG = True
        self.DEBUG_SCAN_NUMBER = -1

        #Info and Setup replacemen
        self.campaign_name = ""
        """Name of the campaign this experiment is to be included in"""
        self.experiment_name = ""
        """Name of experiment, based on setup filename"""
        self.number_of_reactions = 0
        """Maximum number of reactions to run for this experiment"""
        self.experiment_folder = ""
        """Folder location for this experiment"""
        self.reaction_scope = pd.DataFrame
        """EDBO formated reaction scope information"""
        self.EDBO_settings = {}
        """EDBO formated settings for planner optimization\nDoes not have filename for retraining"""
        self.solution_reference_dictionary = json.load(open("./CampaignSetup/solution_references.json"))
        """Dictionary containing all available solution reference PPM values || A word of caution: the spelling and capitilization MUST be exact matches"""
        self.syringe = ""
        """The syringe dedicated to this experiments reactions"""       
        self.campaign_csv = ""
        """Filepath to the CSV containing EDBO information for relevant campaign"""
        self.reaction_number = 0


        #Toggle to just Shim the NMR and nothing else; ensure valveboxes and syringes are disabled in settings
        self.NMR_RUNNER = False
        
        #USER-MANAGED VARS
        self.Devices = devices
        self.current_vial = "EXPERIMENT_VIAL"
        self.next_temperature = 20 #Starting temp in C

        self.shim_source = "Chlorine" #TODO pull from startup script
        
        self.reactions = []
        self.peaks = []
        
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

    def _curate_commands(self):
        """Change all commands to accomodate any changes (like experiment vial)"""
        for idx, arg_list in enumerate(self.command_args):
            for index, arg in enumerate(arg_list):
                if (arg == self.current_vial):
                    self.command_args[idx][index] = self.next_vial
                arg.replace(self.current_vial, self.next_vial)

    def reaction_runtime(self, reaction: Reaction):
        if not self.DEBUG:
            return(abs(round(time.time()- reaction.start_time, 2)))
        else:
            self.DEBUG_SCAN_NUMBER += 1
            return self.DEBUG_SCAN_NUMBER
        
    def set_vial(self, requested_temperature, reaction: Reaction):
        """Send commands to the device driver to allocate a vial for this reaction+key"""
        set_vial_command = "_SET_EXPERIMENT_VIAL"
        heater_file = reaction.save_folder + "\heater.txt"
        set_vial_args = [self.next_vial, requested_temperature, heater_file] #next vial name, temperature request, reaction save folder (for reading return temp.)
        print(self.next_vial)

        self.key.release()
        self.Devices.issue_command(set_vial_command, set_vial_args, self.key) #TODO: need a way to mark a vial as done to free up hotplate
        self.key.acquire()
        
        #Read The temperature the experiment will actually run at
        if not self.DEBUG:
            with open(heater_file) as file:
                    reaction.temperature = float(file.read().splitlines()[0])
                    reaction.hotplate = file.read().splitlines()[1]
                    os.rename(reaction.save_folder, reaction.save_folder+f"_{reaction.hotplate}")
                    reaction.save_folder = reaction.save_folder+f"_{reaction.hotplate}"
            os.remove(heater_file)


        #self._curate_commands()
        self.current_vial = self.next_vial
        #self.next_vial = #TODO

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
            shim_name = self.experiment_name + f"_shim_{self.shim_count}.json"
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
        transfer_solv_args = [self.next_solvent, self.current_vial, self.next_solvent_volume, self.syringe]
        #Transfer reagent
        transfer_reagent_args = [self.next_reagent, self.current_vial, self.next_reagent_volume, self.syringe]
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
    
    def start_experiment(self):
        #self.key = threading.Lock()
        #self.key.acquire()

        if self.NMR_RUNNER:
            self.OVERRIDE_EXPERIMENT_SHIM()


        #Log start of experiment, sleep for insurnace
        print(f"Starting experiment {self.experiment_name}")
        print(self.campaign_csv)
        time.sleep(5)

        self.EDBO_reaction_setup()
            
    def EDBO_reaction_setup(self):
        """Run the EDBO optimizer and get the next solvent, reagent, temperature, and concentration to run"""


        batch_size = self.EDBO_settings["batch"]
        current_reaction_number = 0
        print(self.campaign_csv)
        while current_reaction_number < self.number_of_reactions:
            ### Update Reaction scope ###
            self.reaction_scope =EDBOplus().run(
            filename=self.campaign_csv,  # Previously generated scope.
            objectives=self.EDBO_settings["objectives"],  # Objectives to be optimized.
            objective_mode=self.EDBO_settings["objective_mode"],  # Maximize yield and ee but minimize side_product.
            batch=self.EDBO_settings["batch"],  # Number of experiments in parallel that we want to perform in this round.
            columns_features=self.EDBO_settings["columns_features"], # features to be included in the model.
            init_sampling_method=self.EDBO_settings["init_sampling_method"],  # initialization method.
            seed=0
            )

            reaction_threads = []
            reaction_results = [None] * batch_size
            
            for a in range(batch_size):
                dup_class = copy.deepcopy(self)
                dup_class.next_temperature = self.reaction_scope.loc[a, 'temperature']
                dup_class.next_solvent = self.reaction_scope.loc[a, 'solvent'] 
                dup_class.next_reagent = self.reaction_scope.loc[a, 'reagent'] 
                dup_class.next_solvent_volume = self.reaction_scope.loc[a, 'solvent_volume']
                dup_class.next_reagent_volume = self.reaction_scope.loc[a, 'reagent_volume']
                dup_class.reaction_number = current_reaction_number
                dup_thread =threading.Thread(target=dup_class)
                reaction_threads.append(threading.Thread(target=dup_class.start_reaction, args=(reaction_results, current_reaction_number)))
                current_reaction_number +=1

            for a in reaction_threads:
                a.start()
        
            for i in range(len(reaction_threads)):
                reaction_threads[i].join()

            for idx, result in enumerate(reaction_results):
                if not result:
                    input("error Ef: No data returned from a threaded experiment Perhaps Check: \n 1) Too many reactions for batch size\n 2) data save destination errors")
                final_time = result[0] 
                final_yield = result[1]
                self.reactions.append(result[2])
                
                self.reaction_scope.loc[idx, 'yield'] = final_yield
                self.reaction_scope.loc[idx, 'time'] = final_time
            self.reaction_scope.to_csv(self.campaign_csv)

    def start_reaction(self, results, result_index):
        """Runs in Thread\n places a list of [time, yield, reaction_obj] at place index"""
        self.key = threading.Lock()
        self.key.acquire()
        self.current_reaction = self.reaction_number #Declaring this prevents needing to pass args to the data processing functions.  Makes the flow easier to read
        self.next_vial = self.experiment_name+f"reaction_{self.reaction_number}"

        current_reaction = Reaction()
        save_folder = f"{self.experiment_folder}/{self.next_reagent}_{self.next_reagent_volume}_{self.next_solvent}_{self.next_solvent_volume}"
        os.makedirs(save_folder, exist_ok=True)
        current_reaction.save_folder= save_folder
        current_reaction.solvent = self.next_solvent
        current_reaction.reagent = self.next_reagent
        self.set_vial(self.next_temperature, current_reaction) #TODO get temperature return, pass to current_reaction.temperature
        self.create_commands()
        self.run_commands()   
        
        self.hold_until_complete(current_reaction) #Gets reaction datapoint to feed into analyzer
        self.reactions.append(current_reaction)
        results[result_index] = [self.final_time, self.final_yield, self.reactions[-1]]



    
    def EDBO_add_data(self, time, profit):
        """Add final reaction time and yield(profit) to the planner"""
        self.reaction_scope.loc[0, 'yield'] = profit
        self.reaction_scope.loc[0, 'time'] = time


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
        

