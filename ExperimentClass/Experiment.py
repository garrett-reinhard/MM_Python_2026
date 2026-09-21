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
from ExperimentClass.ReactionRunner import ReactionRunner
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
        self.reagent_volume = float
        """Volume of reagent in reaction"""
        self.solvent_volume = float
        """Volume of solvent in reaction"""        
        self.hotplate = ""
        """Hotplate this reaction took place on"""
        self.syringe = ""
        """Syringe this reaction utilized"""




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




    def start_experiment(self):
        self.key = threading.Lock()
        self.key.acquire()

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

            #Prep all experiments to run
            for a in range(batch_size):
                next_reaction: Reaction = Reaction()
                next_reaction.syringe = self.syringe
                #determine next temperature and vial
                next_reaction.solvent = self.reaction_scope.loc[a, 'solvent'] 
                next_reaction.reagent = self.reaction_scope.loc[a, 'reagent'] 
                next_reaction.solvent_volume = self.reaction_scope.loc[a, 'solvent_volume']
                next_reaction.reagent_volume = self.reaction_scope.loc[a, 'reagent_volume']
                
                next_reaction.save_folder = f"{self.experiment_folder}/{next_reaction.next_reagent}_{next_reaction.next_reagent_volume}_{next_reaction.next_solvent}_{next_reaction.next_solvent_volume}"
                next_temperature = self.reaction_scope.loc[a, 'temperature']
                self.set_vial(next_temperature, next_reaction)


                sub_experiment = ReactionRunner(self, self.Devices) #TODO Fix this dependency on deepcopy to avoid device issues
                reaction_threads.append(threading.Thread(target=sub_experiment.start_reaction, args=(next_reaction, reaction_results, current_reaction_number)))
                current_reaction_number +=1

            #Start all reactions in batch
            for a in reaction_threads:
                a.start()

            #Hold for all reactions in batch to complete
            for i in range(len(reaction_threads)):
                reaction_threads[i].join()

            #Pull results
            for idx, result in enumerate(reaction_results):
                if not result:
                    input("error Ef: No data returned from a threaded experiment Perhaps Check: \n 1) Too many reactions for batch size\n 2) data save destination errors")
                final_time = result[0] 
                final_yield = result[1]
                self.reactions.append(result[2])
                
                self.reaction_scope.loc[idx, 'yield'] = final_yield
                self.reaction_scope.loc[idx, 'time'] = final_time
            self.reaction_scope.to_csv(self.campaign_csv)



    
    def EDBO_add_data(self, time, profit):
        """Add final reaction time and yield(profit) to the planner"""
        self.reaction_scope.loc[0, 'yield'] = profit
        self.reaction_scope.loc[0, 'time'] = time




        
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




