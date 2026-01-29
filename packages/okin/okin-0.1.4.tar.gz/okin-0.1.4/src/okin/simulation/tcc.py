import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time
import os
import logging
import json
from math import log10 as log
import shutil

from okin.simulation.simulator import Simulator
from okin.base.reaction import TEReaction
from okin.base.chem_plot_utils import apply_acs_layout
from okin.base.chem_logger import chem_logger
chem_logger.setLevel(level=logging.INFO)

def timing_wrapper(func):
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        # print(f"Function '{func.__name__}' ran in {elapsed_time:.4f} seconds.")
        return result
    return wrapper

# TimeCourseCreator
class TimeCourseCreator():
    def __init__(self, mechanisms, min_yield=0.5, noise_pct=0.03, noise_type="realistic", trailing_points=3):
        self.NON_LIMITING_CHEMS = {"P", "cat", "time", "L", "L*", "cat1", "cat2", "cat3", "catI", "cat4"}
    
        self.MIN_YIELD = min_yield

        self.NOISE_PCT = noise_pct
        self.NOISE_TYPE = noise_type
        self.TRAILING_POINTS = trailing_points # nr of points added to the end from the point of convergence
        
        # dont change unless you are sure what they do
        self.NR_CONV_POINTS = 3 # nr of data points for 'P' that need to show minimal rate
        self.CONV_TOLERANCE = 0.01 # 0.01 = 1% deviation between the last <self.NR_CONV_POINTS> counts as converged.

        if isinstance(mechanisms, list):
            mechanisms = {"default_M": mechanisms}

        for mechanism_name, reactions in mechanisms.items():
            mechanisms[mechanism_name] = self.convert_reactions(reactions)

        self.mechanisms = mechanisms
    
    def _custom_round(self, val):

        if pd.isna(val) or val == 0:
            return val  # or you could return a default value, e.g., 0
        val = float(val)

        try:
            rounding_digit = abs (2 - int(log(val)))
        except:
            rounding_digit = 10
        rounding_digit += 1

        if val >= 100:
            rounding_digit = 0
            
        if val < 1e-3:
            val = 0
        
        return round(val, rounding_digit)
    
    def get_random_k_values(self, num_k_values):
        ## version 1
        # lower_bound, upper_bound = 1e-5, 1e5
        # random_k_values = np.random.uniform(lower_bound, upper_bound, num_k_values)
        # rounded_k_values = np.round(random_k_values, 3)


        # version 2
        random_k_values = np.random.uniform(0, 1, num_k_values)
        random_k_factors = np.random.choice([1e-2, 1e-1, 1e0, 1e1, 1e2, 1e3, 1e4], num_k_values)
        rounded_k_values = np.round(random_k_values * random_k_factors, 4)

        return self.create_k_dict(rounded_k_values)
        
    def get_random_c_values(self, num_c_values):
        # Set the lower and upper bounds for concentration
        lower_bound, upper_bound = 0.05, 1.0
        
        # Generate the first concentration value
        first_c_value = round(np.random.uniform(lower_bound, upper_bound), 3)
        
        # Generate random c_factors for all but the first concentration value
        # all conc should be 1/3 or 3* as large as the original conc
        c_factors = np.random.uniform(0.333, 3, num_c_values - 1)

        # factors close enough to the original value are equal. noone runs 1.23 mmol vs 1.25 mmol.
        c_factors[(c_factors >= 0.95) & (c_factors <= 1.05)] = 1
        
        # Calculate the subsequent concentration values
        c_values = np.empty(num_c_values)
        c_values[0] = first_c_value
        for i in range(1, num_c_values):
            c_values[i] = round(c_values[i - 1] * c_factors[i - 1], 3)
        
        # Generate the catalysis concentration
        lower_cat_bound, upper_cat_bound = 0.01, 0.1 # 1 - 10 mol %
        cat_factor = np.random.uniform(lower_cat_bound, upper_cat_bound)
        cat_conc = float(round(np.min(c_values) * cat_factor, 3))
        
        return c_values.tolist(), cat_conc

    def get_used_reagents(self, reactions):
        # returns all reagents that are not cat or product
        total_sm = []
        for rct in reactions:
            for chem in (rct.educts + rct.products):
                if "cat" not in chem.label and "P" not in chem.label:
                    total_sm.append(str(chem))
        used_sm = sorted(list(set(total_sm)))
        return used_sm

    def convert_reactions(self, reactions):
        # print(reactions)
        reactions = [TEReaction(reaction_string=rct, id_=i+1) for i, rct in enumerate(reactions)]
        return reactions

    def apply_noise(self, df):
        df_noisy = df.loc[:, ~df.columns.isin(['time', 'cat'])].copy()

        if self.NOISE_TYPE == "gauss":
            # 99.7 % of values fall into the 3 standard deviation from the mean
            std = self.NOISE_PCT / 3 # this makes 99.7% of all values inside the noise boundries of +- noise_pct
            # Generate Gaussian noise
            noise_factor = np.random.normal(1, std, size=df_noisy.shape)
            df_noisy *= noise_factor

        elif self.NOISE_TYPE == "uniform":
            lower_bound = 1 - self.NOISE_PCT
            upper_bound = 1 + self.NOISE_PCT

            noise_factor = np.random.uniform(lower_bound, upper_bound, size=df_noisy.shape)
            df_noisy *= noise_factor

        # this is horrible but i dont have time to make it pretty
        elif self.NOISE_TYPE == "realistic":
            # uniform
            lower_bound = 1 - self.NOISE_PCT
            upper_bound = 1 + (self.NOISE_PCT/4) # unlikely to measure more than you have. 4 is magic number

            noise_factor = np.random.uniform(lower_bound, upper_bound, size=df_noisy.shape)
            df_noisy *= noise_factor


            # gauss
            # 99.7 % of values fall into the 3 standard deviation from the mean
            std = self.NOISE_PCT / 3 # this makes 99.7% of all values inside the noise boundries of +- noise_pct
            # Generate Gaussian noise
            noise_factor = np.random.normal(1, std, size=df_noisy.shape)

            df_noisy *= noise_factor
            


        # df_noisy.iloc[0] = df.iloc[0] # dont apply noise to starting values.
        df_noisy["time"] = df["time"].copy() 
        df_noisy["cat"] = df["cat"]
        return df_noisy

    def find_end_time(self, c_dict, m, k_dict, return_df=False, t_stop_guess=None, sb_string=None, conv_thresh=0.005):
        #* setup variables for endpoint determination simulation
        num_data_points = 50

        # Find the limiting reagent, ignoring the specified keys
        
        limiting_reagent = min((c for c in c_dict if c not in self.NON_LIMITING_CHEMS), key=lambda c: c_dict[c])
        
        sim = Simulator() # new simulator obj that is used for this end time determination
        error_tuple = (None, None, None) # returned when no convergence can be found
        if t_stop_guess:
            t_stop = t_stop_guess
        else:
            t_stop = 1 # max time is = 2**20
        i = 0

        while True:
            i += 1

            # if no product after 8 iterations: error
            if i > 8 and sim.result["P"].max() <= 0:
                return error_tuple
                
            # if no convergence after 20 iterations: error
            if i > 20:
                return error_tuple
            
            print(f"\n____________{i = }, {t_stop = }_____________")
            
            sim.setup(reactions=m, k_dict=k_dict, c_dict=c_dict)


            sim.simulate(0, t_stop, num_data_points, use_const_cat=False, selections=list(c_dict.keys()) + ["time"], sb_string=sb_string)


            if sim.result["P"].max() <= 0:
                continue

            # check for convergance
            norm_result = self.normalize_for_limiting_reagent(sim.result, limiting_reagent=limiting_reagent)
            is_converged, conv_index, nr_conv_points = self.check_convergence(norm_result["P"], conv_thresh=conv_thresh)
            yield_ = round(norm_result["P"].max(), 2)

            if is_converged:
                true_t_stop = self._custom_round(norm_result["time"].iloc[conv_index])
                
                if yield_ < self.MIN_YIELD and i == 1:
                    print("ERROR tuple")
                    return error_tuple
                
                if return_df:
                    
                    sim.setup(reactions=m, k_dict=k_dict, c_dict=c_dict)


                    sim.simulate(0, t_stop, num_data_points, use_const_cat=False, selections=list(c_dict.keys()) + ["time"], sb_string=sb_string)


                    final_df = self.apply_noise(sim.result.copy())
                    
                    # plt.scatter(final_df["time"], final_df["P"])
                    # plt.axvline(x=true_t_stop)
                    # plt.show()
                    return final_df, limiting_reagent, true_t_stop, yield_
                
                else:
                    return limiting_reagent, true_t_stop, yield_

            else:
                # double t_stop until its converged
                t_stop *= 2

    def create_dataset(self, num_reactions_per_mechanism, concs_dict, save_folder=None, show=False, nr_data_points_bounds=(15, 40)):
        # conc_dict_example = { 1: {"A_conc: 1.0"}, # first dict cant have _factor values since there is no base value yet. 
        #                                           # The first dict sets the base values. If not defined they will be chosen at random
        #                       2: {"A_conc: 1.0", "B_fact": {'lower_bound':0.333333, 'upper_bound':0.75} } factor is applied to the base values
        # }

        info_dict = {} # track all info to recreate the data set
        info_dict["noise_pct"] = self.NOISE_PCT
        info_dict["noise_type"] = self.NOISE_TYPE
        
        start_time = time.perf_counter()
        if save_folder:
            os.makedirs(save_folder, exist_ok=True)

        for m_name, m in self.mechanisms.items():
            info_dict["mechanism"] = [str(rct).split(": ")[1] for rct in m]
            num_accepted_rcts = 0
            csv_paths = [] # list of all created csv_paths

            base_c_dict = None

            while num_accepted_rcts < num_reactions_per_mechanism:
                # print(f"_____________________________{num_accepted_rcts = }_________________________")

                #* get random values for concentration for all species that are NOT catalyst or Product    
                used_sm = self.get_used_reagents(m)

                #* get random values for k_values for all reactions
                k_dict = self.get_random_k_values(num_k_values=len(m))
                info_dict["k_dict"] = k_dict

                # create path to folder <mechanism_name>/<reaction>/<len(concs_dict).csv>
                rct_num = 0
                mech_path = f"{save_folder}/{m_name}/rct_{rct_num}"
                while os.path.exists(mech_path):
                    rct_num += 1
                    mech_path = f"{save_folder}/{m_name}/rct_{rct_num}"
                os.makedirs(mech_path)

                # needs a random c_dict to start out with
                c_list, cat_conc = self.get_random_c_values(len(used_sm))
                c_dict = {species:c for species, c in zip(used_sm, c_list)}
                
                c_dict["cat"] = cat_conc
                c_dict["P"] = 0
                
                for i in range(1, len(concs_dict)+1):
                    #* check for updates via concs_dict

                    # c_instructions
                    c_instr_dict = concs_dict[i] # keys start at 1, 2, 3, etc.

                    # all random
                    if not c_instr_dict:
                        # print("getting random vals from no c_instr_dict")
                        c_list, cat_conc = self.get_random_c_values(len(used_sm))
                        c_dict = {species:c for species, c in zip(used_sm, c_list)}
                        
                        c_dict["cat"] = cat_conc
                        c_dict["P"] = 0

                    # update all concentrations for this experiment
                    if i != 1:
                        c_dict = base_c_dict.copy()

                    for s_str, val in c_instr_dict.items():
                        # print(f"getting vals from {c_instr_dict = }")
                        # species_string
                        species, info = s_str.split("_")

                        if species not in c_dict.keys():
                            print(f"WARNING\n{species = } is not in the c_dict. maybe in a later mechanism so I wont throw an error.")
                            continue

                        if info == "conc":
                            # parse _conc
                            #  _conc uses the exact value. 
                            new_conc = val
                            
                        elif info == "fact": # factor
                            if i == 1:
                                raise IndexError("Cant use fact for the first conditions. there is no value to multiply.")
                            # parse _fact
                            # _fact picks a random value between the the lower and upper bound and uses that as a factor on the base value
                            if isinstance(val, dict):
                                used_fact = np.random.uniform(val["lower_bound"], val["upper_bound"])
                                new_conc = base_c_dict[species] * used_fact
                            elif isinstance(val, tuple):
                                # I keep forgetting to make it a dict so now tuples work.
                                used_fact = np.random.uniform(val[0], val[1])
                                new_conc = base_c_dict[species] * used_fact

                            else: # assume its a number and not a dict
                                new_conc = base_c_dict[species] * val
                        
                        c_dict[species] = new_conc  

                    info_dict[f"c_dict_{i}"] = c_dict

                    #* save base dict for working mechanism with at least 50% yield
                    if i == 1:
                        base_c_dict = c_dict.copy()
                        

                    print(f"{i} : {c_dict = }")

                    # returns stop time if there is one
                    limiting_reagent, true_t_stop, yield_ = self.find_end_time(m=m, c_dict=c_dict, k_dict=k_dict)

                    #! on the first iteration make sure that the standard conditions work. 
                    #! Everything after doesnt have to converge.
                    #! You might want to try reactions that fail intentionally.
                    if not true_t_stop and i == 1:
                        num_accepted_rcts -= 1
                        shutil.rmtree(mech_path)
                        print(f"removed {f'{save_folder}/{m_name}'}")
                        break
                    
                    if not true_t_stop and i > 1:
                        true_t_stop = 2**20
                    
                    num_data_points = int(np.random.uniform(low=nr_data_points_bounds[0], high=nr_data_points_bounds[1]))

                    sim = Simulator()
                    sim.setup(reactions=m, k_dict=k_dict, c_dict=c_dict)
                    sim.sb_string
                    sim.simulate(0, true_t_stop, num_data_points, use_const_cat=False, selections=["time"] + list(c_dict.keys()))

                    info_dict[f"num_data_points_{i}"] = num_data_points
                    info_dict[f"true_t_stop_{i}"] = true_t_stop

                    final_df = self.apply_noise(sim.result.copy())
                    final_df = final_df.map(self._custom_round)
                    final_df["cat"] = None
                    final_df.loc[0, "cat"] = c_dict["cat"]

                    if show:
                        plt.plot(final_df["time"], final_df["P"])
                        # plt.plot(final_df["time"], final_df["A"])
                        plt.scatter(final_df["time"], final_df["P"], label=f"P_{i}")
                        # plt.scatter(final_df["time"], final_df["A"], label=f"A_{i}")
                        
                        # plt.title(f"yield: {yield_*100}, {limiting_reagent}_0 = {c_dict[limiting_reagent]}")
                        # plt.show()
                        
                    if save_folder and len(final_df) > 1:
                        csv_num = 0
                        csv_path = f"{mech_path}/exp_{csv_num}.csv"

                        while os.path.exists(csv_path):
                            csv_num += 1
                            csv_path = f"{mech_path}/exp_{csv_num}.csv"

                        print(f"{csv_path = }\n")
                        final_df.to_csv(csv_path, index=False)  
                        csv_paths.append(csv_path)
                    
                    else:
                        print(f"!!!REMOVED {mech_path = }")
                        os.removedirs(mech_path)

                if show:
                    plt.legend()
                    apply_acs_layout()
                    plt.xlabel("time")
                    plt.ylabel("conc")
                    plt.show()

                num_accepted_rcts += 1 # not required for this version where only the first rct has to be accepted, but I'll keep it for now.

                #* save info
                info_dict_path = os.path.join(mech_path, "info_dict.json")
                try:
                    with open(info_dict_path, "w") as file:
                        json.dump(info_dict, file, indent=4)
                except FileNotFoundError:
                    pass

                #* save sb_string
                sb_string_path = os.path.join(mech_path, "sb_string.txt")
                try:
                    with open(sb_string_path, "w") as file:
                        file.write(sim.sb_string)
                except FileNotFoundError:
                    pass

        print(f"Done in {time.perf_counter() - start_time} s")
        return csv_paths, k_dict

    def normalize_for_limiting_reagent(self, df, limiting_reagent):
        max_value = df[limiting_reagent].max()
    	
        norm_df = pd.DataFrame()
        for c in df.columns:
            if c == "time":
                continue
            norm_df[c] = df[c] / max_value

        norm_df["time"] = df["time"].copy()
        return norm_df

    def check_convergence(self, p_series, conv_thresh=0.005):
        # Calculate the differences between consecutive product values in the pd.Series
        diffs = p_series.diff().abs()
        # dd = diffs.diff()

        diffs = diffs / diffs.max()
        # dd = dd / dd.max()
        
        last_d_avg = abs(diffs.tail(self.NR_CONV_POINTS).mean())
        converged = last_d_avg < conv_thresh
        conv_p_val = p_series.iloc[-1] * 0.995 # 1% of max P value
        conv_index = (p_series - conv_p_val).abs().idxmin() + self.TRAILING_POINTS

       
        if converged:
            conv_p_val = p_series.iloc[-1] * 0.95 # 5% of max P value
            conv_index = (p_series - conv_p_val).abs().idxmin() + self.TRAILING_POINTS
            nr_conv_points = len(p_series) - conv_index
            return converged, conv_index, nr_conv_points

        return (None, None, None)

    def create_k_dict(self, k_values):
        num_values = len(k_values)
        k_dict = {}
        
        for i in range(num_values):
            key_k = f"k{i+1}"
            key_kN = f"kN{i+1}"
            random_kN_factor = np.random.uniform(0.8, 20)
            k_dict[key_k] = k_values[i]
            k_dict[key_kN] = np.round(k_values[i] / random_kN_factor, 3)

        return k_dict

