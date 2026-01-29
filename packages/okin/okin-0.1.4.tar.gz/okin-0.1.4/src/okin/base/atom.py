from mendeleev import element
from okin.base.chem_logger import chem_logger

class Atom():
    def __init__(self, elem_):
        self.logger = chem_logger.getChild(self.__class__.__name__)
        try:
            self.info = element(elem_)
            self.label = self.info.symbol
        except Exception as e:
            self.logger.warning(f"{elem_} is not a valid element.")
            if str(e) == "No row was found when one was required":
                return None
            # since I cannot isolate this error I just raise it again
            else:
                self.info = element(elem_)
            self.label = self.info.symbol

    def __repr__(self):
        return self.info.symbol



if __name__ == "__main__":
    x = Atom("Ag")
    print(x.info.atomic_weight)

    #* properties of info:
    # ['abundance_crust', 'abundance_sea', 'annotation', 'atomic_number', 'atomic_radius', 'atomic_radius_rahm', 'atomic_volume',
    # 'atomic_weight', 'atomic_weight_uncertainty', 'block', 'boiling_point', 'c6', 'c6_gb', 'cas', 'covalent_radius', 'covalent_radius_bragg', 
    # 'covalent_radius_cordero', 'covalent_radius_pyykko', 'covalent_radius_pyykko_double', 'covalent_radius_pyykko_triple', 'cpk_color', 'density',
    #  'description', 'dipole_polarizability', 'dipole_polarizability_unc', 'discoverers', 'discovery_location', 'discovery_year', 'ec', 'econf',
    #  'electron_affinity', 'electronegativity', 'electronegativity_allen', 'electronegativity_allred_rochow', 'electronegativity_cottrell_sutton',
    #  'electronegativity_ghosh', 'electronegativity_gordy', 'electronegativity_li_xue', 'electronegativity_martynov_batsanov', 'electronegativity_mulliken',
    #  'electronegativity_nagle', 'electronegativity_pauling', 'electronegativity_sanderson', 'electronegativity_scales', 'electrons', 'electrophilicity',
    #  'en_allen', 'en_ghosh', 'en_pauling', 'evaporation_heat', 'fusion_heat', 'gas_basicity', 'geochemical_class', 'glawe_number', 'goldschmidt_class',
    #  'group', 'group_id', 'hardness', 'heat_of_formation', 'inchi', 'init_on_load', 'ionenergies', 'ionic_radii', 'is_monoisotopic', 'is_radioactive',
    #  'isotopes', 'jmol_color', 'lattice_constant', 'lattice_structure', 'mass', 'mass_number', 'mass_str', 'melting_point', 'mendeleev_number',
    #  'metadata', 'metallic_radius', 'metallic_radius_c12', 'molar_heat_capacity', 'molcas_gv_color', 'name', 'name_origin', 'neutrons', 'nist_webbook_url',
    #  'nvalence', 'oxidation_states', 'oxides', 'oxistates', 'period', 'pettifor_number', 'phase_transitions', 'proton_affinity', 'protons', 'registry',
    #  'sconst', 'screening_constants', 'series', 'softness', 'sources', 'specific_heat', 'specific_heat_capacity', 'symbol', 'thermal_conductivity',
    #  'uses', 'vdw_radius', 'vdw_radius_alvarez', 'vdw_radius_batsanov', 'vdw_radius_bondi', 'vdw_radius_dreiding', 'vdw_radius_mm3', 'vdw_radius_rt',
    #  'vdw_radius_truhlar', 'vdw_radius_uff', 'zeff']