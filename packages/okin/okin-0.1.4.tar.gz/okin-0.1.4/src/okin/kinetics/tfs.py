import numpy as np
import pandas as pd
import json
import os
import glob
import sys
import matplotlib.pyplot as plt
from okin.base.chem_plot_utils import apply_acs_layout
from okin.base.chem_plot_utils import apply_acs_layout_ax
from okin.kinetics.vtna import ClassicVTNA
from okin.kinetics.vtna import MergedVTNA

class ThreeFileSolver():
    def __init__(self, folder, show=False):
        self.prep_data(folder)

        
        # self.solve_catalyst_conc(df1=df_with_poly[0][0], df2=df_with_poly[2][0])

    def prep_data(self, folder):
        data = self.parse_files(folder)
        # print(data)
        # sys.exit()

        df5 = self.split_data(data)


        orders = self.merge_VTNA(df5)
    


        

        # print(data)
        # df_with_poly = self.fit_data(data)

    def _reset_readd(self, df5):
        reset_df5 = []
        for df in df5:
            df["P"] -= df["P"].iloc[0]
            df["time"] -= df['time'].iloc[0]

            reset_df5.append(df)
        return reset_df5

    def _normalize_df5(self, df5):
        pass

    def merge_VTNA(self, df5):  
        reset_df5 = self._reset_readd(df5)

        species_dict = {}
        for s in df5[0].columns:
            #! need to create P_real and P_rate
            if s in ["time", "cat", "cat1", "cat_true", "catI"] + ["P"]:
                continue
            if s == "P":
                guessed_order = 0
                min_order = -1
                max_order = 1
            elif s == "cat_assume":
                guessed_order = 0.84
                min_order = 0
                max_order = 2
            else:
                guessed_order = 1
                min_order = -1
                max_order = 2
            species_dict[s] = {"min_order":min_order, "max_order": max_order, "guessed_order": guessed_order, "best_order": None}

        # species_dict = {
        #         "A": {"min_order":-1, "max_order": 2, "guessed_order": 0.1, "best_order": None},
        #         "B": {"min_order":-1, "max_order": 2, "guessed_order": 1, "best_order": None},
        #         "cat": {"min_order":0, "max_order": 3.0, "guessed_order": 0.84, "best_order": None},
        #         "P": {"min_order":-2, "max_order": 2, "guessed_order": 0, "best_order": None},
        #         }
        
        
        # sys.exit()
        # self.display_df5(reset_df5)
        # sys.exit()
        # first_batch = reset_df5[:2] + reset_df5[4]
        first_batch = [reset_df5[0], reset_df5[2], reset_df5[4]]

        c_vtna = ClassicVTNA(df_rct1=reset_df5[0], df_rct2=reset_df5[2], species_col_name="cat_true", product_col_name="P", time_col_name="time")
        c_vtna.show_plot()
        sys.exit()

        a = MergedVTNA(dfs=first_batch, species_dict=species_dict, product_col_name="P", time_col_name="time", use_r2=False)
        # a.normalize_integrals(show=True)
        # sys.exit()
        # a.get_error(orders=(0.8, 0.62, 1.00))
        a.find_best_orders()
        a.normalize_integrals(show=True)

    def parse_files(self, folder):
        data_files = glob.glob(f"{folder}/*.csv")
        re_add_time_files = glob.glob(f"{folder}/*_info.txt")

        data = []
        i = -1
        for data_file, add_file in zip(data_files, re_add_time_files):
            i += 1
            df = pd.read_csv(data_file)
            
            # df.drop("cat1", inplace=True, axis=1)
            # df.drop("cat", inplace=True, axis=1)

            # df["cat_total"] = None
            df["cat_assume"] = df["cat"].iloc[0]
            df["cat_true"] = df["cat"] + df["cat1"]
            # print(df)

            with open(add_file, "r") as f:
                content = f.read()
                if content.isdigit():
                    re_add_time = int(content)
                else:
                    re_add_time = False
            
            data.append( (df, re_add_time) )

        return data
    
    def display_df5(self, df_list):
        fig, axes = plt.subplots(nrows=1, ncols=5, figsize=(20, 15), sharey=True)


        for i, (df, ax) in enumerate(zip(df_list, axes)):
            ax.scatter(df['time'], df['P'], label='P', color='tab:blue')
            ax.scatter(df['time'], df['A'], label='A', color='tab:orange')
            ax.scatter(df['time'], df['B'], label='B', color='tab:green')
            
            ax.set_title(f'Regime {i+1}')
            ax.set_xlabel('time')
            if i == 0:
                ax.set_ylabel('Value')
            apply_acs_layout_ax(ax)

        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc='upper center', ncol=3)
        fig.suptitle('P, A, B vs Time for 5 DataFrames', fontsize=16)
        fig.tight_layout(rect=[0, 0, 1, 0.95])

        
        plt.show()

        # sys.exit()


    def split_data(self, data):
        df5 = []
        for df, re_add_time in data:
            if re_add_time:
                df_before = df[df["time"] <= re_add_time].copy()
                df_after = df[df["time"] > re_add_time].copy()

                df5.append(df_before)
                df5.append(df_after)
            else:
                df5.append(df)
            
        # self.display_df5(df5)
        return df5

    def fit_data(self, data):
        new_data = []
        for df, re_add_time in data:
            if re_add_time:
                df_before, df_after = self.split_data(df, split_time=re_add_time)
                coeffs, poly_func = self.create_fit(df_before)
                new_data.append( (df_before, poly_func))

                # self.plot_poly_fit(df=df_before, poly_func=poly_func)

                coeffs, poly_func = self.create_fit(df_after)
                new_data.append( (df_after, poly_func))

                # self.plot_poly_fit(df=df_after, poly_func=poly_func)

            else:
                coeffs, poly_func = self.create_fit(df)
                new_data.append( (df, poly_func) )

        
        return new_data

    def create_fit(self, df: pd.DataFrame):
        """
        Fits a 7th-order polynomial to the 'P' column of a DataFrame.

        Parameters:
        - df (pd.DataFrame): Input DataFrame with at least a 'P' column.
        - x_col (str): Optional name of the column to use as the independent variable.
                    If None, the index will be used.

        Returns:
        - coeffs (np.ndarray): Coefficients of the 7th-order polynomial, highest degree first.
        - poly_func (np.poly1d): A callable polynomial function.
        """

        if "P" not in df.columns:
            raise ValueError("DataFrame must contain a 'P' column.")

        x = df["time"].values 
        y = df["P"].values

        if len(x) < 8:
            raise ValueError("At least 8 data points are required to fit a 7th-order polynomial.")

        coeffs = np.polyfit(x, y, deg=5)
        poly_func = np.poly1d(coeffs)

        return coeffs, poly_func

    def plot_poly_fit(self, df: pd.DataFrame, poly_func: np.poly1d):
        """
        Plots the original 'P' data and the fitted polynomial curve.

        Parameters:
        - df (pd.DataFrame): DataFrame containing 'P' and optionally an x column.
        - poly_func (np.poly1d): The fitted polynomial function.
        - x_col (str): Optional. Name of the x column. If None, the index is used.
        - title (str): Plot title.
        """
        if "P" not in df.columns:
            raise ValueError("DataFrame must contain a 'P' column.")

        x = df["time"].values 
        y = df["P"].values

        x_fit = np.linspace(x.min(), x.max(), 300)
        y_fit = poly_func(x_fit)

        plt.figure(figsize=(8, 5))
        plt.plot(x, y, "o", label="Original Data", markersize=6)
        plt.plot(x_fit, y_fit, "-", label="7th-Order Fit", linewidth=2)
        plt.xlabel("time")
        plt.ylabel("P")
        plt.title("fit")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def solve_catalyst_conc(self, df1, df2, order=1):
        
        c_vtna = ClassicVTNA(df_rct1=df1, df_rct2=df2, species_col_name="cat_total", product_col_name="P", time_col_name="time")
        c_vtna.show_plot()


        # plt.scatter(df1["time"], df1["P"])
        # plt.scatter(df2["time"], df2["P"])
        # apply_acs_layout()
        # plt.show()




if __name__ == "__main__":
    x = ThreeFileSolver(folder=r"C:\python_code\hein_modules\re_add_protocol_testing_files\M2_pd")