if __name__ == "__main__":
    # ending in n = normal, cd = continuous deactivation, pd = product deactivation, sd = starting material deactivation

    mechanisms = {
        # "M1_n": [   "A + cat -> cat1",
        #             "cat1 + -> P + cat"
        #         ],
        # "M1_cd": ["A + cat -> cat1", "cat1 -> P + cat", "cat -> catI"],
        # "M1_pd": ["A + cat -> cat1", "cat1 -> P + cat", "cat + P-> catI"],
        # "M1_sd": ["A + cat -> cat1", "cat1 -> P + cat", "cat + A -> catI"],

        "M2_n": ["A + cat -> cat1", "cat1 + B -> P + cat"],
        "M2_cd": ["A + cat -> cat1", "cat1 + B -> P + cat", "cat -> catI"],
        "M2_pd": ["A + cat -> cat1", "cat1 + B -> P + cat", "cat + P-> catI"],
        "M2_sd": ["A + cat -> cat1", "cat1 + B -> P + cat", "cat + A -> catI"],
        
        # "M3_n":  ["A + A -> C", "C + cat -> cat1", "cat1 -> P + cat"],
        # "M3_cd": ["A + A -> C", "C + cat -> cat1", "cat1 -> P + cat", "cat -> catI"],
        # "M3_pd": ["A + A -> C", "C + cat -> cat1", "cat1 -> P + cat", "cat + P -> catI"],
        # "M3_sd": ["A + A -> C", "C + cat -> cat1", "cat1 -> P + cat", "cat + A -> catI"],
        }
    
    
    # mechanism_name:
    #   - reaction:
    #          — experiment
    
    fake_reactor = TimeCourseCreator(mechanisms=mechanisms, min_yield=0.5, noise_pct=0.01, noise_type="realistic", trailing_points=3)

    concs_mod_dict = {  
                        1: {"A_conc": 0.1, "B_conc": 0.12, "cat_conc":0.003},                               
                        2: {"cat_fact": 0.7},
                        3: {"A_fact": 0.66, "B_fact": 0.66, "cat_fact": 0.7},
                        # 4: {"B_fact": {'lower_bound':1.5, 'upper_bound':1.5}}
                        # 4: {"A_fact": (0.2, 3.0)}
            }

    fake_reactor.create_dataset(num_reactions_per_mechanism=1, concs_dict=concs_mod_dict, save_folder="test", show=False, nr_data_points_bounds=(40,40))



