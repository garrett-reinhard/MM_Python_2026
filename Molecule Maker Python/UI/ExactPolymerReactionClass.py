class ExactPolymerReactionPlan:
    def __init__(self, polymer_length: int=1):
        self.DesiredPolymerLength = polymer_length

        ### Action Planning ###
        self.SolidSupportedPolymer: bool = False
        self.OrthogonallyProtectedMonomer: bool = False
        self.MonomerRemovalSolidSupported: bool = False
        self.ActivatorSolidSupported: bool = False
        self.EndCapped: bool = False


        ### Component Selection ###

        self.MonomerSolution:str = "None"
        self.CouplingReactionComponent:str = "None"
        self.ExcessMonomerWash:str = "None"
        self.ActivatorComponent:str = "None"
        self.ExcessActivatorWash:str = "None"
        self.CleavingComponent:str = "None"
        self.EndCapComponent:str = "None"
        self.MonomerAbsorberVial:str = "None"
        self.ActivatorVial: str = "None"