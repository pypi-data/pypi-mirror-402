# from distutils.log import error
import sys

# from reactions import 
from okin.base.reaction import TEReaction
import tellurium as te
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
from okin.base.chem_logger import chem_logger
# Simulator uses a list of TEReactions

class Simulator():
    def __init__(self):
        self.logger = chem_logger.getChild(self.__class__.__name__)
        self.invalid_arrow_dict = {"Equilibrium": "<=>", "HalfHead": "<==>", "line": "--"}

    def unify_arrows(self, reactions):
        for i in range(len(reactions)):
            rct = reactions[i]
            if rct.drawn_arrow in self.invalid_arrow_dict.values():
                reactions[i].drawn_arrow = "->" # the one and only for Sb strings
        return reactions

    def setup(self, reactions, k_dict, c_dict):

        if isinstance(reactions[0], str):
            reactions = [TEReaction(reaction_string=rct, id_=i+1) for i, rct in enumerate(reactions)]

        if not isinstance(reactions[0], TEReaction):
             raise TypeError(f"reactions need to by type {type(TEReaction)} but are type {type(reactions[0])}.")

        reactions = self.unify_arrows(reactions)
        self.sb_string = self._get_antimony_str(reactions=reactions, c_dict=c_dict, k_dict=k_dict)

    
    def simulate(self, start=None, stop=None, nr_time_points=None, use_const_cat=False,  sb_string=None, times=None, selections=None):
        if sb_string:
            r = te.loada(sb_string)
        else:
            r = te.loada(self.sb_string)

        if selections is not None:
            selections = list(set(list(selections) + ["time"]))

        if times is not None:
            rr_res = r.simulate(times=times, selections=selections)
        else:
            rr_res = r.simulate(start, stop, nr_time_points, selections=selections)

        result = self.convert_to_pd_df(rr_res)

        if use_const_cat:
            result["cat"] = [result["cat"][0]]*len(result["cat"])

        self.result = result

    def convert_to_pd_df(self, rr_result):
        df = pd.DataFrame(rr_result)
        # to make it compatible with GUI
        header = [x.replace("[", "").replace("]", "") for x in rr_result.colnames]
        df.columns = header
        return df

    def _get_total_used_chems(self, reactions):
        total_chems = []
        for rct in reactions:
            for chem in (rct.educts + rct.products):
                total_chems.append(str(chem))
        return sorted(list(set(total_chems)))

    def _get_antimony_str(self, reactions, c_dict, k_dict):
        used_chems = self._get_total_used_chems(reactions)
        self.used_chems = used_chems
        r_lines = []
        for rct in reactions:
            line = ""
            line += f"{str(rct)};\t\t{rct.rate_eq}\n"
            r_lines.append(line)

        c_lines = []
        const_conc = []
        for chem in used_chems:
            if chem in c_dict.keys():
                if "$" in str(c_dict[chem]):
                    line = f"${chem} = {c_dict[chem].replace('$', '')}\n"
                    const_conc.append(chem)
                else:
                    line = f"{chem} = {c_dict[chem]}\n"
            else:
                line = f"{chem} = 0\n"

            c_lines.append(line)

        k_lines = []
        for k_name, k_value in k_dict.items():
            if "$" in str(k_value):
                line = f"${k_name} = {k_value.replace('$', '')}\n"
            else:
                line = f"{k_name} = {k_value}\n"

            k_lines.append(line)

        
        sb_string = f"{''.join([l for l in r_lines])}\n\n{''.join([l for l in c_lines])}\n\n{''.join([l for l in k_lines])}"
        # self.sb_string = sb_string
        return sb_string
    
    def apply_sb_mods(self, mod_dict):
        temp_sb_list = []
        self.logger.info(f"Applying {mod_dict}")
        for line in self.sb_string.split("\n"):
            temp_line = line
            for species, _ in mod_dict.items():
                if line.strip().startswith("J"):
                    # self.logger.debug(f"in Reaction:\n{line.strip()}\n")
                    # temp_sb_string += line.replace(species, f"${species}")
                    temp_line = line.replace(species, f"${species}")
                    # # in case it gets applied twice
                    # temp_line = temp_line.replace("$$", "$")
                    # self.logger.debug(f"in Reaction:\n{line.strip()}\n{temp_line}")
            temp_sb_list.append(temp_line)

        for species, mods in mod_dict.items():
            if mods["mod_type"] == "function":
                temp_sb_list.append(f"{species} := {mods['func']}")

        temp_sb_string = "\n".join(temp_sb_list)
        self.sb_string = temp_sb_string
        
def main():
  
    reactions = ["A+cat->cat1", "cat1+B->P + cat", "cat1 + A -> catI"]
    k_dict = {"k1":0.1, "kN1":0, "k2":0.1, "kN2":0, "k3":0, "kN3":0}

    c_dict = {"A":1.0, "cat":0.01, "B":1.2, "cat1":0}
    sim = Simulator()
    sim.setup(reactions=reactions, c_dict=c_dict, k_dict=k_dict)
    sim.simulate(0, 100, 40, use_const_cat=False, selections=["A", "P"])
    sim.result["A"] = sim.result["A"] 
    sim.result["P"] = sim.result["P"]
    
    plt.scatter(sim.result["time"], sim.result["A"], label="A")
    plt.scatter(sim.result["time"], sim.result["P"], label="P")
    plt.legend()
    plt.show()

    

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    main()
