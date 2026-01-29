from okin.base.reaction import TEReaction
from okin.cd_parser.cd_parser import CDParser
from okin.base.chem_logger import chem_logger
from okin.simulation.simulator import Simulator
from okin.base.chem_plot_utils import apply_acs_layout
from okin.simulation.tcc import TimeCourseCreator
from math import log10 as log

import os, glob, json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from itertools import product

#TODO _____________ What should happen when create model is called __________
#TODO (1) Give dfs. model that.

#TODO (2) Give dfs. model that. Try other user defined mechanisms (add/del steps). User defined steps will always be tried first.

#TODO (3) Give dfs. model that. Suggest new mechanistic steps (basic stuff cat deact etc.) maybe fit a function to get basic behavior…

#TODO (4) Give 2 dfs. model that. Suggest new mechanistic steps. Simulate them. 
#TODO      Calculate the deviation between simulated data of the new mechanism vs simulated data of the initial guess mechanism.
#TODO      The one with the biggest difference gives the most new information (I just assume that for now).

#TODO (5)


class Modler():
    """
    self.df_dict is a list of dfs. each df represents one experiment and has to contain the same headers.
    self.copasi_settings is one large dict with all default values used in COPASI modeling. It is loaded and written as a JSON!
    self.parameters is a dict(dict) with keys being the parameters to be optimized {"k1": {"bounds": (lower_bound, upper_bound), "definition": kN2*5, "best_guess": value}}

    self.current_mechanism is an updated mechanism that is going to be modeled next.
    self.current_results is a dict of all parameters that are to be optimized together with their final optimization value.
    self.current_error is the error of the current mechanistic guess after optimizing / modeling.

    self.steps_to_try is a list of reaction strings. tries the addition of these steps as FIFO. If empty a new guess will be generated.
    self.steps_to_del is a list of reaction strings. If the str matches  tries the deletion of these steps as FIFO. If empty a new guess will be generated.

    self.history is a list(dict) of all previously modeled mechanisms [{"mechanism": self.current_mechanism, "results": self.current_results}, "error": self.current_error]
    """

    def __init__(self, copasi_path):
        self.logger = chem_logger.getChild(self.__class__.__name__)
        self.COPASI_PATH = copasi_path

        self.to_plot = None
        
        # COPASI setup
        self.copasi_settings = self._get_copasi_settings()
        self.parameters = {}
        self.k_boundaries = {}
        self.df_dict = {}
        self.fixed_k_dict = {}

        # Basic mechanism setup
        self.current_mechanism = None
        self.current_results = {}
        self.current_error = None
        
        # modifying the mechanism
        self.steps_to_try = []
        self.steps_to_del = []

        # tracking the mechanism
        self.history = {}

        self.manual_sb_edit = False

        self.max_mse_c_values = None

        self.create_paths()
        self.simulator = Simulator()

    def create_paths(self):
        # current_folder = f"{os.path.dirname(os.path.abspath(__file__))}" # this is nuts.
        # self.COPASI_PATH = f"{current_folder}\\local_copasi"
        self.COPASI_BASE_PATH = os.path.join(self.COPASI_PATH, "temp")
        self.COPASI_INPUT_PATH = os.path.join(self.COPASI_BASE_PATH, "input")
        self.COPASI_OUTPUT_PATH = os.path.join(self.COPASI_BASE_PATH, "kopt", "Fit1", "results", "curr_run") # copasi demands this structure
        self.COPASI_DEFAULT_PATH = os.path.join(self.COPASI_PATH, "default")

    #*___________________________________________________________________________________________________________________
    #*                                        **helper functions**

    def _get_copasi_settings(self):
        copasi_settings = {
            "problem": "kopt",
            "results_directory": "curr_run",
            "report_name": "k_values",
            "method": "genetic_algorithm",
            "weight_method": "mean_squared",
            "randomize_start_values": True,
            "number_of_generations": "10",
            "population_size": "10",
            "tolerance": 1e-05,
            "copy_number": 3,
            "pe_number": 10,
            "run_mode": "parallel",
            "calculate_statistics": False,
            "config_filename": "config.yml",
            "context": "s",
            "cooling_factor": 0.85,
            "create_parameter_sets": False,
            "cross_validation_depth": 1,
            "fit": 1,
            "iteration_limit": 50,
            "lower_bound": 1e-06,
            "number_of_iterations": 100000,
            "overwrite_config_file": False,
            "pf": 0.475,
            "pl_lower_bound": 1000,
            "pl_upper_bound": 1000,
            "prefix": None,
            "quantity_type": "concentration",
            "random_number_generator": 1,
            "rho": 0.2,
            "save": False,
            "scale": 10,
            "seed": 0,
            "start_temperature": 1,
            "start_value": 0.1,
            "std_deviation": 1e-06,
            "swarm_size": 50,
            "update_model": False,
            "upper_bound": 1000000,
            "use_config_start_values": False,
            "validation_threshold": 5,
            "validation_weight": 1
        }
        return copasi_settings
    
    def _clear_copasi_inputs(self):
        files = glob.glob(f"{self.COPASI_INPUT_PATH}/*.csv")
        for f in files:
            os.remove(f)

        files = glob.glob(f"{self.COPASI_INPUT_PATH}/*.txt")
        for f in files:
            if not f.endswith("user_settings.txt"):
                os.remove(f)

    def _create_copasi_csvs(self):
        for path, df in self.df_dict.items():
            name = os.path.basename(path)

            time_col = [c for c in df.columns if c.lower().startswith("time")][0]

            try:
                df = df.rename(columns={time_col: 'time'})
            except:
                pass

            df = df.reset_index(drop=True)
            df = df.set_index("time")
            new_path = os.path.join(self.COPASI_INPUT_PATH, name)

            # create the _indep column to signal COPASI the starting concentration for that species FROM THE CSV FILE
            for species in df.columns:
                # create starting conc for species in CSV
                if species.lower().startswith("unnamed") or species.lower().startswith("time"):
                    continue
    
                starting_conc = df[species].iloc[0]
                col_name = species + "_indep"
                df[col_name] = None  # Initialize the new column with None (or NaN)

                # Set the value for the first row in the new column
                df.loc[0, col_name] = starting_conc

            # delete all time course values that should not be used for to match
            for col in df.columns:
                if col == "time" or col.endswith("_indep"):
                    continue
                if col not in self.to_match:
                    # Set all values except the first one to ""
                    df.iloc[1:, df.columns.get_loc(col)] = None

            # self.logger.info(f"Created csv at {new_path=}")
        
            # remove [] from headers 
            df.columns = [col.replace('[', '').replace(']', '') for col in df.columns]

            df.to_csv(new_path)

    def _create_copasi_inputs(self):
        
        # populate k_dict. use pre fix given values with $
        k_dict = {}
        for i in range(1, len(self.current_mechanism)+1):        
            for k_name in [f"k{i}", f"kN{i}"]:
                if k_name in self.fixed_k_dict.keys():
                    k_dict[k_name] = f"${self.fixed_k_dict[k_name]}"
                else:
                    k_dict[k_name] = str(np.random.randint(low=0, high=10e4))

        fit_item_path = os.path.join(self.COPASI_INPUT_PATH, "fit_items.txt")
        # fitting items, fitting_items

        # k_to_fit = {k_name: {} for k_name in k_dict.keys() if "$" not in k_dict[k_name]}
        k_to_fit = [k_name for k_name in k_dict.keys() if "$" not in k_dict[k_name]]

        # for k,d in self.k_boundaries.items():
        #     if k in k_to_fit.keys():
        #         k_to_fit[k] = d

        #     else:
        #         raise IndexError(f"{k = } was given boundaries but is not to be fitted.")
        
        self.logger.info(f"{k_to_fit=}")

        with open(fit_item_path, "w") as fif:
            fif.write(str(k_to_fit))

        # sb string setup
        sb_string = self.simulator._get_antimony_str(reactions=self.current_mechanism, k_dict=k_dict, c_dict={})
        sb_string_path = os.path.join(self.COPASI_INPUT_PATH, "sb_string.txt")


        with open(sb_string_path, "w") as sbf:
            # print(f"COPASI from Sb string:\n{self.sb_string}")
            sbf.write(sb_string)

        
    def _write_copasi_settings(self):
        curr_settings_path = os.path.join(self.COPASI_INPUT_PATH, "user_settings.txt")
        # self.logger.info(f"Settings file = {curr_settings_path}")



        with open(curr_settings_path, "w") as f:
            json.dump(self.copasi_settings, f, indent=4)
            # f.write(str(self.copasi_settings))
        

    def _start_copasi(self):
        #! version for calling second environment
        python_exe_path = os.path.join(self.COPASI_PATH, "copasi_env", "python.exe")
        python_file_path = os.path.join(self.COPASI_PATH, "optimize_k.py")
        cmd = f"{python_exe_path} {python_file_path}"
        print(f"\n\n{cmd = }\n")
        os.system(cmd)

    def _custom_round(self, val):
        return val
        if pd.isna(val):
            return val  # or you could return a default value, e.g., 0
        val = float(val)

        rounding_digit = abs (2 - int(log(val)))

        if val < 1e-3:
            val = 0
        
        return round(val, rounding_digit)

    def _read_results(self):
        print(f"{self.COPASI_OUTPUT_PATH = }")
        paths_to_ks = glob.glob(self.COPASI_OUTPUT_PATH + "\*.txt")
        
        dfs = []
        for path_to_ks  in paths_to_ks:
            temp_df = pd.read_csv(path_to_ks, sep="\t")
            dfs.append(temp_df)
        
        df = pd.concat(dfs, ignore_index=True).sort_values(by='RSS', ascending=True)
        df['RSS_scaled'] = df['RSS'] / df['RSS'].min()
        
        # Apply rounding function every column ~EXCEPT RSS~ to make it more readable 1850.382942394 vs 1850
        df[df.columns.difference(['RSS'])] = df[df.columns.difference(['RSS'])].map(self._custom_round)

        return df

    def _custom_error(self, true_df, sim_df):
        pass

    #*___________________________________________________________________________________________________________________
    #*                                        **SETUP User functions**
    def set_species_for_model(self, species):
        self.model_species = species

    def set_models(self, models):
        
        self.models = {}

        for name, m in models.items():
            rcts = [TEReaction(reaction_string=rct, id_=i+1) for i, rct in enumerate(m["reactions"])]
            self.models[name] = {"reactions": rcts, "k_dict": m["k_dict"]}

        self.logger.info("Set models to:")
        for name, m in self.models.items():
            self.logger.info(f"{name}: {m}")

    def set_m_reactions(self, mechanism=None, cdxml_path=None):
        # m = mechanism. but its no k values so m_reactions
        assert bool(mechanism) ^ bool(cdxml_path), "Give either reaction list or chemdraw path"

        if mechanism:
            self.current_mechanism = [TEReaction(reaction_string=rct, id_=i+1) for i, rct in enumerate(mechanism)]
        
        elif cdxml_path:
            cd_parser = CDParser(cdxml_path, draw=False)
            self.current_mechanism = cd_parser.find_reactions(draw=False)
        
        self.logger.info(f"Set current mechanstic guess to:\n{self.current_mechanism}")


    def add_experiment_csv(self, csv_paths, show=False):

        if isinstance(csv_paths, list):
            for csv_path in csv_paths:
                new_df = pd.read_csv(csv_path)

                # check if all dfs have the same columns
                if self.df_dict:
                    reference_df = list(self.df_dict.values())[0]                    
                    assert set(reference_df.columns) == set(new_df.columns), f"All csv_files need the same column names. Here\n{reference_df.columns}\n!=\n{new_df.columns}"

                self.df_dict[csv_path] = new_df
        else:
            new_df = pd.read_csv(csv_paths)

            # check if all dfs have the same columns
            if self.df_dict:
                reference_df = list(self.df_dict.values())[0]
                assert reference_df.columns.equals(new_df.columns), f"All csv_files need the same column names. Here\n{reference_df.columns}\n!=\n{new_df.columns}"
            self.df_dict[csv_paths] = new_df
        
        if show:
            for i, df in enumerate(self.df_dict.values()):
                plt.scatter(df["time"], df["P"])
                plt.plot(df["time"], df["P"], label=f"P_{i}")
                plt.scatter(df["time"], df["A"])
                plt.plot(df["time"], df["A"], label=f"A_{i}")
                plt.legend()
                apply_acs_layout()

            plt.show()

        self.logger.info(f"New {len(self.df_dict) = }")

    def set_copasi_settings(self, new_settings):
        """
        Update COPASI settings.
        """
        # print(new_settings)
        for k,v in new_settings.items():
            if k not in self.copasi_settings.keys():
                raise ValueError(f"{k} is not a valid key. Only valid keys are: {self.copasi_settings.keys()}")
            self.copasi_settings[k] = v

    def set_fixed_k_values(self, fixed_k_dict):
        self.fixed_k_dict = fixed_k_dict

    def set_k_boundaries(self, k_boundaries):
        """
        dict(
        k1 = {"lower_bound": 0, "upper_bound":100},
        kN1 = {"lower_bound": 0, "upper_bound":100},
        )
        """
        self.k_boundaries = k_boundaries
    
    def set_species_to_plot(self, species: list):
        self.to_plot = [s.replace("[", "").replace("]", "") for s in species]


    def set_species_to_match(self, species):
        """
        The to_match species have to be consistent across all files, so it stays a class variable and is never passed as an argument.
        """
        self.to_match = [s.replace("[", "").replace("]", "") for s in species]

        if not self.to_plot:
            self.set_species_to_plot(species=self.to_match)

    def add_reaction(self, rct):
        pass

    def del_reaction(self, rct):
        pass
    
    def set_manual_sb_edit(self, manual_sb_edit):
        self.manual_sb_edit = bool(manual_sb_edit)

    #*___________________________________________________________________________________________________________________
    #*                                        **MODELING User functions**

    def create_models(self, mechanism_dict, result_py_path):
        #TODO this needs a threshhold on how much RSS (other errors) have to be better before accepting a new reaction
        #TODO something like RSS_1 * (num_rct_m1*self.NOISE_PCT) < RSS_2 * (num_rct_m2*self.NOISE_PCT)

        #TODO Also check if reactions are "forward enough". If not set the values to 0 and see if that makes the RSS worse or the same.

        """
        mechanism is list(str) or list(TEReaction)
        dfs = list(pd.Dataframe)
        """

        # check self.to_match has columns available
        for species in self.to_match:
            for _, df in self.df_dict.items():
                if species not in df.columns:
                    raise IndexError(f"{species = } is used to optimize but not in the Data = {df.columns}.")
        
        #TODO check if all species to match exist in all mechanisms
        

        result_dict = {}
        for name, m in mechanism_dict.items():
            result_dict[name] = {}

            self.set_m_reactions(m)
            self._clear_copasi_inputs()
            self._write_copasi_settings()
            self._create_copasi_csvs()
            self._create_copasi_inputs()

            if self.manual_sb_edit:
                input("Edit now and then hit any key.")
            self._start_copasi()

            #! _______________modeling is over_________________
            mod_res_df = self._read_results()
            best = mod_res_df.iloc[0].to_dict()
            
            # add fixed k-values back in
            for k,v in self.fixed_k_dict.items():
                # not sure if this would ever happen… better save than sorry.
                if k in best.keys():
                    raise IndexError(f"{k} was set fixed but was optimized. Double check.")
                best[k] = v
            
            k_dict = {k:v for k,v in best.items() if k.startswith("k")}

            
            result_dict[name]["best_k_dict"] = k_dict
            result_dict[name]["RSS"] = best["RSS"]
            print(result_dict)

        # it is what it is 
        with open(result_py_path, "+a") as f:
            f.write("""import glob, os
import pandas as pd
from chem_sim.simulator import Simulator
import matplotlib.pyplot as plt
from chem_utils.chem_plot_utils import apply_acs_layout\n\n""")

            f.write("mechanisms = ")
            json.dump(mechanism_dict, f, indent=4)
            f.write("\n")
            f.write("results = ")
            json.dump(result_dict, f, indent=4)

            f.write("""
csvs = glob.glob(os.path.abspath('./data/*.csv'))
species_to_show = ["P"]

sim = Simulator()
                    
for name, m in mechanisms.items():
    best_k_dict = results[name]["best_k_dict"]

    for csv in csvs:
        csv_name = csv.split("\\\\")[-1]
        df = pd.read_csv(csv)

        c_dict = df.loc[0]
        print(c_dict)

        sim.setup(reactions=m, k_dict=best_k_dict, c_dict=c_dict) 

        stop_time = df["time"].iloc[-1] 
        sim.simulate(stop=stop_time, times=df["time"], selections=species_to_show)

        r = sim.result

        for s in species_to_show:
            plt.scatter(df["time"], df[s], label=csv_name, s=35)
            plt.plot(r["time"], r[s], linestyle=":", marker="*", markersize=5)


            apply_acs_layout()
            # plt.title(f"{name} - {csv_name}")
            plt.title(f"{name}")
            plt.legend()
            plt.xlabel("time")
            plt.ylabel("conc")
    plt.show() # one tab = all traces at once. Two tabs = each trace individually
    """)









            # self.show_model_fit()
            
            # #* get true data
            # first_file_path = list(self.df_dict.keys())[0]
            # self.logger.info(f"{first_file_path = }")
            # true_df = pd.read_csv(first_file_path)

            # #* get modeled/simulated data 
            # c_dict = {c:true_df[c].iloc[0].tolist() for c in true_df.columns}
            # self.simulator.setup(reactions=self.current_mechanism, k_dict=k_dict, c_dict=c_dict)
            # self.simulator.simulate(times=true_df["time"].tolist())
            # sim_df = self.simulator.result

    def create_single_model(self):
        """
        mechanism is list(str) or list(TEReaction)
        dfs = list(pd.Dataframe)
        """
        
        # check self.to_match has columns available
        for species in self.to_match:
            for _, df in self.df_dict.items():
                if species not in df.columns:
                    raise IndexError(f"{species = } is used to optimize but not in the Data = {df.columns}.")

        self._clear_copasi_inputs()
        self._write_copasi_settings()
        self._create_copasi_csvs()
        self._create_copasi_inputs()


        if self.manual_sb_edit:
            input("Edit now and then hit any key.")

        self._start_copasi()

    def get_current_model_results(self, file_index=0):
        mod_res_df = self._read_results()
        best = mod_res_df.iloc[0].to_dict()
        
        for k,v in self.fixed_k_dict.items():
            # not sure if this would ever happen… better save than sorry.
            if k in best.keys():
                raise IndexError(f"{k} was set fixed but was optimized. Double check.")
            
            best[k] = v

        k_dict = {k:v for k,v in best.items() if k.startswith("k")}

        # get true data
        first_file_path = list(self.df_dict.keys())[file_index]
        self.logger.info(f"{first_file_path = }")
        true_df = pd.read_csv(first_file_path)

        # get modeled/simulated data 
        c_dict = {c:true_df[c].iloc[0].tolist() for c in true_df.columns}

        return k_dict, c_dict, true_df

    def show_model_fit(self, show_all=False, save_modeled_data=False):
        k_dict, c_dict, true_df = self.get_current_model_results()
        # print(f"{k_dict = }\n{c_dict = }\n{true_df = }")

        
        
        # self._custom_error(true_df, sim_df)

        if show_all:
            for i in range(len(self.df_dict)):
                csv_path = list(self.df_dict.keys())[i]
                csv_name = csv_path.split("\\")[-1]

                k_dict, c_dict, true_df = self.get_current_model_results(file_index=i)

                for s in self.to_plot:
                    self.simulator.setup(reactions=self.current_mechanism, k_dict=k_dict, c_dict=c_dict)
                    self.simulator.simulate(times=true_df["time"].tolist())
                    sim_df = self.simulator.result
                    plt.scatter(true_df["time"], true_df[s], label=f"True {s}")
                    plt.plot(sim_df["time"], sim_df[s], linestyle=":", marker="*", markersize=5, label=f"Model {s}")

                if save_modeled_data:
                    new_csv_name = f"{csv_path[:-4]}_modeled.csv"
                    sim_df.to_csv(new_csv_name, index=False)
                    self.logger.info(f"Saved file to {new_csv_name}")

                plt.title(csv_name)
                apply_acs_layout()
                plt.show()

                
        else:
            csv_path = list(self.df_dict.keys())[0] # always first file
            csv_name = csv_path.split("\\")[-1]

            for s in self.to_plot:
                self.simulator.setup(reactions=self.current_mechanism, k_dict=k_dict, c_dict=c_dict)
                self.simulator.simulate(times=true_df["time"].tolist())
                sim_df = self.simulator.result
                plt.scatter(true_df["time"], true_df[s], label=f"True {s}")
                plt.plot(sim_df["time"], sim_df[s], linestyle=":", marker="*", markersize=5, label=f"Model {s}")
            
            if save_modeled_data:
                new_csv_name = f"{csv_path[:-4]}_modeled.csv"
                sim_df.to_csv(new_csv_name, index=False)
                self.logger.info(f"Saved file to {new_csv_name}")
            apply_acs_layout()
            plt.show()



        
        
    
    def find_next_best_experiment(self, initial_c_dict:dict, bounds:list, method:str ="optimization", grid_sizes:dict = None):
        # bounds: list[tuple]
        self.c_dict_species = list(initial_c_dict.keys())
        c_dict_vals = list(initial_c_dict.values())

        if "P" not in self.c_dict_species:
            self.c_dict_species.append("P")
            c_dict_vals.append(0.0)
            bounds["P"] = (0, 0)

        self.logs = {}
        self.i = 0
        self.new_conditions = {"c_dict": None, "error": 1}
        # Minimize the negative of the function to maximize it

        if method == "optimization":
            # Get the bounds in the correct order based on your initial values
            param_order = list(initial_c_dict.keys())  # or ['A', 'B', 'cat', 'P'] if you know the order
            bounds_list = [bounds[param] for param in param_order]

            result = minimize(
                lambda x: self.get_model_mse(x), 
                c_dict_vals, 
                bounds=bounds_list, 
                method='Powell', 
                options={}  # Set max iterations here
            )
            optimal_values = result.x
        
        if method == "grid":
            # dict_bounds = {name: bound for name, bound in zip(self.c_dict_species, bounds)} #{"A": (0.1, 1), "B": (0.1, 1), …}
            optimal_values = self.grid_search(bounds, grid_sizes)
        # best_c_dict = {}
        # for name, conc in zip(self.c_dict_species, optimal_values):
        #     best_c_dict[name] = conc

        plt.title(f"{self.new_conditions['c_dict']}")
        self.display_models(self.new_conditions["c_dict"])
        max_value = result.fun  # Since we minimized the negative, negate the result

        with open("max_mse.json", "w") as f:
            json.dump(self.max_mse_c_values, f, indent=4)

        return optimal_values, max_value

    def grid_search(self, dict_bounds, grid_sizes):
        species_names = list(grid_sizes.keys())
        grid_ranges = {species: np.round(np.arange(dict_bounds[species][0], dict_bounds[species][1], grid_sizes[species]), 3) for species in species_names}
        all_combinations = list(product(*grid_ranges.values()))

        import time

        start = time.perf_counter()
        i = 0
        for combination in all_combinations:
            i += 1
            self.logger.info(f"{i}/{len(all_combinations)}") # i/729

            self.get_model_mse(c_dict_vals=combination)
            # c_dict = {species: conc for species, conc in zip(species_names, combination)}
            # df, limiting_reagent, true_t_stop, yield_ = tcc.find_end_time(m=rcts, c_dict=c_dict, k_dict=k_dict, return_df=True, t_stop=128)

        self.logger.info(f"\n________________\nIt took {time.perf_counter() - start} seconds\n________________________")
        # import sys
        # sys.exit()
      
    def get_model_mse(self, c_dict_vals):
        c_dict = {species: round(conc,3) for species, conc in zip(self.c_dict_species, c_dict_vals)}

        if "P" not in c_dict.keys():
            c_dict["P"] = 0.0

        dfs = []
        # times = []
        names = []
        tcc = TimeCourseCreator(mechanisms=[], noise_pct=0.05, noise_type=None)
        # Initialize a dictionary to store column comparisons
        column_comparisons = {species_name: [] for species_name in self.model_species}
        for name, model in self.models.items():
            names.append(name)
            k_dict = model["k_dict"]
            rcts = model["reactions"]

            df, limiting_reagent, true_t_stop, yield_ = tcc.find_end_time(m=rcts, c_dict=c_dict, k_dict=k_dict, return_df=True)
            # Find the largest starting value (max of the first row)
            max_start_value = df.iloc[0].max()

            # Normalize the entire DataFrame
            df_normalized = df / max_start_value
            dfs.append(df_normalized)
            
                                          
            
        #     plt.scatter(df["time"], df["P"])
        #     times.append(df["time"])
        # apply_acs_layout()
        # plt.show()

        if not self.max_mse_c_values:
            self.max_mse_c_values = {}  # To store c_values for the max MSE

        # Compare columns for each species
        for species_name in self.model_species:
            mse_values = []
            
            # For each pair of DataFrames, compare the values of the same species column
            for i in range(len(dfs)):
                for j in range(i + 1, len(dfs)):
                    name1 = names[i]
                    name2 = names[j]
                    df1 = dfs[i]
                    df2 = dfs[j]

                    key = f"{name1} vs {name2} ({species_name})"
                    if key not in self.max_mse_c_values.keys():
                        self.max_mse_c_values[key] = {"c_dict": None, "mse": -1}
                        
                    # Ensure the species column exists in both DataFrames
                    if species_name in df1.columns and species_name in df2.columns:
                        # Compare the columns for similarity
                        col1 = df1[species_name]
                        col2 = df2[species_name]

                        #TODO this assumes that the time column is synced
                        mse = abs(np.mean((col1.values - col2.values) ** 2))  # Multiply by 1000 for better scaling
                        mse_values.append(mse)
                        
                        # Track the maximum MSE and the corresponding c_dict
                        
                        if self.max_mse_c_values[key]["mse"] < mse:

                            # self.logger.info(f"updated {key = }... {mse = }\n {self.max_mse_c_values}")
                            self.max_mse_c_values[key] = {"c_dict": c_dict, "mse": mse}

                        column_comparisons[species_name].append({
                            "comparison": f"{name1} vs {name2}",
                            "mse": mse
                        })

        # Print the results
        error = -sum(mse_values) * 100
        if error < self.new_conditions["error"]:
            print(f"New BEST of {error} with {c_dict = }")
            self.new_conditions = {"c_dict": c_dict, "error": error}
        self.logger.info(f"Calculated {error = }; {c_dict = }")
        
        # self.display_models(c_dict)
        self.logs[self.i] = {"c_dict": c_dict, "mse": error}
        self.logs = dict(sorted(self.logs.items(), key=lambda item: item[1]['mse']))
        with open("results.json", "w") as f:
            json.dump(self.logs, f, indent=4)

        self.i += 1

        return error
    
    def display_models(self, c_dict):        
        sim = Simulator()
        for name, model in self.models.items():
            k_dict = model["k_dict"]
            rcts = model["reactions"]
            sim.setup(reactions=rcts, c_dict=c_dict, k_dict=k_dict)
            sim.simulate(0, 300, 40, use_const_cat=False, selections=["time", "A", "P"])
            sim_df = sim.result
            plt.plot(sim_df["time"], sim_df["P"], linestyle=":", marker="*", markersize=4, label=f"{name} (simulated)")
        # plt.scatter(data["time"], data["P"], label="True Data", color="black")
        plt.ylabel("[P]")
        plt.xlabel("time")
        plt.xlabel("time")
        plt.ylabel("[P]")
        plt.legend()
        apply_acs_layout()
        plt.show()



