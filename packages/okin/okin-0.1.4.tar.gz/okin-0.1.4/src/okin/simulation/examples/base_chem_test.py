from chem_base.atom import Atom
from chem_base.compound import Compound
from chem_base.reaction import Reaction, TEReaction

# for verbose output set to DEBUG
from chem_utils.chem_logger import chem_logger
import logging
chem_logger.setLevel(logging.INFO)


def atom_test():
    my_atom = Atom("F")
    print(my_atom.info.electronegativity())
    print(my_atom.info.cas)

    #* properties of info:
    #* ['abundance_crust', 'abundance_sea', 'annotation', 'atomic_number', 'atomic_radius', 'atomic_radius_rahm', 'atomic_volume', 'atomic_weight', 'atomic_weight_uncertainty', 'block', 'boiling_point', 'c6', 'c6_gb', 'cas', 'covalent_radius', 'covalent_radius_bragg', 'covalent_radius_cordero', 'covalent_radius_pyykko', 'covalent_radius_pyykko_double', 'covalent_radius_pyykko_triple', 'cpk_color', 'density', 'description', 'dipole_polarizability', 'dipole_polarizability_unc', 'discoverers', 'discovery_location', 'discovery_year', 'ec', 'econf', 'electron_affinity', 'electronegativity', 'electronegativity_allen', 'electronegativity_allred_rochow', 'electronegativity_cottrell_sutton', 'electronegativity_ghosh', 'electronegativity_gordy', 'electronegativity_li_my_cmpdue', 'electronegativity_martynov_batsanov', 'electronegativity_mulliken', 'electronegativity_nagle', 'electronegativity_pauling', 'electronegativity_sanderson', 'electronegativity_scales', 'electrons', 'electrophilicity', 'en_allen', 'en_ghosh', 'en_pauling', 'evaporation_heat', 'fusion_heat', 'gas_basicity', 'geochemical_class', 'glawe_number', 'goldschmidt_class', 'group', 'group_id', 'hardness', 'heat_of_formation', 'inchi', 'init_on_load', 'ionenergies', 'ionic_radii', 'is_monoisotopic', 'is_radioactive', 'isotopes', 'jmol_color', 'lattice_constant', 'lattice_structure', 'mass', 'mass_number', 'mass_str', 'melting_point', 'mendeleev_number', 'metadata', 'metallic_radius', 'metallic_radius_c12', 'molar_heat_capacity', 'molcas_gv_color', 'name', 'name_origin', 'neutrons', 'nist_webbook_url', 'nvalence', 'omy_cmpdidation_states', 'omy_cmpdides', 'omy_cmpdistates', 'period', 'pettifor_number', 'phase_transitions', 'proton_affinity', 'protons', 'registry', 'sconst', 'screening_constants', 'series', 'softness', 'sources', 'specific_heat', 'specific_heat_capacity', 'symbol', 'thermal_conductivity', 'uses', 'vdw_radius', 'vdw_radius_alvarez', 'vdw_radius_batsanov', 'vdw_radius_bondi', 'vdw_radius_dreiding', 'vdw_radius_mm3', 'vdw_radius_rt', 'vdw_radius_truhlar', 'vdw_radius_uff', 'zeff']

def compound_test():
    my_cmpd = Compound(sum_formula="H3CH2CC(O)OH", label="acetic acid")
    print(my_cmpd.molecular_weight)
    print(my_cmpd.sum_formula)
    print(my_cmpd.label)
    print(my_cmpd.compact_sum_formula)

    # individual atoms can be accessed in a compound 
    print(my_cmpd.sum_formula_dict["C"]["atom_obj"].info.atomic_weight)


def reaction_test():
    my_reaction_string = "3Zn + 2Fe{3+} -> 3Zn{2+} + 2Fe"
    my_rct = Reaction(reaction_string=my_reaction_string)
    print(my_rct)
    print(my_rct.educts)
    print(my_rct.products)

    #* every educt and product in the reaction is a Compound
    print(my_rct.educts[0].molecular_weight)

    #* Atoms inside compounds are recognized as Atoms and can be accessed as such
    print(my_rct.educts[1].sum_formula_dict["Fe"]["atom_obj"].info)

def te_reaction_test():
    my_reaction_string = "A + B -> C"
    my_rct = TEReaction(reaction_string=my_reaction_string, id_=1)
    print(my_rct)
    print(my_rct.educts, my_rct.products)
    print(my_rct.rate_eq)

    my_reaction_string2 = "D -> E + F"
    my_rct2 = TEReaction(reaction_string=my_reaction_string2, id_=4)
    print(my_rct2)
    print(my_rct2.educts, my_rct.products)
    print(my_rct2.rate_eq)

atom_test()
compound_test()
reaction_test()
te_reaction_test()
