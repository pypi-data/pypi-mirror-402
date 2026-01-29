from okin.cd_parser.CDClasses.cd_fragment import CDFragment
from okin.base.compound import Compound
from mendeleev import element


class CDChem(CDFragment, Compound):
    def __init__(self, xml_fragment):
        CDFragment.__init__(self, "chem")

        self.xml_frag = xml_fragment

        self.id_ = CDFragment.get_attribute(self, xml_obj=self.xml_frag, attribute="id")

        original_bb = self.get_coordinates(self.xml_frag, "BoundingBox")
        self.bb = CDFragment.get_bigger_bb(self, original_bb)

        self._temp_sum_formula_dict = {"H": 0}
        self.get_chem_label_dict()
        Compound.__init__(self, self._temp_sum_formula_dict)

    def get_chem_label_dict(self):
        # get atom counts for sum formula
        atoms = self.xml_frag.findall("n")
        charge = 0

        for i in range(len(atoms)):
            self.bonds = self.xml_frag.findall("b")
            #? <Basic Idea>
                # create a list with all atoms at one point
                # mostly this is just one atom so the list has only one element
                # labels like "NO2" will have multiple atoms
                # iterate over the list of atoms and add all of them to the sumformula
            #? </Basic Idea>

            sub_atoms = [atoms[i]]
            starting_node = atoms[i]

            # if there is a label add all atoms to the sub_atoms list
            nested_frag = starting_node.find("fragment")
            if (nested_frag):
                sub_atoms = []
                for nested_atom in nested_frag:
                    if "NumHydrogens" in nested_atom.attrib:
                        sub_atoms.append(nested_atom)

            if "NodeType" in starting_node.attrib:
                if "Nickname" == starting_node.attrib["NodeType"] or "Fragment" == starting_node.attrib["NodeType"]:
                    sub_atoms = []
                    
                    nested_frag = starting_node.find("fragment")
                    nested_atoms = nested_frag.findall("n")[:-1]
                    nested_bonds = nested_frag.findall("b")
                    for s_atom in nested_atoms:
                        sub_atoms.append(s_atom)
                    # override bonds variable here and reassign each cycle
                    # it works. LOL!
                    self.bonds = nested_bonds 
            
            # this is the loop for one atom at a time
            for i in range(len(sub_atoms)):
                atom = sub_atoms[i]
                atom_symbol = self.get_atom_symbol(atom)
                num_H = self.calc_num_H(atom, atom_symbol)
                self.update_dict(atom_symbol, num_H)

                if "Charge" in atom.attrib:
                    charge += int(atom.attrib["Charge"])
        
        self._temp_sum_formula_dict["charge"] = charge

    def update_dict(self, item_to_add, num_H):
        if item_to_add in self._temp_sum_formula_dict.keys():
            self._temp_sum_formula_dict[item_to_add] += 1
        else:
            self._temp_sum_formula_dict[item_to_add] = 1

        self._temp_sum_formula_dict["H"] += num_H

    def get_atom_symbol(self, atom):
        atom_symbol = None
        if "NodeType" in atom.attrib:
            if atom.attrib["NodeType"] == "Unspecified":
                non_chem_label =  atom.find("t").find("s").text

            elif atom.attrib["NodeType"] == "GenericNickname":
                ss = atom.find("t").findall("s")
                non_chem_label = ""
                for s in ss:
                    non_chem_label += s.text

            return "(" + non_chem_label + ")"
            

        elif "NumHydrogens" in atom.attrib:
            # its not C find out which one it is
            # this try except is just in case sb types out CH3 groups...
            try:
                curr_elem = element(int(atom.attrib["Element"]))
                atom_symbol = curr_elem.symbol
            except:       
                if "GenericNickname" in atom.attrib:
                    # it is R in there or sth else that is not an element
                    atom_symbol = atom.attrib["GenericNickname"]
                else:
                    atom_symbol = "C"

        if atom_symbol == None:
            atom_symbol = "C"

        return atom_symbol

    def calc_num_H(self, atom, atom_symbol):

        if "NumHydrogens" in atom.attrib:
            num_H = int(atom.attrib["NumHydrogens"])

        elif atom_symbol == "C":
            C_id_ = self.get_attribute(atom, "id")
            # figure out H connected to C
            # num_H = (C*4 - bonds_on_C)
                            
            bonds_on_C = 0
            for bond in self.bonds:
                # B = beginning of bond
                # E = end of bond
                if bond.attrib["B"] == C_id_ or bond.attrib["E"] == C_id_:
                    if "Order" in bond.attrib:
                        bonds_on_C += int(bond.attrib["Order"])
                    else:
                        bonds_on_C += 1
            
            num_H = 4 - bonds_on_C
        
        else:
            num_H = 0  

        return num_H

