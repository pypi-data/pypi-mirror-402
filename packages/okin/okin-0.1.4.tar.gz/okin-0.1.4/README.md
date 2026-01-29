# OKIN

Organic Kinetics is a package to perform tasks useful for understanding kinetic behaviour in organic chemistry.<br/>
Requires python >= 3.9 unless CMake is available then python >=3.8.

## Installation

From PyPI:
### Base package
- Create and activate a dedicated environment
- `pip install re_add_modeler`

### With Modeling
- make sure COPASI is installed (https://copasi.org/Download/)
- download and unzip 'python implementation of COPASI':
https://drive.google.com/file/d/1cVNLU4SBsz0JhC48MO69wVSLH-RpyIt6/view?usp=sharing
- OR clone github repo of 'python implementation of COPASI' `https://gitlab.com/heingroup/py_copasi`
- The modeling class requires the path to that folder as an argument `modler = Modler(copasi_path=local_copasi_path)`

## Usage

### 1. ChemDraw Parser

Parse reactions/mechanistic cycles directly from ChemDraw `.cdxml` files, allowing you to extract and work with reaction information.

**Example:**

```python
from okin.cd_parser.cd_parser import CDParser

# Load a ChemDraw file
cd_parser = CDParser(file_path="base_cycle.cdxml", draw=True)

# Extract all reactions
reactions = cd_parser.find_reactions()
print(f"Reactions found in {cd_parser.file_path}:")
for rct in reactions:
    print(rct)
```
- `file_path`: Path to your ChemDraw `.cdxml` file.  
- `draw=True`: Optionally renders the Chemdraw File with the bounding boxes. These determine which parts to treat as one reaction or a new one.
- `find_reactions()`: Returns a list of reaction objects parsed from the file, which can be used for other functions of this package (simulation, VTNA, or modeling).



### 2. Rate Equations

Calculate the *Steady-State* rate equation for a given mechanism.

**Example:**

```python
from okin.simulation.rate_equation import RateEquation

# Define reactions (reversible or irreversible)
reactions = ["A + cat <==> cat1", "cat1 + B -> cat + P", "B + cat -> cat_I"]
rate_eq = RateEquation(reactions)

# Display LaTeX rate law
print(rate_eq.debug_string)
rate_eq.show_latex_rate_law()

```
- The used catalytic species need to be named `cat` for base catalyst and `cat<nr>` e.g. `cat1` for all intermediates. Deactivated cat needs to be named `catI`.
- Reversible reactions should use `<==>`; irreversible reactions use `->`.  
- `show_latex_rate_law()` renders the final rate law in LaTeX format. If latex is not available it prints the LaTeX string.
- `rate_eq.debug_string` shows the math that has been performed


### 3. Simulation

Okin allows you to simulate chemical reaction kinetics over time with specified rate constants and initial concentrations.

#### **Fixed Simulation**

```python
from okin.simulation.simulator import Simulator
import matplotlib.pyplot as plt
from okin.base.chem_plot_utils import apply_acs_layout

# Define mechanism, rate constants, and initial concentrations
mechanism = ["A + cat -> cat1", "cat1 + B -> cat + P", "X + cat -> cat_deact"]
k_dict = {"k1": 10, "kN1": 5, "k2": 3, "kN2": 0, "k3": 0.005, "kN3": 0}
c_dict = {"A": 1.0, "B": 1.2, "cat": 0.05, "P": 0.0, "X": 0.1}

# Setup and run simulation
sim = Simulator()
sim.setup(mechanism, k_dict, c_dict)
sim.simulate(start=0, stop=80, nr_time_points=40)

# Access results
df = sim.result

# Plot results
plt.scatter(df["time"], df["A"])
plt.scatter(df["time"], df["B"])
plt.scatter(df["time"], df["P"])
plt.xlabel("time")
plt.ylabel("concentration")
apply_acs_layout()
plt.show()
```

- `setup()` takes mechanism as strings, rate constants (`k_dict`), and initial concentrations (`c_dict`).  
- `simulate()` runs the time evolution over a specified range with a given number of points.  
- Results are stored in `sim.result` as a DataFrame for plotting or further analysis.
- Reversibility is determined by k-values and not by arrows.



#### **Interactive Simulation**

```python
from okin.simulation.tc_engine import InteractiveTimeCourse

mechanism = [
    "A + cat = cat1",
    "cat1 + B = P + cat",
    "cat1 + A  = catI"
]
initial_conditions = {
    "A": 1.0, 
    "B": 1.2,
    "cat": 0.01
}
conserved_species = {
    # Specify any conservation equations
    # Example:
    # 'E_free': 'E_total - ES'
}
k_init = {
    "k1": 1,
    "k2": 0,
    "k3": 1,
    "k4": 0,
    "k5": 100,
    "k6": 10
}

portrait = InteractiveTimeCourse(
    mechanism, initial_conditions, conserved_species, k_init, mode="vtna")
portrait.run()

```

- `mechanism` contains the elementary steps as strings
- Reversible arrow: `=`: is highly recommended. Non-reversible arrow `->`: use with care 
- `initial_conditions` are the starting concentrations. Species not mentioned here are set to 0.
- `k_dict` contains the starting k-values. Range from 0-100 in steps of 0.1
- `k1` (forward for rct1); `k2` (backwards for rct1); !different from fixed simulation which has `k1` and `kN1`!
- `allowed_modes = ["vtna", "tc", "phase"]`. 
- `"vtna"` shows time course, catalyst concentration and VTNA for doubled [cat]. Slower response time than other modes.
- `"tc"` shows only the time course. Good for fast exploration.
- `"phase"` shows customizable phase diagrams


### 4. VTNA (Variable Time Normalization Analysis)

Determine reaction orders via VTNA (https://pubs.rsc.org/en/content/articlelanding/2019/sc/c8sc04698k).

**Example:**

```python
from okin.kinetics.vtna import ClassicVTNA

# Assuming df1 and df2 are results from two simulations or experiments
vtna = ClassicVTNA(df_rct1=df1, df_rct2=df2, species_col_name="cat", product_col_name="P", time_col_name="time")

# Best kinetic order for the species
print(f"Best order for cat: {vtna.best_order}")

# Plot normalized VTNA data
vtna.show_plot()
```

- `df_rct1`, `df_rct2`: DataFrames containing time-course data for two experiments that only vary in one concentration.  
- `species_col_name`: Name of the species for which the initial concentration was changed. Same name as the provided data.
- `product_col_name`: Name of the column used to track reaction progress. Same name as the provided data.
- `time_col_name`: Name of the time column.  Same name as the provided data.
- `show_plot()`: Visualizes the normalized reaction rates for comparison.


### 5. Modeling with COPASI

Okin integrates with COPASI (https://copasi.org/) to build and fit kinetic models from experimental data.

**Example:**

```python
from okin.model.modler import Modler

# Initialize Modler with local COPASI path
modler = Modler(copasi_path=r"D:\python_code\hein_modules\local_copasi")

# Set reaction mechanism
reactions = ["A + cat -> cat1", "cat1 + B -> cat + P", "X + cat -> cat_I"]
modler.set_m_reactions(reactions)

# Add experimental CSV data
modler.add_experiment_csv(["data1.csv","data2.csv"])

# Specify species for model fitting
modler.set_species_for_model(["P","A"])
modler.set_species_to_match(["P","A","B"])

# Configure COPASI optimization settings
modler.set_copasi_settings({"number_of_generations":50,"population_size":50})

# Create and fit the model
modler.create_single_model()
modler.show_model_fit(save_modeled_data=True, show_all=True)
```

- `copasi_path`: Path to the local COPASI folder (LINK WILL BE ADDED SOON)  
- `reactions`: List of reactions defining the mechanism.
- `experiment CSV files`: Paths to one or more CSV files with experimental data  .
- `species_for_model`: Species used for internal error calculations. 
- `species_to_match`: Species used by COPASI to fit the model.
- `copasi_settings`: Dictionary of COPASI optimization parameters  
- `create_single_model()`: Runs COPASI. 
- `show_model_fit()`: Displays the fitted model and optionally saves modeled data.


## License
This project is licensed under the MIT License.

## Future
This project will receive updates in the near future.

