
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
        self.reagents = []
        """list of all reagents in this reaction"""

        self.reagent_volumes = []
        """list of all Volume of each reagent in reaction"""

        self.current_vial=""
   
        self.hotplate = ""
        """Hotplate this reaction took place on"""
        self.syringe = ""
        """Syringe this reaction utilized"""


