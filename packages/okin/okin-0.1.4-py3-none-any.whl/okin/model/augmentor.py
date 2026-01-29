from okin.base.reaction import TEReaction
from okin.kinetics.vtna import ClassicVTNA
import glob, os, sys
import pandas as pd
from okin.base.chem_logger import chem_logger

"""
This class should never use k-values. These go to the Model class.
"""


class MechanismAugmentor():
    def __init__(self, mechanism: list, data_path: str, naming_dict: dict):
        self.logger = chem_logger.getChild(self.__class__.__name__)

        self.naming_dict = naming_dict # {"real_name": "standard_name"}

        self.mechanisms = {} # {<id:int>: {"mechansim": <mechansim>, "reason": <reason:str>}}
        self.std_m = self.standardize_mechanism(mechanism) # std_m = standard_mechanism

        if not os.path.exists(data_path):
            raise NameError(f"{os.path.abspath(data_path)} does not exist. It should contain the currently obtained data.")
        
        self.data_path = data_path

    def standardize_mechanism(self, mechanism):
        self.logger.info(f"Real mechanism =\n{mechanism}")

        for real_name, std_name in self.naming_dict.items():
            mechanism = [str(rct).replace(real_name, std_name) for rct in mechanism]
        std_m = [TEReaction(reaction_string=rct, id_=i+1) for i, rct in enumerate(mechanism)]
        
        self.logger.info(f"Standard mechanism =\n{std_m}")
        return std_m


    
    def add_reaction(self, rct):
        if isinstance(rct, TEReaction):
            self.mechanism.append(rct)
        elif isinstance(rct, str):
            self.mechanism.append(TEReaction(reaction_string=rct, id_=len(self.mechanism)+1))

    def del_reaction(self, rct=None, id_: int=None):
        if rct:
            self.mechanism.remove(rct)
        elif id_:
            self.mechanism.remove(self.mechanism[id_-1]) # id gets +1 during generation in TEReaction class to start at 1
        else:
            raise ValueError("Either rct or id_ must be given.")
    
    def get_new_generation(self, data_folder):
        dfs = [pd.read_csv(path) for path in glob.glob(f"{data_folder}/*.csv")]
        iteration = len(dfs) # prob not a good approach. just check what files are there




if __name__ == "__main__":

    mechanism = [
        "ArBr + Pd -> cat1",
        "cat1 + ArMgBr -> ArAr + cat"
        ]

    eval_path ="./test_eval"

    naming_dict = {"ArBr": "A", "ArMgBr": "B", "Pd": "cat", "ArAr": "P"}

    x = MechanismAugmentor(mechanism=mechanism, data_path=eval_path, naming_dict=naming_dict)