if __name__ == "__main__":
    def make_fake_data():
        from okin.simulation.tcc import TimeCourseCreator
        
        mechanisms = {
        "M1_n": ["A + cat -> cat1", "cat1 -> P + cat"],
        # "M1_cd": ["A + cat -> cat1", "cat1 -> P + cat", "cat -> catI"],
        # "M1_pd": ["A + cat -> cat1", "cat1 -> P + cat", "cat + P-> catI"],
        # "M1_sd": ["A + cat -> cat1", "cat1 -> P + cat", "cat + A -> catI"],

        # "M2_n": ["A + cat -> cat1", "cat1 + B -> P + cat"],
        # "M2_cd": ["A + cat -> cat1", "cat1 + B -> P + cat", "cat -> catI"],
        # "M2_pd": ["A + cat -> cat1", "cat1 + B -> P + cat", "cat + P-> catI"],
        # "M2_sd": ["A + cat -> cat1", "cat1 + B -> P + cat", "cat + A -> catI"],
        
        # "M3_n":  ["A + A -> C", "C + cat -> cat1", "cat1 -> P + cat"],
        # "M3_cd": ["A + A -> C", "C + cat -> cat1", "cat1 -> P + cat", "cat -> catI"],
        # "M3_pd": ["A + A -> C", "C + cat -> cat1", "cat1 -> P + cat", "cat + P -> catI"],
        # "M3_sd": ["A + A -> C", "C + cat -> cat1", "cat1 -> P + cat", "cat + A -> catI"],
            }

        # mechanism_name:
        #   - reaction:
        #          — experiment
        #
        
        fake_reactor = TimeCourseCreator(mechanisms=mechanisms, min_yield=0.5, noise_pct=0.03, noise_type="gauss", trailing_points=3)
        concs_mod_dict = {  1: {"A_conc": 1.0},                               
                            2: {"cat_fact": 1.5},
                            3: {"B_fact": 1.5},
                            # 4: {"B_fact": {'lower_bound':1.5, 'upper_bound':1.5}}
                            4: {"A_fact": (0.2, 3.0)},
                            5: {}
                }

        fake_reactor.create_dataset(num_reactions_per_mechanism=1, concs_dict=concs_mod_dict, save_folder="test", show=False, nr_data_points_bounds=(15, 40))

    # _______________________________________________________________________________________

    # m = Modler(copasi_path=r"D:\python_code\hein_modules\local_copasi")


    # rcts = [
    #     "A + cat -> cat1",
    #     "cat1 + B -> P + cat",
    #     "P + cat -> cat2"
    #     ]

    print("Modeling:\n______________________________")
    # local_copasi_path = r"D:\python_code\hein_modules\py_copasi"
    local_copasi_path = r"D:\python_code\hein_modules\testing_stuff\py_copasi"
    modler = Modler(copasi_path=local_copasi_path)

    my_mechanism_guess = [ 
        "A + cat -> cat + P",
        ] 

    modler.set_m_reactions(mechanism=my_mechanism_guess)
    modler.add_experiment_csv(csv_paths=[r"D:\python_code\hein_modules\simulated_test_csvs\data1.csv", r"D:\python_code\hein_modules\simulated_test_csvs\data2.csv"])
    modler.set_species_for_model(species=["P", "A"])
    modler.set_species_to_match(species=["P", "A"])
    modler.set_copasi_settings(new_settings={"number_of_generations":50, "population_size": 50})
    modler.create_single_model()
    modler.show_model_fit(save_modeled_data=True, show_all=True)


    # m = Modler()
    # mechanisms = {
    # "M1":
    #     {
    #     "A + cat -> cat1": {"k1":0.3, "kN1":0.05},
    #     "cat1 + B -> P + cat": {"k2":100, "kN2":0},
    #     "A + cat -> catI": {"k3":0.05, "kN3":0}
    #     },

    # "M2":
    #     {
    #     "A + cat -> cat1": {"k1":0.3, "kN1":0.05},
    #     "cat1 + B -> P + cat": {"k2":100, "kN2":0},
    #     "P + cat -> catI": {"k3":0.05, "kN3":0}
    #     },
    # "M3":
    #     {
    #     "A + cat -> cat1": {"k1":0.3, "kN1":0.05},
    #     "cat1 + B -> P + cat": {"k2":100, "kN2":0},
    #     "cat -> catI": {"k3":0.05, "kN3":0}
    #     }
    # }

    # # from modeling the mechansims wtih the data
    # k_dict_M1 = {'k1': 0.67282, 'kN1': 0.000232981, 'k2': 0.273698, 'k3': 0.0978742, 'kN3': 1e-05, 'kN2': 0}
    # k_dict_M2 = {'k1': 1.04382, 'kN1': 0.000789731, 'k2': 0.135528, 'k3': 0.211901, 'kN3': 6.94133e-05, 'kN2': 0}
    # k_dict_M3 = {'k1': 975.566, 'kN1': 1.87212e-05, 'k2': 0.128818, 'k3': 43.2637, 'kN3': 1.55055e-05, 'kN2': 0}

    # models = {
    #     "M1": {"reactions": list(mechanisms["M1"].keys()), "k_dict": k_dict_M1},
    #     "M2": {"reactions": list(mechanisms["M2"].keys()), "k_dict": k_dict_M2},
    #     "M3": {"reactions": list(mechanisms["M3"].keys()), "k_dict": k_dict_M3},
    # }


    # m.set_models(models=models)
    # m.set_species_for_model(species=["P", "A"])

    # c_dict = {"A": 0.5, "B": 0.8, "cat": 0.05, "P": 0.0}

    # bounds = {"A": (0.3, 1.01), "B": (0.3, 1.01), "cat": (0.01, 0.101), "P": (0.0, 1.01)}

    # m.find_next_best_experiment(initial_c_dict=c_dict, bounds=bounds, method="optimization", grid_sizes={"A": 0.1, "B": 0.1, "cat": 0.01, "P": 0.1})
    # m.display_models(c_dict={"A": 1.0, "B": 0.8, "cat": 0.05, "P":0})

    # 477.17 seconds for 729 ~= 0.65 seconds per iteration
    # results [A] = 0.9, [B] = 0.9, [cat] = 0.01

    #* 
    # my_csvs = glob.glob(os.path.abspath('./test/*_10.csv'))
    # for c in my_csvs:
    #     df = pd.read_csv(c)
    #     non_time_cols = [col for col in df.columns if col != "time"]
    #     for ntc in non_time_cols:
    #         df[ntc] *= 10

    #     name = f"{c[:-4]}_10.csv"
    #     print(name)
    #     df.to_csv(name, index=False)
    

    
    # have species that cant be measured to be otpimized within a given +- % value No. thats stupid.
    # REAL PATH C:\Users\Finn\Python\modeling\local_copasi\temp\input\user_settings.txt

    # LOOKING FOR: c:\Users\Finn\Python\modeling\src\chem_model\local_copasi\temp\input\user_settings.txt

# {'B': {'best_k_dict': {'k1': 48.1, 'kN1': 0.0016, 'k2': 408.0, 'kN2': 0.0, 'k3': 0.3, 'kN3': 0.19}, 'RSS': 0.0869301}}
# {
#     'A': {'best_k_dict': {'k1': 52.2, 'kN1': 0.0, 'k2': 545.0, 'kN2': 130.0}, 'RSS': 0.115026}, 
#     'B': {'best_k_dict': {'k1': 48.9, 'kN1': 0.0018, 'k2': 420.0, 'kN2': 2.29, 'k3': 0.38, 'kN3': 0.18}, 'RSS': 0.0762956}}