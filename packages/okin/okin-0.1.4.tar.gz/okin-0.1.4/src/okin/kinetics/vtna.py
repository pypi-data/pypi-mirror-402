import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
from scipy.optimize import minimize
from scipy.optimize import differential_evolution

from scipy.interpolate import interp1d
from sklearn.metrics import r2_score
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

from okin.base.chem_plot_utils import apply_acs_layout
from okin.base.chem_logger import chem_logger

class ClassicVTNA():
    def __init__(self, df_rct1, df_rct2, species_col_name, product_col_name, time_col_name="time", min_order=-2, max_order=2, auto_evaluate=True):
        self.logger = chem_logger.getChild(self.__class__.__name__)
        #? 1-series should be the faster reaction
        self.species1 = df_rct1[species_col_name]
        self.product1 = df_rct1[product_col_name]
        self.time1 = df_rct1[time_col_name]

        self.species2 = df_rct2[species_col_name]
        self.product2 = df_rct2[product_col_name]
        self.time2 = df_rct2[time_col_name]

        self.product1 -= min(self.product1)
        self.product2 -= min(self.product2)


        self.min_order = min_order
        self.max_order = max_order

        self.species_col_name = species_col_name
        self.product_col_name = product_col_name
        self.time_col_name = time_col_name

        self.df_rct1 = df_rct1
        self.df_rct2 = df_rct2

        if auto_evaluate:
            self.calc_best_order()

    def normalize_integral_old(self, concentrations, times, order=1):
        """
        Normalize the integral of concentrations up to a given time point.

        Args:
            concentrations (pd.Series): A pandas Series containing concentration values.
            times (pd.Series): A pandas Series containing corresponding time values.
            order (float): The order of the integral.

        Returns:
            pd.Series: A pandas Series containing the normalized integral values up to each time point.
        """
        if not isinstance(concentrations, pd.Series) or not isinstance(times, pd.Series):
            raise ValueError("concentrations and times must be pandas Series")

        if concentrations.shape != times.shape:
            raise ValueError("concentrations and times must have the same shape")

        normalized_integral = [0]

        for i in range(1, len(concentrations)):
            prev_conc = concentrations.iloc[i - 1]
            prev_time = times.iloc[i - 1]

            curr_conc = concentrations.iloc[i]
            curr_time = times.iloc[i]

            time_diff = curr_time - prev_time

            new_rect_height = (curr_conc + prev_conc) * 0.5
            epsilon = 1e-20  # Small value to avoid division by zero
            new_subs_rect = (new_rect_height ** order) * time_diff

            if new_subs_rect < epsilon:
                new_subs_rect = epsilon

            normalized_integral.append(normalized_integral[-1] + new_subs_rect)

        return pd.Series(normalized_integral)

    def normalize_integral(self, concentrations: pd.Series, times: pd.Series, order=1) -> pd.Series:
        if not isinstance(concentrations, pd.Series) or not isinstance(times, pd.Series):
            raise ValueError("concentrations and times must be pandas Series")
        if concentrations.shape != times.shape:
            raise ValueError("concentrations and times must have the same shape")

        # Differences in time (Δt)
        dt = times.diff().fillna(0).to_numpy()

        # Average concentrations between intervals
        avg_conc = (concentrations.shift() + concentrations) / 2
        avg_conc.iloc[0] = 0  # First value has no previous point

        # Compute (avg_conc ** order) * dt
        integrand = np.power(avg_conc, order) * dt

        return integrand.cumsum()

    def get_error(self, x1, y1, x2, y2):
        """
        Calculate the error between two sets of data points.

        Args:
            x1 (pd.Series): x-axis values for the first set of data points.
            y1 (pd.Series): Corresponding y-values for the first set of data points.
            x2 (pd.Series): x-axis values for the second set of data points.
            y2 (pd.Series): Corresponding y-values for the second set of data points.

        Returns:
            float: The error between the two sets of data points.
        """
        if not isinstance(x1, pd.Series) or not isinstance(y1, pd.Series) or \
        not isinstance(x2, pd.Series) or not isinstance(y2, pd.Series):
            raise ValueError("All inputs must be pandas Series")

        
        # Combine the data points into a single DataFrame
        x = list(x1) + list(x2)
        y = list(y1) + list(y2)
        # print(x)
        # print(y)
        # sys.exit()
        # data_ = pd.DataFrame({'x-axis': pd.concat([x1, x2]), 'y-axis': pd.concat([y1, y2])})
        data = pd.DataFrame({'x-axis': x, 'y-axis': y})
        # data = pd.DataFrame({'x-axis': pd.concat([x1, x2]), 'y-axis': pd.concat([y1, y2])})

        # Sort the data by x-axis and calculate the absolute difference
        sorted_diff = data.sort_values('x-axis').diff()
        error = sorted_diff.abs()['y-axis'].sum()

        return error
    
    

    def calc_best_order(self):
        results = []

        for order_ in np.linspace(self.min_order, self.max_order, 201):
            order = round(order_, 2)

            normalized_x_axis_1 = self.normalize_integral(
                self.species1, self.time1, order=order)
            normalized_x_axis_2 = self.normalize_integral(
                self.species2, self.time2, order=order)

            error = self.get_error(
                normalized_x_axis_1, self.product1, normalized_x_axis_2, self.product2)

            results.append((error, order))
        results.sort(key=lambda errs: errs[0])
        
        self.results = results
        self.best_error = results[0][0]
        self.best_order = results[0][1]
        self.best_norm_x_axis1 = self.normalize_integral(
            self.species1, self.time1, order=self.best_order)
        self.best_norm_x_axis2 = self.normalize_integral(
            self.species2, self.time2, order=self.best_order)

    def show_plot(self, label1=None, label2=None, xlabel=None, ylabel=None, title=None, path=None):
        apply_acs_layout()

        if not xlabel:
            xlabel = f"Σ {self.species_col_name}^{self.best_order}Δt"
        if not ylabel:
            ylabel = f"{self.product_col_name}"
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        if not label1:
            label1 = f"{self.product_col_name} 1"
        if not label2:
            label2 = f"{self.product_col_name} 2"

        if title:
            plt.title(title)
        else:
            plt.title(f"Lowest error  = {self.best_error}")
        
        color1, color2 = plt.rcParams['axes.prop_cycle'].by_key()['color'][:2]
        plt.scatter(self.best_norm_x_axis1, self.product1, label=label1, facecolors='none',linewidths=1.5, edgecolors=color1)
        plt.scatter(self.best_norm_x_axis2, self.product2, label=label2, facecolors='none',linewidths=1.5, edgecolors=color2)

        plt.legend(loc="best", fontsize=12)
        plt.tight_layout()
        if path:
            plt.savefig(path, dpi=500)
        plt.show()

    def get_specific_order_axes(self, order, show=True):
        normalized_x_axis_1 = self.normalize_integral(
            self.species1, self.time1, order=order)
        normalized_x_axis_2 = self.normalize_integral(
            self.species2, self.time2, order=order)

        if show:
            plt.xlabel(f"Σ {self.species_col_name}^{order}Δt")
            plt.ylabel(f"{self.product_col_name}")

            plt.scatter(normalized_x_axis_1, self.product1,
                    label=f"{self.product_col_name} 1")
            plt.scatter(normalized_x_axis_2, self.product2,
                    label=f"{self.product_col_name} 2")

            plt.legend(loc="best", fontsize=12)
            apply_acs_layout()
            plt.show()
        error = self.get_error(x1=normalized_x_axis_1, y1=self.product1, x2=normalized_x_axis_2, y2=self.product2)
        return normalized_x_axis_1, normalized_x_axis_2, error

