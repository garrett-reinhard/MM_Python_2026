class ExactPolymerReactionPlan:
    def __init__(self, polymer_length: int=1):
        
        ### Action Planning ###
        SolidSupportedPolymer: bool = False
        OrthogonallyProtectedMonomer: bool = False
        MonomerRemovalSolidSupported: bool = False
        ActivatorSolidSupported: bool = False
        EndCapped: bool = False


        ### Component Selection ###

        MonomerSolution:str = "None"
        CouplingReactionComponent:str = "None"
        ExcessMonomerWash:str = "None"
        ActivatorComponent:str = "None"
        ExcessActivatorWash:str = "None"
        CleavingComponent:str = "None"
        EndCapComponent:str = "None"
        MonomerAbsorberVial:str = "None"
        ActivatorVial: str = "None"