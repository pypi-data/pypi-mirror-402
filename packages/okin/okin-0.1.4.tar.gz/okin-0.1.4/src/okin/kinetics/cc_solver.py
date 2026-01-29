import numpy as np
import pandas as pd
from okin.base.chem_logger import chem_logger
from okin.base.chem_plot_utils import apply_acs_layout
from okin.simulation.simulator import Simulator
import matplotlib.pyplot as plt
from okin.kinetics.vtna import ClassicVTNA
from scipy.integrate import cumulative_trapezoid
from scipy.interpolate import interp1d
from scipy.optimize import minimize
from scipy.optimize import minimize_scalar
import sys
from math import e
from scipy.optimize import differential_evolution
from scipy.optimize import curve_fit

# cat_total = sum( all cat species that are in the cycle)
# cat_calc = predicted sum( all cat species that are in the cycle)
# cat = general cat e.g. cat1_t0 is starting [cat] of df1



class CCSolver():
    def __init__(self, mech):
        self.mech = mech
        df1 = pd.read_csv(f"M1_{mech}/rct1_{mech}.csv")
        df2 = pd.read_csv(f"M1_{mech}/rct2_{mech}.csv")
        self._set_data(df1, df2)

    def _set_data(self, df1, df2, progres_species="P", time_name="time"):
            
            df1 = df1.rename(columns={progres_species: "P", time_name: "time"})
            df2 = df2.rename(columns={progres_species: "P", time_name: "time"})

            df1 = df1[["time", "P", "cat"]]
            df2 = df2[["time", "P", "cat"]]

            # set const cat
            cat1_t0 = df1["cat"].iloc[0]
            cat2_t0 = df2["cat"].iloc[0]
            df1["cat"] = cat1_t0
            df2["cat"] = cat2_t0

            # df1, df2 = self._fill_missing_Ps(df1=df1, df2=df2)
            df1, df2 = self._normalize(df1=df1, df2=df2)
            df1, df2 = self._cut_off(df1=df1, df2=df2, species="P")

            self.visualize_dfs(df1=df1, df2=df2, species=["P"])

            df1.to_csv("used_df1.csv", index=False)
            df2.to_csv("used_df2.csv", index=False)

    def _fill_missing_Ps(self, df1: pd.DataFrame, df2: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
            # Get the union of all P values
            all_Ps = sorted(set(df1["P"]).union(set(df2["P"])))

            # Build interpolators: P → time
            interp1 = interp1d(df1["P"], df1["time"], bounds_error=False, fill_value=np.nan)
            interp2 = interp1d(df2["P"], df2["time"], bounds_error=False, fill_value=np.nan)

            # Interpolate times for the full P set
            times1 = interp1(all_Ps)
            times2 = interp2(all_Ps)

            # Create new dataframes with shared P grid
            filled_df1 = pd.DataFrame({"time": times1, "P": all_Ps}).dropna().sort_values("time").reset_index(drop=True)
            filled_df2 = pd.DataFrame({"time": times2, "P": all_Ps}).dropna().sort_values("time").reset_index(drop=True)

            return filled_df1, filled_df2

    def _normalize(self, df1, df2, species="all"):
        if species == "all":
                # #! normalize
            combined_max = pd.concat([df1, df2]).max()

            # Step 2: Normalize both DataFrames using the combined max
            df1 = df1 / combined_max
            df2 = df2 / combined_max
        
        else:
            # normalize only this species
            # Compute the max value for the specified species across both DataFrames
            max_val = max(df1[species].max(), df2[species].max())

            # Normalize only the specified species column
            df1[species] = df1[species] / max_val
            df2[species] = df2[species] / max_val
        
        return df1, df2
        
    def _cut_off(self, df1, df2, species):
         # Step 1: Get the max value of "P" in each DataFrame
        max_p1 = df1["P"].max()
        max_p2 = df2["P"].max()

        # Step 2: Take the smaller of the two
        cutoff = min(max_p1, max_p2)

        # Step 3: Keep only rows where P <= cutoff
        df1 = df1[df1["P"] <= cutoff].reset_index(drop=True)
        df2 = df2[df2["P"] <= cutoff].reset_index(drop=True)
        return df1, df2

    def sigmoidal_decay(self, x, k=1, x0=0):
        """
        Sigmoidal decay function that starts near 1 and approaches 0.5.
        
        Parameters:
        - x : array-like or float
        - k : steepness of the decay (positive value)
        - x0: midpoint of the decay

        Returns:
        - y : value(s) of the function
        """
        return 0.5 + 0.5 / (1 + np.exp(k * (x - x0)))

    def polynomial(self, x, coeffs):
        """
        Evaluate a polynomial at x using given coefficients.
        Coefficients should be in descending powers.
        """
        return np.polyval(coeffs, x)

    def get_fit(self, func_type="sig"):
        df1 = pd.read_csv("used_df1.csv")
        df2 = pd.read_csv("used_df2.csv")

        b1 = df1["cat"].iloc[0]
        b2 = df2["cat"].iloc[0]
        
        self.df1 = df1.copy()
        self.df2 = df2.copy()

        #* 
        if func_type == "sig":
            self.func = self.sigmoidal_decay
            bounds = [(-0.1, 0.1)]  +  [(b2, b2), (0, 2), (0, 2)]

        #* 
        if func_type == "poly":
            poly_degree = 5
            self.func = self.polynomial
            bounds = [(-0.1, 0.1)] * poly_degree + [(b2, b2), (0, 2), (0, 2)]

        # Now optimizing only 10 parameters (5 for each poly)
        result = differential_evolution(
            self.get_error,
            bounds=bounds,
            strategy='best1bin',
            maxiter=1000,
            popsize=25,
            tol=1e-6,
            mutation=(0.5, 1),
            recombination=0.7,
            polish=True,
            seed=2,
            disp=True  # Optional: shows progress
        )

        if not result.success:
            print("Optimization failed:", result.message)
            sys.exit()

        # Reconstruct final polynomials
        opt_params = list(result.x)
        coeffs = opt_params[:-2]
        x, y = opt_params[-2:]

        df2["cat_total"] = self.func(df2["time"], coeffs=coeffs)
        df1["cat_total"] = df2["cat_total"] * y
        df1[""]
    
        c_vtna = ClassicVTNA(self.df1, self.df2, species_col_name="cat_calc", product_col_name="P", time_col_name="time", auto_evaluate=False)
        plt.title("VTNA using 5th-order polynomial with fixed intercept")

        _, _, err = c_vtna.get_specific_order_axes(order=1, show=True)

        return self.df1, self.df2

    def get_error(self, params):
        
        vars_ = params[:-2]
        x_stretch, y_strech = params[-2:]

        b1 = df1_orig["cat"].iloc[0]
        b2 = df2_orig["cat"].iloc[0]

        df1 = df1_orig.copy()
        df2 = df2_orig.copy()

        # df1["cat_calc"] = A1 * (1-m1)**df1["time"]
        # df2["cat_calc"] = A2 * (1-m2)**df1["time"]
        df1["cat_calc"] = A1 * np.exp(-m1 * df1["time"])
        df2["cat_calc"] = A2 * np.exp(-m2 * df2["time"])



        # Penalize negative or values exceeding initial cat values
        if (df1["cat_calc"] < 0).any() or (df1["cat_calc"] > b1).any():
            return 1e6
        if (df2["cat_calc"] < 0).any() or (df2["cat_calc"] > b2).any():
            return 1e6


        c_vtna = ClassicVTNA(
            df1, df2,
            species_col_name="cat_calc",
            product_col_name="P",
            time_col_name="time",
            auto_evaluate=False
        )
        _, _, err = c_vtna.get_specific_order_axes(order=1, show=False)

        print(f"err={err}, params={params}")
        return np.log1p(abs(1 - err))
    
    def visualize_dfs(self, df1, df2, species: list):
        for s in species:
            plt.scatter(df1["time"], df1[s], label=f"{s}1")
            plt.scatter(df2["time"], df2[s], label=f"{s}2")
        
        apply_acs_layout()
        plt.xlabel("time")
        plt.ylabel("conc")
        plt.legend()
        plt.show()

    def show_real_overlap(self, cat1, cat2):
        df1 = pd.read_csv("filled_df1.csv")
        df2 = pd.read_csv("filled_df2.csv")

        real_df1 = pd.read_csv(f"M1_{self.mech}/rct1_{self.mech}_real.csv")
        real_df2 = pd.read_csv(f"M1_{self.mech}/rct2_{self.mech}_real.csv")

        combined_max = pd.concat([real_df1, real_df2]).max()

        # Step 2: Normalize both DataFrames using the combined max
        real_df1 = real_df1 / combined_max
        real_df2 = real_df2 / combined_max

        plt.scatter(real_df1["time"], real_df1["cat_total"], label="real_1")
        plt.scatter(real_df2["time"], real_df2["cat_total"], label="real_2")

        # Optional fix: align lengths
        min_len1 = min(len(df1["time"]), len(cat1))
        min_len2 = min(len(df2["time"]), len(cat2))

        # Plot only overlapping ranges
        plt.scatter(df1["time"].iloc[:min_len1], cat1[:min_len1], label="calc_1")
        plt.scatter(df2["time"].iloc[:min_len2], cat2[:min_len2], label="calc_2")

        # plt.title(f"Fitting calc [cat] | err = 0.9300419071151931")
        apply_acs_layout()
        plt.legend()
        plt.tight_layout()
        plt.show()

    def run_solver(self, order=1):
        # cat1, cat2 = self.vtna_approach(order=order)
        # cat1, cat2 = self.solve_cat_from_integral()

        # cat1, cat2 = self.linear_approx_gridsearch()
        # cat1, cat2 = self.linear_approx()
        # cat1, cat2 = self.poly_approx()
        cat1, cat2 = self.exp_decay_approx()
        # cat1, cat2 = self.gauss_decay_approx()
        # cat1, cat2 = self.logistic_decay_approx()
        
        # print(type(cat1))
        self.show_real_overlap(cat1=cat1, cat2=cat2)
        # self.true_exp()
        # self.true_gauss()
        # self.true_linear()


if __name__ == "__main__":
    x = CCSolver(mech="pd")
    # x.run_solver()