class MergedVTNA():
    def __init__(self, dfs, species_dict, product_col_name, time_col_name="time", use_r2=False):
        self.product_col_name = product_col_name
        self.time_col_name = time_col_name
        self.dfs = dfs
        self.cut_dfs(pcnt_of_product=0.8)
        self.sd = species_dict

        if use_r2:
            print("WARNING! You are about to use r2 in the optimization. Unless you fully understand what that means DONT DO IT. It usually breaks it and was only implemented for debugging purposes.")
        self.use_r2 = use_r2
        self.last_r2 = None

    def normalize_integrals(self, show=False):
        for df in self.dfs:
            integral_sum = None
            
            title = ""
            for species, vals in self.sd.items():
                order = vals["guessed_order"]
                title += f"{species}={order} | "
                if integral_sum is None:
                    integral_sum = df[species] ** order
                else:
                    integral_sum *= df[species] ** order
            
            df.loc[:, 'delta_t'] = df[self.time_col_name].diff().fillna(0)
            df.loc[:, 'norm_x'] = (integral_sum * df['delta_t']).cumsum().fillna(0)
        
            if show:
                plt.scatter(df["norm_x"], df[self.product_col_name], label=f"[{self.product_col_name}]")
        
        if show:
            plt.title(title)
            apply_acs_layout()
            plt.show()

    def get_overlay_simple(self):
        df_concat_vertical = pd.concat(self.dfs, ignore_index=True)
        sorted_diff = df_concat_vertical.sort_values('norm_x').diff()
        error = sorted_diff.abs()[self.product_col_name].sum()
        print(f"{error = }")
        return error
    
    def get_overlay(self):
        # Concatenate all 'norm_x' values to create a common grid
        all_norm_x = np.concatenate([df['norm_x'].values for df in self.dfs])
        common_grid = np.linspace(all_norm_x.min(), all_norm_x.max(), 1000)
        
        # Interpolate each DataFrame's 'P' values onto the common grid
        interpolated_Ps = []
        
        for df in self.dfs:
            interp_func = interp1d(df['norm_x'], df[self.product_col_name], kind='linear', fill_value="extrapolate")
            interpolated_Ps.append(interp_func(common_grid))
        
        # Calculate the MSE between each pair of interpolated P values
        mse_values = []
        num_dfs = len(interpolated_Ps)
        
        for i in range(num_dfs):
            for j in range(i + 1, num_dfs):
                mse = mean_squared_error(interpolated_Ps[i], interpolated_Ps[j])
                mse_values.append(mse)
        
        # Return the average MSE as a measure of overlap
        return np.mean(mse_values)

    def get_r2(self, show=False):

        r2_scores = []
        for i, df in enumerate(self.dfs, 1):
            # Reshape data for sklearn
            X = df['norm_x'].values.reshape(-1, 1)
            y = df['P'].values

            model = LinearRegression()
            model.fit(X, y)
            y_pred = model.predict(X)
            r2 = r2_score(y, y_pred)
            r2_scores.append(1-r2)

            if show:
                print(f"DataFrame {i}:")
                print(f"  Coefficients: {model.coef_}")
                print(f"  Intercept: {model.intercept_}")
                print(f"  R²: {r2:.4f}")
                
                # Plot the data and the linear fit
                plt.figure(figsize=(10, 6))
                plt.scatter(df['norm_x'], df['P'], label='Data')
                plt.plot(df['norm_x'], y_pred, color='red', label='Linear Fit')
                plt.xlabel('norm_x')
                plt.ylabel('P')
                plt.title(f'Linear Regression for DataFrame {i}')
                plt.legend()
                plt.show()

        return r2_scores
    
    def get_error(self, orders):
        for species, new_order in zip(self.sd.keys(), orders):
            # print(f"{species = }, {new_order = }")
            self.sd[species]["guessed_order"] = new_order
        self.normalize_integrals()

        overlay_error = self.get_overlay() * 100

        r2_error = sum(self.get_r2()) 
        self.last_r2 = r2_error # track last r2_error even though not used for optimizaiton
        r2_error = r2_error * 100 * float(self.use_r2)

        

        error = overlay_error + r2_error
        print(f"{overlay_error = }, {r2_error = }, {self.last_r2 = }")
        return error

    def cut_dfs(self, pcnt_of_product=0.8):
        cut_dfs = []
        for df in self.dfs:
            max_value = df[self.product_col_name].max()
            cutoff_value = pcnt_of_product * max_value
            cutoff_index = df[df[self.product_col_name] >= cutoff_value].index[0]
            cut_df = df.loc[:cutoff_index]
            cut_dfs.append(cut_df)

        self.dfs = cut_dfs.copy()

    def find_best_orders(self, method='L-BFGS-B'):
        initial_guess = [self.sd[species]['guessed_order'] for species in self.sd if self.sd[species]['best_order'] is None]
        bounds = [(self.sd[species]['min_order'], self.sd[species]['max_order']) for species in self.sd if self.sd[species]['best_order'] is None]
        print(initial_guess, bounds)
        # input("go?")
        result = minimize(self.get_error, x0=initial_guess, bounds=bounds, method=method)
        result = differential_evolution(self.get_error, bounds=bounds, init='latinhypercube')
        print(result)
        return result
                            
