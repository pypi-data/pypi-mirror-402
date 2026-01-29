"""
This module was originally made by Dylan Pyle and slightly changed to fit into this package.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint
from matplotlib.widgets import Slider, CheckButtons, Button, TextBox
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap
from typing import Dict, List, Tuple, Any, Callable, Optional
from itertools import combinations
import pandas as pd
from okin.kinetics.vtna import ClassicVTNA
import time
# from okin.base.chem_plot_utils import apply_acs_layout_ax


class MechanismParser:
    """Parse reaction mechanisms and extract species and reactions."""
    
    @staticmethod
    def parse_mechanism(reaction_strings: List[str]) -> Dict[str, Any]:
        """
        Parse a list of reaction strings and return reaction information.
        Supports both irreversible (->) and reversible (=) reactions.
        
        Args:
            reaction_strings: List of reaction strings, e.g., 
                ["A + cat = cat1", "cat1 -> cat + P"]
                Use "=" for reversible reactions (generates forward and reverse)
                Use "->" for irreversible reactions
        
        Returns:
            Dictionary containing:
            - 'reactions': List of all reaction tuples (reactants, products, reversible)
            - 'species': Set of all unique species
            - 'num_reactions': Total number of elementary reactions (reversible counted as 2)
            - 'k_dict': Dictionary with k1, k2, ... for each elementary reaction
        """
        reactions = []
        species_set = set()
        reaction_counter = 0
        
        # Parse all reactions
        for i, rxn_str in enumerate(reaction_strings):
            # Remove extra whitespace
            rxn_str = rxn_str.strip()
            
            # Check if reversible (=) or irreversible (->)
            is_reversible = '=' in rxn_str and '->' not in rxn_str
            
            if is_reversible:
                # Split by =
                parts = rxn_str.split('=')
                if len(parts) != 2:
                    raise ValueError(f"Invalid reaction format: '{rxn_str}'. Must have exactly one '='")
            elif '->' in rxn_str:
                # Split by ->
                parts = rxn_str.split('->')
                if len(parts) != 2:
                    raise ValueError(f"Invalid reaction format: '{rxn_str}'. Must have exactly one '->'")
            else:
                raise ValueError(f"Invalid reaction format: '{rxn_str}'. Must contain '=' or '->'")
            
            reactants_str = parts[0].strip()
            products_str = parts[1].strip()
            
            # Parse reactants and products
            reactants = [s.strip() for s in reactants_str.split('+')] if reactants_str else []
            products = [s.strip() for s in products_str.split('+')] if products_str else []
            
            # Add to species set
            species_set.update(reactants)
            species_set.update(products)
            
            # Add forward reaction
            reactions.append({
                'reactants': reactants,
                'products': products,
                'index': reaction_counter,
                'reversible': is_reversible,
                'is_reverse': False,
                'parent_index': i
            })
            reaction_counter += 1
            
            # Add reverse reaction if reversible
            if is_reversible:
                reactions.append({
                    'reactants': products,  # Swap for reverse
                    'products': reactants,
                    'index': reaction_counter,
                    'reversible': is_reversible,
                    'is_reverse': True,
                    'parent_index': i
                })
                reaction_counter += 1
        
        # Create k_dict with one rate constant per elementary reaction
        k_dict = {}
        for i in range(len(reactions)):
            k_dict[f'k{i+1}'] = 0.0  # Rate constant (will be set by user/sliders)
        
        return {
            'reactions': reactions,
            'species': sorted(species_set),
            'num_reactions': len(reactions),
            'k_dict': k_dict
        }
    
    @staticmethod
    def print_mechanism_info(mechanism_info: Dict[str, Any]) -> None:
        """
        Print formatted information about the parsed mechanism.
        
        Args:
            mechanism_info: Dictionary returned from parse_mechanism()
        """
        print("\n" + "="*70)
        print("MECHANISM INFORMATION")
        print("="*70)
        
        print(f"\nSpecies detected: {mechanism_info['species']}")
        print(f"Total elementary reactions: {mechanism_info['num_reactions']}")
        
        print("\n--- Elementary Reactions ---")
        for rxn in mechanism_info['reactions']:
            reactants = ' + '.join(rxn['reactants'])
            products = ' + '.join(rxn['products'])
            k = f"k{rxn['index']+1}"
            arrow = "⇌" if rxn['reversible'] and not rxn['is_reverse'] else "→"
            if rxn['reversible'] and rxn['is_reverse']:
                print(f"  R{rxn['index']+1}: {reactants} → {products}  ({k}) [reverse]")
            else:
                print(f"  R{rxn['index']+1}: {reactants} {arrow} {products}  ({k})")
        
        print("\n" + "="*70 + "\n")


class ODEGenerator:
    """Generate ODE systems from parsed reaction mechanisms."""
    
    @staticmethod
    def generate_ode_function(mechanism_info: Dict[str, Any], 
                             conserved_species: Optional[Dict[str, str]] = None) -> Callable:
        """
        Generate an ODE function from a parsed mechanism.
        
        Args:
            mechanism_info: Dictionary from parse_mechanism()
            conserved_species: Dict mapping species name to conservation equation
                              e.g., {'cat': 'cat_total - cat1 - catIA - catIP'}
                              
        Returns:
            ODE function compatible with scipy.integrate.odeint
        """
        reactions = mechanism_info['reactions']
        species = mechanism_info['species']
        
        # Determine which species are dynamic (have ODEs) vs conserved
        conserved_species = conserved_species or {}
        dynamic_species = [s for s in species if s not in conserved_species]
        
        # Create species index mapping for dynamic species
        species_idx = {s: i for i, s in enumerate(dynamic_species)}
        
        def ode_system(state, t, k_values):
            """Generated ODE system"""
            # Unpack state for dynamic species
            state_dict = {s: state[i] for i, s in enumerate(dynamic_species)}
            
            # Calculate conserved species
            for spec, formula in conserved_species.items():
                # Build namespace for eval
                namespace = {**state_dict, **k_values}
                state_dict[spec] = eval(formula, {"__builtins__": {}}, namespace)
                # Ensure non-negative
                state_dict[spec] = max(0, state_dict[spec])
            
            # Calculate reaction rates
            rates = []
            for rxn in reactions:
                k = k_values.get(f"k{rxn['index']+1}", 0.0)
                
                # Calculate rate based on reactants
                rate = k
                for reactant in rxn['reactants']:
                    conc = state_dict.get(reactant, 0)
                    rate *= max(0, conc)
                
                rates.append(rate)
            
            # Calculate derivatives for dynamic species
            derivatives = []
            for spec in dynamic_species:
                d_dt = 0
                
                # Add contributions from all reactions
                for i, rxn in enumerate(reactions):
                    # Species consumed (negative contribution)
                    d_dt -= rxn['reactants'].count(spec) * rates[i]
                    # Species produced (positive contribution)
                    d_dt += rxn['products'].count(spec) * rates[i]
                
                derivatives.append(d_dt)
            
            return derivatives
        
        return ode_system
    
    @staticmethod
    def compute_derivatives_at_point(mechanism_info: Dict[str, Any],
                                     state_dict: Dict[str, float],
                                     k_values: Dict[str, float],
                                     conserved_species: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """
        Compute derivatives at a specific point for vector field calculation.
        
        Args:
            mechanism_info: Dictionary from parse_mechanism()
            state_dict: Dictionary mapping species names to concentrations
            k_values: Dictionary of rate constants
            conserved_species: Dict mapping species name to conservation equation
            
        Returns:
            Dictionary mapping species names to their derivatives
        """
        reactions = mechanism_info['reactions']
        species = mechanism_info['species']
        conserved_species = conserved_species or {}
        
        # Calculate conserved species
        full_state = state_dict.copy()
        for spec, formula in conserved_species.items():
            namespace = {**full_state, **k_values}
            full_state[spec] = max(0, eval(formula, {"__builtins__": {}}, namespace))
        
        # Calculate reaction rates
        rates = []
        for rxn in reactions:
            k = k_values.get(f"k{rxn['index']+1}", 0.0)
            rate = k
            for reactant in rxn['reactants']:
                conc = full_state.get(reactant, 0)
                rate *= max(0, conc)
            rates.append(rate)
        
        # Calculate derivatives
        derivatives = {}
        for spec in species:
            if spec not in conserved_species:
                d_dt = 0
                for i, rxn in enumerate(reactions):
                    d_dt -= rxn['reactants'].count(spec) * rates[i]
                    d_dt += rxn['products'].count(spec) * rates[i]
                derivatives[spec] = d_dt
        
        return derivatives


class PhasePortraitPlotter:
    """Create phase portrait visualizations."""
    
    @staticmethod
    def generate_plot_pairs(species: List[str], 
                           conserved_species: Optional[Dict[str, str]] = None) -> List[Tuple[str, str]]:
        """
        Generate all meaningful pairs of species for phase portraits.
        
        Args:
            species: List of species names
            conserved_species: Dict of conserved species (excluded from dynamic pairs)
            
        Returns:
            List of (species1, species2) tuples for plotting
        """
        conserved_species = conserved_species or {}
        dynamic_species = [s for s in species if s not in conserved_species]
        
        # Generate all unique pairs of dynamic species
        pairs = list(combinations(dynamic_species, 2))
        
        return pairs
    
    @staticmethod
    def create_vector_field(x_range: np.ndarray, y_range: np.ndarray,
                           x_species: str, y_species: str,
                           mechanism_info: Dict[str, Any],
                           k_values: Dict[str, float],
                           fixed_values: Dict[str, float],
                           conserved_species: Optional[Dict[str, str]] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Create vector field for a 2D phase portrait.
        
        Args:
            x_range: Array of x-axis values
            y_range: Array of y-axis values
            x_species: Name of species on x-axis
            y_species: Name of species on y-axis
            mechanism_info: Parsed mechanism information
            k_values: Rate constants
            fixed_values: Fixed concentrations for other species
            conserved_species: Conservation equations
            
        Returns:
            Tuple of (dx, dy, magnitude) arrays
        """
        X, Y = np.meshgrid(x_range, y_range)
        dX = np.zeros_like(X)
        dY = np.zeros_like(Y)
        
        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                # Build state dictionary
                state_dict = fixed_values.copy()
                state_dict[x_species] = X[i, j]
                state_dict[y_species] = Y[i, j]
                
                # Compute derivatives
                derivs = ODEGenerator.compute_derivatives_at_point(
                    mechanism_info, state_dict, k_values, conserved_species
                )
                
                dX[i, j] = derivs.get(x_species, 0)
                dY[i, j] = derivs.get(y_species, 0)
        
        magnitude = np.sqrt(dX**2 + dY**2)
        magnitude[magnitude == 0] = 1  # Avoid division by zero
        
        return dX, dY, magnitude

