import sys
import json
from Devices.DeviceClass import Devices
from  Devices.device_commands import command_controller
from Devices.DeviceTransport.transport_methods import NodeTree
from ExperimentClass.Experiment import Experiment
from threading import Thread
from ExperimentClass.Planners.EDBO import EDBOplus

#import multiprocessing
#from multiprocessing import Process
#from multiprocessing import Lock
#from multiprocessing import Queue
import os
import shutil

#If enabled, system will NOT load any hardware or execute any commands and will skip to data analysis
global DATA_DEBUG
DATA_DEBUG = False


#All script loading occurs in campaign class
class Campaign:
    def __init__(self):
        """Campaign class is the stem of the system.  Main function is to read the initial setup files and pass information
        to Experiment classes and device class.  If there is an issue with campaign setup, its probably here
        """

        self.settings = json.load(open("./CampaignSetup/settings.json"))
        self.settings["DATA_DEBUG"] = DATA_DEBUG
        self.components = json.load(open("./CampaignSetup/components.json"))
        print(self.components)
        self.node_tree  = NodeTree(components=self.components)

        self.Devices = Devices(self.settings, self.components)

        self.Experiments = []

        self.load_experiments()
        self.create_save_directory()

    def _parse_script_text(self, text):
        """
        Takes in a text and returns a dictionary splitting the text
        by line and appending the first word as the command and rest of the string
        as list of arguments
        """

        commands = []
        command_arguments = []
        text = text.split('\n')
        #Cheacking for experiment properties; if not a property add it to the list of commands
        #TODO currently MUST! have an experiment vial declared
        for line in text:
            parsed = line.split(" ", 1)
            if parsed[0] == "EXPERIMENT_SOLUTION_REFERENCE":
                experiment_offset_solution = json.load(open("./CampaignSetup/solution_references.json"))[parsed[1]]
                print(experiment_offset_solution)
                #input()
            else:
                commands.append(parsed[0])
                command_arguments.append(parsed[1].split())                

        
        return(commands, command_arguments, experiment_offset_solution)
    
    def load_experiments(self):
        """Load Each script file from the experimets folder to an index"""
        for index , filename in enumerate(os.listdir("./CampaignSetup/Experiments")):
            new_experiment = Experiment(devices=self.Devices)
            new_experiment.experiment_name = filename
            

            experiment_setup = json.load(open(f"./CampaignSetup/Experiments/{filename}"))

            new_experiment.number_of_reactions = experiment_setup["max_number_of_reactions"]
            new_experiment.reaction_scope = EDBOplus().generate_reaction_scope(
                                components=experiment_setup["reaction_components"], 
                                filename=f"{filename}.csv",
                                check_overwrite=False
                            )
            new_experiment.EDBO_settings = experiment_setup["planner_setup"]
            new_experiment.syringe = experiment_setup["syringe"]
            new_experiment.campaign_name = experiment_setup["campaign_name"]
            self.Experiments.append(new_experiment)
    def create_save_directory(self):
        """Creates the folders for saving each experiments data seperately, added to experiment dictionaries for their own reference"""

        self.settings["directories"] = {}
        self.settings["directories"]["save_data"] ="./save_data/" 
        root = self.settings["directories"]["save_data"]


        #Create subfolders for each experiment, save path to experiment dict. for NMR scans later
        for exp in self.Experiments:
            name = exp.experiment_name
            campaign_name = exp.campaign_name
            exp_folder = root + f"/{campaign_name}"+ f"/{name}"
            os.makedirs(exp_folder, exist_ok=True)
            exp.experiment_folder = exp_folder



    def start(self):
        """Start the experiments; wait for them all to complete
        Convert experiment dict to objects, start all experiment.start() as threads, each experiment needs to run data to devices and have a key"""
        experiment_threads = []
        for exp in self.Experiments:
            print ("starting exp")
            
            t = Thread(target=exp.start_experiment)
            t.start()
            experiment_threads.append(t)
            


if __name__ ==  '__main__':
    core = Campaign()
    core.start()
    print("done :D")