class PointVTNA(ClassicVTNA):
    DESCRIPTION ="""
    Assumptions:
        - all conc are measured at the same time in a run (not measure SM at t=1 and P at t=2)
        - in between points the conc change is assumed to be linear (VTNA does that already)

    interpolate which generates the matching conc points on the other tc errors when 
    """
        
    def __init__(self, df_rct1, df_rct2, species_col_name, product_col_name, time_col_name, min_order=-2, max_order=2, win=7):
        super().__init__(df_rct1, df_rct2, species_col_name, product_col_name, time_col_name, min_order, max_order)
        self.orders = self.get_orders(win)

    def get_orders(self, win):
        # set variables
        self.n = n = win # yeah i'm not renaming
        conc1 = self.species1.copy()
        conc2 = self.species2.copy()
        time1 = self.time1.copy()
        time2 = self.time2.copy()
        prod1 = self.product1.copy()
        prod2 = self.product2.copy()
        p_max = min([prod1.max(), prod2.max()])

        p1_index = prod1[(prod1 <= p_max)].index
        p2_index = prod2[(prod2 <= p_max)].index

        conc1 = conc1.iloc[p1_index]
        time1 = time1.iloc[p1_index]
        prod1 = prod1.iloc[p1_index]
        conc2 = conc2.iloc[p2_index]
        time2 = time2.iloc[p2_index]
        prod2 = prod2.iloc[p2_index]

        # plt.scatter(time1, prod1, label="p1", color="black")
        # plt.scatter(time2, prod2, label="p2")
        # plt.ylabel("y")
        # plt.xlabel("x")
        # plt.legend(loc="best")
        # plt.show()

        orders = []
        plot_time = []
        for i, t in zip(range(len(prod1) - n + 1), range(len(time1) - n + 1)):
            print(i)
            
            win_p1 = prod1.iloc[i:i+n]  # Get 5 values from p1
            # window1 = window_p1.index      # Get the corresponding indices
            
            win_p2 = prod2[(prod2 >= win_p1.min()) & (prod2 <= win_p1.max())]

            win_s1 = conc1[win_p1.index]
            win_t1 = time1[win_p1.index]

            win_t2 = time2[win_p2.index]
            win_s2 = conc2[win_p2.index]


            x_time = self.interpolate(long_time=win_t1, long_p=win_p1, p_conc=win_p2.min())
            if x_time is None:
                break
            dt = win_t2.min() - x_time

            win_t1.iloc[0] = x_time
            win_p1.iloc[0] = win_p2.min()
            win_t2 -= dt    


            best_order, best_norm_x_axis1, best_norm_x_axis2 = self.p_calc_best_order(time1=win_t1, species1=win_s1, product1=win_p1, time2=win_t2, species2=win_s2, product2=win_p2)


            plot_time.append(t)
            orders.append(best_order)

        self.plotting_time = plot_time
        return orders

    def p_calc_best_order(self, time1, species1, product1, time2, species2, product2):
        results = []
        ers = []
        ors = []
        for order_ in np.linspace(self.min_order, self.max_order, 201):
            order = round(order_, 2)

            normalized_x_axis_1 = self.normalize_integral(
                species1, time1, order=order)
            normalized_x_axis_2 = self.normalize_integral(
                species2, time2, order=order)


            error = self.get_error_(
                normalized_x_axis_1, product1, normalized_x_axis_2, product2)

            results.append((error, order))
            ers.append(error)
            ors.append(order)

        results.sort(key=lambda errs: errs[0])
        best_order = results[0][1]
        best_norm_x_axis1 = self.normalize_integral(species1, time1, order=best_order)
        best_norm_x_axis2 = self.normalize_integral(species2, time2, order=best_order)
        return best_order, best_norm_x_axis1, best_norm_x_axis2
        
    def get_error_(self, xs1, ys1, xs2, ys2):      
        xs = list(xs1) + list(xs2)
        ys = list(ys1) + list(ys2)

        slope, intercept, r_value, p_value, std_err = linregress(xs, ys)

        # Calculate R-squared value
        r_squared = r_value**2

        error = 1-r_squared

        return error

    def get_matching_values(self, full_time, full_species, full_product, p_window):
        #* get matching species values
        # Find the indices of points in 'full' that are within the range defined time_window
        f_indices = full_product[(full_product >= p_window.min()) & (full_product <= p_window.max())].index

        # Filter 'long' and 'long_time' based on the filtered indices
        time2_window = list(full_time[f_indices])
        conc2_window = list(full_species[f_indices])
        prod2_window = list(full_product[f_indices])


        # calculate approx conc for lowest and highest time
        # low_s = self.interpolate(long_time=full_time, long=full_species, time=p_window.min())
        # high_s = self.interpolate(long_time=full_time, long=full_species, time=p_window.max())
        # # append those conc to the conc2_window
        # conc2_window = [low_s] + conc2_window + [high_s]
        # time2_window = [p_window.min()] + time2_window + [p_window.max()]

        # #? maybe leave out product from prediction??
        # #TODO figure this out
        # low_p = self.interpolate(long_time=full_time, long=full_species, time=p_window.min())
        # high_p = self.interpolate(long_time=full_time, long=full_species, time=p_window.max())

        return pd.Series(time2_window), pd.Series(conc2_window), pd.Series(prod2_window)

    def interpolate(self, long_time, long_p, p_conc):
        """
        Perform linear interpolation between two points in 'long' based on 'conc'.

        Args:
            long (pd.Series): A pandas Series containing the 'long' values.
            long_time (pd.Series): A pandas Series containing the corresponding time values.
            conc (float): The concentration value for which interpolation is needed.

        Returns:
            float: The interpolated x-value corresponding to 'conc'.
        """
        if not isinstance(long_p, pd.Series) or not isinstance(long_time, pd.Series):
            raise ValueError("'long' and 'long_time' must be pandas Series.")

        if long_p.shape[0] != long_time.shape[0]:
            raise ValueError("'long' and 'long_time' must have the same number of elements.")


        # Find the nearest values in 'long' one above and one below 'conc'
        above_p = long_p[long_p > p_conc].min()
        below_p = long_p[long_p <= p_conc].max()

        # Perform linear interpolation
        try:
            x_above = long_time[long_p == above_p].values[0]
            x_below = long_time[long_p == below_p].values[0]
        except:
            return None

        y_above = above_p
        y_below = below_p

        x_time = np.interp(p_conc, [y_below, y_above], [x_below, x_above])

        return x_time
       
    def apply_moving_average(self, ma_width=3):
        if not ma_width%2:
            print("Please give an odd number as moving average window")
            return
        self.plotting_offset = (ma_width-1)/2
        self.orders = np.convolve(self.orders, np.ones(ma_width), 'valid') / ma_width

    def show_plot(self, show_best_order=True):
        plt.xlabel("time")
        plt.ylabel(f"order of {self.species_col_name}")
        plt.title(f"avg order: {round(sum(self.orders)/len(self.orders), 2)} c_vtna: {self.best_order}")
        
        plt.plot(self.plotting_time, self.orders, alpha=0.5)
        plt.scatter(self.plotting_time, self.orders, alpha=0.5)
        
        plt.axhline(self.best_order, label="classical VTNA order", color="darkgreen")

        plt.legend(loc="best", fontsize=12)
        plt.show()

    def show_interpolation(self, index):
        #! This is for debug!!! 
        n = 3
        conc1 = self.species1.copy()
        conc2 = self.species2.copy()
        time1 = self.time1.copy()
        time2 = self.time2.copy()
        prod1 = self.product1.copy()
        prod2 = self.product2.copy()

        # form lists with length n for conc1
        for i in range(len(conc1) - n + 1):
            conc_window = conc1.iloc[i:i+n].to_numpy()
            time_window = time1.iloc[i:i+n].to_numpy()
            prod_window = prod1.iloc[i:i+n].to_numpy()

            time2_window, conc2_window, prod2_window = self.get_matching_values(full_time=time2, full_species=conc2, full_product=prod2, p_window=time_window)

            if i == index:
                #! do not delete. this is my test if something goes wrong
                # plt.scatter(time2_window, conc2_window, alpha=0.5, label="filtered points")
                plt.scatter(time2, conc2, alpha=0.5, label="all points (ys)")
                plt.scatter(time_window, conc_window, label="window", color="black")
                plt.ylabel("y")
                plt.xlabel("x")
                plt.legend(loc="best")
                plt.title("data")
                # plt.title(f"ys filterd in range {conc_window.min()} - {conc_window.max()}")
                plt.show()