class InteractiveTimeCourse:
    """Create interactive phase portrait visualization with sliders."""
    
    def __init__(self, mechanism: List[str], 
                 initial_conditions: Dict[str, float],
                 conserved_species: Optional[Dict[str, str]] = None,
                 k_init: Optional[Dict[str, float]] = None,
                 mode: str = "tc"):
        """
        Initialize interactive phase portrait system.
        
        Args:
            mechanism: List of reaction strings
            initial_conditions: Dictionary of initial concentrations
            conserved_species: Dictionary of conservation equations
            k_init: Initial rate constant values (optional)
            t_max: Maximum simulation time
        """
        self.mechanism = mechanism
        self.initial_conditions = initial_conditions
        self.conserved_species = conserved_species or {}
        self.t_max = 1
        self.mode = mode
        # Parse mechanism
        self.mech_info = MechanismParser.parse_mechanism(mechanism)
        MechanismParser.print_mechanism_info(self.mech_info)
        
         # Generate ODE function
        self.ode_func = ODEGenerator.generate_ode_function(
            self.mech_info, conserved_species
        )
        
        # Setup initial k values
        if k_init is None:
            k_init = {}
            for i in range(1, self.mech_info['num_reactions'] + 1):
                # Default: forward reactions faster than reverse
                if i % 2 == 1:
                    k_init[f'k{i}'] = 0.0
                else:
                    k_init[f'k{i}'] = 0.0
        self.k_init = k_init
        
        # Determine which dynamic species need sliders (only non-zero initial conditions)
        self.dynamic_species = [s for s in self.mech_info['species'] 
                                if s not in self.conserved_species]
        # Only create sliders for species explicitly specified with non-zero initial values
        # Any species not in initial_conditions defaults to 0.0
        self.slider_species = [s for s in self.dynamic_species 
                               if s in initial_conditions and initial_conditions[s] != 0.0]
        
        # Generate plot pairs
        self.plot_pairs = PhasePortraitPlotter.generate_plot_pairs(
            self.mech_info['species'], conserved_species
        )
        
        # Setup plot visibility
        self.plot_visible = {f'plot{i+1}': i < 2 for i in range(len(self.plot_pairs))}
        
        # Setup slider parameters
        self.slider_dict = {}
        self.slider_axes = {}

        # Figure and axes
        self.fig = None
        self.plot_axes = []
        
        num_reactions = self.mech_info['num_reactions']
        # Only count sliders for species with non-zero initial conditions
        num_initial_conds = len(self.slider_species)
        num_sliders = num_reactions + num_initial_conds
        
        slider_height_needed = num_sliders * 0.35
        base_plot_height = 6
        fig_height = base_plot_height + slider_height_needed
        
        # Create figure
        self.fig = plt.figure(figsize=(16, fig_height))
        bottom_margin = 0.04 + (num_sliders * 0.04)
        plt.subplots_adjust(left=0.05, bottom=bottom_margin, right=0.95, 
                           top=0.92, hspace=0.20, wspace=0.15)
        
        # Create subplot axes (show 2 at a time) + 1 timecourse
        if self.mode == "tc":
            self.time_course_ax = self.fig.add_subplot(1, 1, 1) #self.fig.add_axes([0.1, 0.1, 0.4, 0.4])
        elif self.mode == "vtna":
            gs = self.fig.add_gridspec(2, 2, width_ratios=[2, 1.3], height_ratios=[1, 1], wspace=0.1, hspace=0.1)
            # Left column: two plots stacked
            self.time_course_ax = self.fig.add_subplot(gs[0, 0])  # top-left
            self.cat_ax = self.fig.add_subplot(gs[1, 0])  # bottom-left
            # Right column: one plot spanning both rows
            self.vtna_ax = self.fig.add_subplot(gs[:, 1])  # right column, spans both rows

        elif self.mode == "phase":
            ax1 = self.fig.add_subplot(1, 3, 1)
            ax2 = self.fig.add_subplot(1, 3, 2)
            ax3 = self.fig.add_subplot(1, 3, 3)
            self.plot_axes = [ax1, ax2]
            self.time_course_ax = ax3
            
            # Create sliders
            self._create_sliders()
            
            # Create checkboxes for plot selection
            self._create_checkboxes()
            
            # Initial plot
            self._update_tc_plot()
                        
        self._create_sliders()

    def _create_checkboxes(self):
        """Create checkboxes for plot selection."""
        check_ax = plt.axes((0.88, 0.65, 0.10, 0.25))
        
        plot_labels = [f'Plot {i+1}: {pair[0]}-{pair[1]}' 
                      for i, pair in enumerate(self.plot_pairs)]
        check_visibility = [self.plot_visible[f'plot{i+1}'] 
                           for i in range(len(self.plot_pairs))]
        
        self.check_buttons = CheckButtons(check_ax, plot_labels, check_visibility)
        self.check_buttons.on_clicked(self._toggle_plot)
        
        # Update button
        update_button_ax = plt.axes((0.88, 0.58, 0.10, 0.04))
        self.update_button = Button(update_button_ax, 'Update Plots', 
                                    color='lightblue', hovercolor='skyblue')
        self.update_button.on_clicked(self._on_update_button)
    
    def run(self):
        # # Initial plot
        # if self.mode == "tc":
        #     self._update_tc_plot()
        # elif self.mode == "vtna":
        #     self._update_vtna_plot()
        # elif self.mode == "phase":
        #     self._update_phase_plot()
        self._update(val=42)
        plt.show()
    
    def _create_sliders(self):
        """Create sliders for rate constants and initial conditions."""
        num_reactions = self.mech_info['num_reactions']
        
        # Only create sliders for species with non-zero initial conditions
        num_initial_conds = len(self.slider_species)
        num_sliders = num_reactions + num_initial_conds
        
        slider_height = 0.02
        slider_spacing = 0.03
        slider_left = 0.12
        slider_width = 0.76
        bottom_start = 0.01 + (num_sliders * slider_spacing) + slider_spacing

        if num_reactions <= 2:
            bottom_start = 0.1
        elif num_reactions <= 4:
            bottom_start = 0.22

        # Rate constant sliders
        for i in range(1, num_reactions + 1):
            row = i - 1
            y_pos = bottom_start - (row * slider_spacing)
            ax = plt.axes((slider_left, y_pos, slider_width, slider_height))
            
            rxn = self.mech_info['reactions'][i-1]
            reactants = ' + '.join(rxn['reactants'])
            products = ' + '.join(rxn['products'])
            
            init_val = self.k_init.get(f'k{i}', 1.0)
            slider = Slider(ax, f'k{i}: {reactants}→{products}', 
                          0.0, 100, valinit=init_val, valstep=0.1)
            
            self.slider_dict[f'k{i}'] = slider
            self.slider_axes[f'k{i}'] = ax
            slider.on_changed(self._update)


        # Initial condition sliders (only for starting materials with non-zero initial values)
        for idx, species in enumerate(self.slider_species):
            row = num_reactions + idx
            y_pos = bottom_start - (row * slider_spacing)
            ax = plt.axes((slider_left, y_pos, slider_width, slider_height))
            
            init_val = self.initial_conditions.get(species, 1.0)
            
            # Use TextBox for catalyst concentration, Slider for others
            if species.lower() == 'cat':
                slider = Slider(ax, f'[{species}]₀', 0.0, 0.5, 
                              valinit=init_val, valstep=0.001)
                slider.on_changed(self._update)
                self.slider_dict[f'{species}_0'] = slider
                self.slider_axes[f'{species}_0'] = ax
            else:
                slider = Slider(ax, f'[{species}]₀', 0.0, 2.0, 
                              valinit=init_val, valstep=0.1)
                slider.on_changed(self._update)
                self.slider_dict[f'{species}_0'] = slider
                self.slider_axes[f'{species}_0'] = ax
    
    def _toggle_plot(self, label):
        """Toggle plot visibility."""
        # Extract plot number from label
        plot_num = int(label.split(':')[0].split()[1])
        plot_key = f'plot{plot_num}'
        
        visible_count = sum(self.plot_visible.values())
        
        # Prevent enabling if already at limit
        if not self.plot_visible[plot_key] and visible_count >= 2:
            return
        
        self.plot_visible[plot_key] = not self.plot_visible[plot_key]
    
    def _on_update_button(self, event):
        """Handle update button click."""
        # Enforce 2-plot limit
        visible_count = sum(self.plot_visible.values())
        if visible_count > 2:
            count = 0
            for i in range(len(self.plot_pairs)):
                key = f'plot{i+1}'
                if self.plot_visible[key]:
                    count += 1
                    if count > 2:
                        self.plot_visible[key] = False
        
        self._update_tc_plot()
    
    def _update(self, val):
        """Callback for slider changes."""
        if self.mode == "tc":
            self._update_tc_plot()
        elif self.mode == "vtna":
            self._update_vtna_plot()
        elif self.mode == "phase":
            self._update_phase_plot()
    
    def _update_textbox(self, text):
        """Callback for textbox changes."""
        self._update_phase_plot()
    
    def find_stall_point(self, arr, t, f=1.1):     
        arr /= arr.max()
        time_index = np.where(arr >= (0.95) )[0]
        t_max = t[time_index[0]] * f
        return t_max
        
    def _update_tc_plot(self):
        """Update the phase portrait plots."""
        # Build k_values dict
        k_values = {}
        for i in range(1, self.mech_info['num_reactions'] + 1):
            k_values[f'k{i}'] = self.slider_dict[f'k{i}'].val
        
        # Build initial conditions
        conc_state = []
        for species in self.dynamic_species:
            # Get value from slider/textbox if it exists, otherwise use 0 (for intermediates)
            if f'{species}_0' in self.slider_dict:
                widget = self.slider_dict[f'{species}_0']
                # Handle both Slider and TextBox widgets
                if isinstance(widget, TextBox):
                    try:
                        val = float(widget.text)
                    except ValueError:
                        val = 0.0  # Default to 0 if text is invalid
                else:
                    val = widget.val
            else:
                val = 0.0  # Intermediates start at zero
            conc_state.append(val)
        
        # Add conserved species values to k_values for conservation equations
        for key, val in self.initial_conditions.items():
            if key not in self.dynamic_species:
                k_values[key] = self.slider_dict[f'{key}_0'].val if f'{key}_0' in self.slider_dict else val
        
        # find max time
        t = np.linspace(0, 2_000_000, 1_000_001)
        solution = odeint(self.ode_func, conc_state, t, args=(k_values,))
        P_ind = self.dynamic_species.index("P")
        # P = solution[:, P_ind]
        self.t_max = self.find_stall_point(arr=solution[:, P_ind], t=t)
        
        # Solve ODE
        t = np.linspace(0, self.t_max, 1000)
        solution = odeint(self.ode_func, conc_state, t, args=(k_values,))
        
        # Create solution dictionary
        sol_dict = {}
        for i, species in enumerate(self.dynamic_species):
            sol_dict[species] = solution[:, i]
            
        # Update Time Course Plot
        self.time_course_ax.clear()
        self.time_course_ax.set_title('Concentration vs Time', fontsize=11, fontweight='bold')
        self.time_course_ax.set_xlabel('Time (t)', fontsize=10, fontweight='bold')
        self.time_course_ax.set_ylabel('Concentration', fontsize=10, fontweight='bold')
        self.time_course_ax.grid(True, alpha=0.3)
        
        # Plot each dynamic species
        # for i, species in enumerate(self.dynamic_species):
        #     self.time_course_ax.plot(t, solution[:, i], label=f'[{species}]', linewidth=2, alpha=0.8)
        for species in sol_dict:
            if "cat" in species or species=="time":
                continue
            species_ind = self.dynamic_species.index(species)
            self.time_course_ax.plot(t, solution[:, species_ind], label=f'[{species}]_1', linewidth=3, alpha=0.8)#, marker="o", markersize=2)
            
        self.time_course_ax.legend(loc='upper right', fontsize=9, framealpha=0.9)
        self.time_course_ax.set_xlim(0, self.t_max)
        self.time_course_ax.set_ylim(bottom=0)
        
        
        # Update title
        k_str = ", ".join([f"k{i}={k_values.get(f'k{i}', 0.0):.3f}" 
                          for i in range(1, self.mech_info['num_reactions'] + 1)])
        plt.suptitle(f'Phase Portrait Analysis | {k_str}', 
                    fontsize=10, fontweight='bold')
        
        if self.fig is not None:
            self.fig.canvas.draw_idle()

    def _update_phase_plot(self):
        """Update the phase portrait plots."""
        # Build k_values dict
        k_values = {}
        for i in range(1, self.mech_info['num_reactions'] + 1):
            k_values[f'k{i}'] = self.slider_dict[f'k{i}'].val
        
        # Build initial conditions
        initial_state = []
        ic_dict = {}
        for species in self.dynamic_species:
            # Get value from slider/textbox if it exists, otherwise use 0 (for intermediates)
            if f'{species}_0' in self.slider_dict:
                widget = self.slider_dict[f'{species}_0']
                # Handle both Slider and TextBox widgets
                if isinstance(widget, TextBox):
                    try:
                        val = float(widget.text)
                    except ValueError:
                        val = 0.0  # Default to 0 if text is invalid
                else:
                    val = widget.val
            else:
                val = 0.0  # Intermediates start at zero
            initial_state.append(val)
            ic_dict[species] = val
        
        # Add conserved species values to k_values for conservation equations
        for key, val in self.initial_conditions.items():
            if key not in self.dynamic_species:
                k_values[key] = self.slider_dict[f'{key}_0'].val if f'{key}_0' in self.slider_dict else val
        
        # find max time
        t = np.linspace(0, 1_000_000, 1_000_001)
        solution = odeint(self.ode_func, initial_state, t, args=(k_values,))
        P_ind = self.dynamic_species.index("P")
        # P = solution[:, P_ind]
        self.t_max = self.find_stall_point(arr=solution[:, P_ind], t=t)

        # Solve ODE
        t = np.linspace(0, self.t_max, 1000)
        solution = odeint(self.ode_func, initial_state, t, args=(k_values,))
        
        # Create solution dictionary
        sol_dict = {}
        for i, species in enumerate(self.dynamic_species):
            sol_dict[species] = solution[:, i]
            
        # Update Time Course Plot
        self.time_course_ax.clear()
        self.time_course_ax.set_title('Concentration vs Time', fontsize=11, fontweight='bold')
        self.time_course_ax.set_xlabel('Time (t)', fontsize=10, fontweight='bold')
        self.time_course_ax.set_ylabel('Concentration', fontsize=10, fontweight='bold')
        self.time_course_ax.grid(True, alpha=0.3)
        
        # Plot each dynamic species
        for i, species in enumerate(self.dynamic_species):
            self.time_course_ax.plot(t, solution[:, i], label=f'[{species}]', linewidth=2, alpha=0.8, marker="o")
            
        self.time_course_ax.legend(loc='upper right', fontsize=9, framealpha=0.9)
        self.time_course_ax.set_xlim(0, self.t_max)
        self.time_course_ax.set_ylim(bottom=0)
        
        # Get visible plots
        visible_plots = [i for i, key in enumerate([f'plot{i+1}' for i in range(len(self.plot_pairs))])
                        if self.plot_visible[key]][:2]
        
        # Clear all axes
        for ax in self.plot_axes:
            ax.clear()
            ax.set_visible(False)
        
        # Draw visible plots
        for idx, plot_idx in enumerate(visible_plots):
            if idx >= len(self.plot_axes):
                break
            
            ax = self.plot_axes[idx]
            ax.set_visible(True)
            
            x_species, y_species = self.plot_pairs[plot_idx]
            
            # Calculate dynamic axis limits based on trajectory data
            x_data = sol_dict.get(x_species, np.array([0]))
            y_data = sol_dict.get(y_species, np.array([0]))
            
            # Get max values from trajectory and scale by 1.1 with minimum fallback
            x_max_data = x_data.max() if len(x_data) > 0 else 0.0
            y_max_data = y_data.max() if len(y_data) > 0 else 0.0
            
            # Set minimum axis range if data is all zeros or very small
            x_max = max(x_max_data * 1.1, 0.001)
            y_max = max(y_max_data * 1.1, 0.001)
            
            # Create vector field
            x_range = np.linspace(0, x_max, 12)
            y_range = np.linspace(0, y_max, 12)
            
            # Build fixed values for other species
            fixed_values = {}
            for species in self.mech_info['species']:
                if species not in [x_species, y_species] and species not in self.conserved_species:
                    # Use mid-range value for fixed species
                    fixed_values[species] = ic_dict.get(species, 1.0) * 0.5
            
            dX, dY, magnitude = PhasePortraitPlotter.create_vector_field(
                x_range, y_range, x_species, y_species,
                self.mech_info, k_values, fixed_values, self.conserved_species
            )
            
            # Normalize vectors and plot
            X, Y = np.meshgrid(x_range, y_range)
            ax.quiver(X, Y, dX/magnitude, dY/magnitude, magnitude,
                     cmap='coolwarm', alpha=0.6, scale=35, width=0.003)
            
            # Plot trajectory
            if x_species in sol_dict and y_species in sol_dict:
                # Create gradient color trajectory from green to grey to red
                points = np.array([sol_dict[x_species], sol_dict[y_species]]).T
                segments = [[[points[i, 0], points[i, 1]], [points[i+1, 0], points[i+1, 1]]] 
                           for i in range(len(points)-1)]
                
                # Create color map: green -> grey -> red
                cmap = LinearSegmentedColormap.from_list('trajectory', 
                                                         ['green', 'grey', 'red'])
                
                # Create line collection with gradient
                lc = LineCollection(segments, cmap=cmap, linewidth=2.5, alpha=0.9)
                lc.set_array(np.linspace(0, 1, len(segments)))
                ax.add_collection(lc)
                
                # Plot start and end markers
                ax.scatter(sol_dict[x_species][0], sol_dict[y_species][0],
                          color='green', s=100, marker='o', 
                          edgecolors='black', linewidth=2, zorder=5)
                ax.scatter(sol_dict[x_species][-1], sol_dict[y_species][-1],
                          color='red', s=100, marker='X',
                          edgecolors='black', linewidth=2, zorder=5)
            
            # Labels and formatting with dynamic limits
            ax.set_xlabel(f'[{x_species}]', fontsize=10, fontweight='bold')
            ax.set_ylabel(f'[{y_species}]', fontsize=10, fontweight='bold')
            ax.set_title(f'{x_species} vs {y_species}', fontsize=11, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.set_xlim(0, x_max)
            ax.set_ylim(0, y_max)
        
        # Update title
        k_str = ", ".join([f"k{i}={k_values.get(f'k{i}', 0.0):.3f}" 
                          for i in range(1, self.mech_info['num_reactions'] + 1)])
        plt.suptitle(f'Phase Portrait Analysis | {k_str}', 
                    fontsize=10, fontweight='bold')
        
        if self.fig is not None:
            self.fig.canvas.draw_idle()

    def _update_vtna_plot(self):
        """Update the phase portrait plots."""
        # Build k_values dict
        k_values = {}
        for i in range(1, self.mech_info['num_reactions'] + 1):
            k_values[f'k{i}'] = self.slider_dict[f'k{i}'].val
        
        # Build initial conditions
        conc_state = []
        for species in self.dynamic_species:
            # Get value from slider/textbox if it exists, otherwise use 0 (for intermediates)
            if f'{species}_0' in self.slider_dict:
                widget = self.slider_dict[f'{species}_0']
                # Handle both Slider and TextBox widgets
                if isinstance(widget, TextBox):
                    try:
                        val = float(widget.text)
                    except ValueError:
                        val = 0.0  # Default to 0 if text is invalid
                else:
                    val = widget.val
            else:
                val = 0.0  # Intermediates start at zero
            conc_state.append(val)
        
        cat_id = self.dynamic_species.index("cat")
        conc_state2 = conc_state.copy()
        conc_state2[cat_id] *= 2

        # Add conserved species values to k_values for conservation equations
        for key, val in self.initial_conditions.items():
            if key not in self.dynamic_species:
                k_values[key] = self.slider_dict[f'{key}_0'].val if f'{key}_0' in self.slider_dict else val
        
        # end for 1st rct
        t = np.linspace(0, 2_000_000, 1_000_001)
        solution = odeint(self.ode_func, conc_state, t, args=(k_values,))
        P_ind = self.dynamic_species.index("P")
        self.t_max = self.find_stall_point(arr=solution[:, P_ind], t=t)


        t1 = np.linspace(0, self.t_max, 1000)
        solution1 = odeint(self.ode_func, conc_state, t1, args=(k_values,))
        df1 = pd.DataFrame()
        for i, species in enumerate(self.dynamic_species):
            df1[species] = np.concatenate([
                                solution1[:20:2, i],
                                solution1[20:400:10, i],    # first 400 points, every 10th
                                solution1[400:700:15, i], # next 300 points, every 15th
                                solution1[700:1001:30, i] # last 300 points, every 30th
                            ])
        df1["time"] = np.concatenate([
                        t1[:20:2],
                        t1[20:400:10],
                        t1[400:700:15],
                        t1[700:1001:30]
                    ])
        
        #! second tc
        solution = odeint(self.ode_func, conc_state2, t, args=(k_values,))
        P_ind = self.dynamic_species.index("P")
        t_max2 = self.find_stall_point(arr=solution[:, P_ind], t=t)
        print(f"{self.t_max = }, {t_max2 = }")

        t2 = np.linspace(0, t_max2, 1000)
        solution2 = odeint(self.ode_func, conc_state2, t2, args=(k_values,))
        df2 = pd.DataFrame()

        imax = solution1[:, P_ind].argmax()  # index of true peak
        print(f"{imax = }")
        indices = np.r_[0:20:2, 20:400:10, 400:700:15, 700:1000:30, imax]
        indices = np.unique(indices)


        for i, species in enumerate(self.dynamic_species):
            df2[species] = solution2[indices, i]

            # df2[species] = np.concatenate([
            #                     solution2[:20:2, i],
            #                     solution2[20:400:10, i],    # first 400 points, every 10th
            #                     solution2[400:700:15, i], # next 300 points, every 15th
            #                     solution2[700:1001:30, i] # last 300 points, every 30th
            #                 ])
            
        df2["time"] = t2[indices]
        # df2["time"] = np.concatenate([
        #                 t2[:20:2],
        #                 t2[20:400:10],
        #                 t2[400:700:15],
        #                 t2[700:1000:30]
        #             ])
        
        cols_to_sum = [c for c in df1.columns if c.startswith('cat') and not c.startswith('catI')] 
        df1["cat_abs"] = conc_state[cat_id]
        df1.to_csv("df1.csv", index=False)
        df2["cat_abs"] = conc_state2[cat_id]
        df2.to_csv("df2.csv", index=False)

        print(f"{df2['P'].max() = }, {df2['time'].max() = }")
        

        # Update Time Course Plot
        self.time_course_ax.clear()
        self.time_course_ax.set_title('Concentration vs Time', fontsize=11, fontweight='bold')
        self.time_course_ax.set_xlabel('Time (t)', fontsize=10, fontweight='bold')
        self.time_course_ax.set_ylabel('Concentration', fontsize=10, fontweight='bold')
        self.time_course_ax.grid(True, alpha=0.3)
        
        # Plot each dynamic species
        for species in df1.columns:
            if "cat" in species or species=="time":
                continue
            self.time_course_ax.plot(df1["time"], df1[species], label=f'[{species}]_1', linewidth=3, alpha=0.8, marker="o")#, marker="o", markersize=2)
            self.time_course_ax.plot(df2["time"], df2[species], label=f'[{species}]_2', linewidth=3, alpha=0.8, marker="o")#, marker="o", markersize=2)

        self.time_course_ax.legend(loc='upper right', fontsize=8, framealpha=0.9)
        self.time_course_ax.set_xlim(0, self.t_max)
        self.time_course_ax.set_ylim(bottom=0)
        
        # s = time.perf_counter()
        c_vtna = ClassicVTNA(df_rct1=df1, df_rct2=df2, species_col_name="cat_abs", product_col_name="P", time_col_name="time", min_order=-2, max_order=2)
        norm_ax1 = c_vtna.best_norm_x_axis1
        norm_ax2 = c_vtna.best_norm_x_axis2
        # print(f"vtna took {time.perf_counter() - s} s")

        self.vtna_ax.clear()
        self.vtna_ax.plot(norm_ax1, df1["P"], marker="o", label="P1", alpha=0.5)
        self.vtna_ax.plot(norm_ax2, df2["P"], marker="o", label="P2", alpha=0.5)
        self.vtna_ax.legend(prop={'size': 12})
        self.vtna_ax.set_title(f"Best cat order = {c_vtna.best_order}")


        #! for general overview
        self.cat_ax.clear()
        df1['cat_active'] = df1[cols_to_sum].sum(axis=1)
        df2['cat_active'] = df2[cols_to_sum].sum(axis=1)
        df1['cat_deact'] = df1["cat_abs"] - df1["cat_active"]
        df2['cat_deact'] = df2["cat_abs"] - df2["cat_active"]
        self.cat_ax.plot(df1["time"], df1["cat_active"], label="active catalyst 1", marker="o")
        self.cat_ax.plot(df2["time"], df2["cat_active"], label="active catalyst 2", marker="o")
        self.cat_ax.plot(df1["time"], df1["cat_deact"], label="deact catalyst 1", marker="o")
        self.cat_ax.plot(df2["time"], df2["cat_deact"], label="deact catalyst 2", marker="o")

        # #! for each species
        # for s in df1.columns:
        #     if not s.startswith("cat") or s == "cat_abs":
        #         continue
        #     self.cat_ax.plot(df1["time"], df1[s], label=f"{s} rct1", marker="o")
        #     self.cat_ax.plot(df2["time"], df2[s], label=f"{s} rct2", marker="o")
        self.cat_ax.legend(fontsize=8)


        axes = [self.time_course_ax, self.vtna_ax, self.cat_ax]
        with plt.style.context('seaborn-v0_8-whitegrid'):
            for ax in axes:
                # Add horizontal and vertical lines at y=0 and x=0
                ax.axhline(y=0, color='k')
                ax.axvline(x=0, color='k')

                # Enable and customize the grid
                ax.grid(True, linestyle='--')

                # Set tick label size
                ax.tick_params(axis='x', labelsize=10)
                ax.tick_params(axis='y', labelsize=10)

                # Make tick labels bold
                for label in ax.get_xticklabels():
                    label.set_fontweight('bold')
                for label in ax.get_yticklabels():
                    label.set_fontweight('bold')




        # Update title
        # k_str = ", ".join([f"k{i}={k_values.get(f'k{i}', 0.0):.3f}" 
        #                   for i in range(1, self.mech_info['num_reactions'] + 1)])
        # plt.suptitle(f'Phase Portrait Analysis | {k_str}', 
        #             fontsize=10, fontweight='bold')
        
        if self.fig is not None:
            self.fig.canvas.draw_idle()



if __name__ == "__main__":
    mechanism = [
        "A + cat = cat1",
        "cat1 + B = P + cat",
        "cat1 + A  = catI"
    ]
    
    initial_conditions = {
        "A": 1.0, 
        "B": 1.0,
        "cat": 0.01
    }
    
    conserved_species = {
        # Specify any conservation equations
        # Example:
        # 'E_free': 'E_total - ES'
    }
    
    k_init = {
        "k1": 1,
        "k2": 1,
        "k3": 1,
        "k4": 0,
        "k5": 10,
        "k6": 10
    }

    allowed_modes = ["vtna", "tc", "phase"]
    mode = "vtna"
    portrait = InteractiveTimeCourse(
        mechanism, initial_conditions, conserved_species, k_init, mode="vtna")
    portrait.run()

