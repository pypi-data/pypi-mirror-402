from okin.base.atom import Atom
import re

from okin.base.chem_logger import chem_logger


class Compound():
    DESCRIPTION = """
    This is not a database for compounds. It converts strings/dicts representing a compound into a Compound() instance.
    PhNMe2 is not seen as Dimethylaniline. It is just phnme2.
    """

    VALID_ELEMENTS = ['H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne', 'Na', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ar', 'K', 'Ca', 'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr', 'Rb', 'Sr', 'Y', 'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn', 'Sb', 'Te', 'I', 'Xe', 'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu', 'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg', 'Tl', 'Pb', 'Bi', 'Po', 'At', 'Rn', 'Fr', 'Ra', 'Ac', 'Th', 'Pa', 'U', 'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf', 'Es', 'Fm', 'Md', 'No', 'Lr', 'Rf', 'Db', 'Sg', 'Bh', 'Hs', 'Mt', 'Ds', 'Rg', 'Cn', 'Nh', 'Fl', 'Mc', 'Lv', 'Ts', 'Og']

    def __init__(self, sum_formula=None, sum_formula_dict=None, label=None):
        self.logger = chem_logger.getChild(self.__class__.__name__)
        self.block_pattern = re.compile("[A-Z][a-z]?[0-9]*")
        self.occurences_pattern = re.compile("[0-9]+")
        self.elem_pattern = re.compile("[A-Z][a-z]?")

        if not any([sum_formula, sum_formula_dict, label]):
            self.logger.error("Compound received 0 arguments")
            raise TypeError(
                "Compound needs excactly one identifier but 0 were given")

        if isinstance(sum_formula, dict):
            sum_formula = self.combine_sum_formula_dict(sum_formula)

        sum_formula = str(sum_formula)
        # print(f"now working on {sum_formula}")
        # The first argument that is not None is used for creation sum_formula > sum_formula_dict > label

        # self.logger.debug(f"The first argument that is not None is used for creation: sum_formula={sum_formula}, sum_formula_dict={sum_formula_dict}, label={label}")

        if sum_formula_dict:
            sum_formula_dict = self.link_atom_obj(sum_formula_dict)
            sum_formula = self.combine_sum_formula_dict(sum_formula_dict)

        # create all properties first and set them to None if it is not a valid sum_formula
        
        if self._is_valid_molecule(sum_formula):
            self.sum_formula = sum_formula
            self.sum_formula_dict = self.parse_sum_formula()
            self._molecular_weight = self._calc_moleculal_weight()
            # I made this line for fun. Dont hate me for it.
            self.compact_sum_formula = "".join(
                [f"{symbol}{str(info['occurences'])*bool(info['occurences']!=1)}" for symbol, info in self.sum_formula_dict.items()])

        else:
            self.sum_formula = None
            self.sum_formula_dict = {}
            self._molecular_weight = None
            self.compact_sum_formula = None

        self.label = label if label else sum_formula
        if self.label.startswith("(") and self.label.endswith(")"):
            self.label = self.label[1:-1]

        # self.logger.debug(f"{self.sum_formula=} | is_valid_molecule={self._is_valid_molecule(self.sum_formula)} that was initialized with {self.label=}")

    def _calc_moleculal_weight(self):
        molecular_weight = 0
        for val in self.sum_formula_dict.values():
            occurences = val["occurences"]
            weight = val["atom_obj"].info.atomic_weight
            molecular_weight += weight * occurences
        return molecular_weight

    @property
    def molecular_weight(self):
        return self._molecular_weight

    @molecular_weight.setter
    def molecular_weight(self, weight):
        self._molecular_weight = weight

    def link_atom_obj(self, sum_formula_dict):
        for symbol, occurences in sum_formula_dict.items():
            atom_obj = Atom(symbol)
            sum_formula_dict[symbol] = {'occurences': occurences, "atom_obj": atom_obj}
        return sum_formula_dict

    def _is_valid_molecule(self, sum_formula):
        if not sum_formula:
            return False

        # One block = e.g. 'H6' or "Pb2"
        blocks = self.block_pattern.findall(sum_formula)

        for b in blocks:
            # get 2 from Pb2 and set to 1 if just C
            occurences = [
                nr for nr in self.occurences_pattern.findall(b) if nr]
            if occurences:
                occurences = int(occurences[0])
            else:
                occurences = 1

            elem = self.elem_pattern.findall(b)[0]

            if elem not in self.VALID_ELEMENTS:
                self.molecular_weight = None
                return False

        return True

    def parse_sum_formula(self):
        # if it hits this method it is a valid sum_formula
        # dict should be filled with mendeleev elements
        sum_formula_dict = dict()

        # One block = e.g. 'H6' or "Pb2"
        blocks = self.block_pattern.findall(self.sum_formula)

        for b in blocks:
            occurences = [
                nr for nr in self.occurences_pattern.findall(b) if nr]
            if occurences:
                try:
                    occurences = int(occurences[0])
                except:
                    self.logger.debug(f"{b=}, {occurences=}")
                    pass
            else:
                occurences = 1

            elem = self.elem_pattern.findall(b)[0]

            if elem not in sum_formula_dict.keys():
                sum_formula_dict[elem] = occurences
            else:
                sum_formula_dict[elem] += occurences

        return self.link_atom_obj(sum_formula_dict)

    def combine_sum_formula_dict(self, sum_formula_dict):
        # delete Hydrogen from sum_formula if there are none
        if "H" in sum_formula_dict.keys():
            if sum_formula_dict["H"] == 0:
                del sum_formula_dict["H"]

        str_sum_formula = ""
        for key, value in sorted(sum_formula_dict.items()):
            # charge should be last thing to be added so just store value and add after loop
            if key == "charge":
                charge = value
                continue

            str_sum_formula += str(key)
            if value != 1:
                str_sum_formula += str(value)

        if "charge" in sum_formula_dict.keys():
            if charge != 0:
                # another beauty of python to add sign to charge
                str_sum_formula += f"{{{'{0:+}'.format(charge)}}}"

        return str_sum_formula

    def __repr__(self) -> str:
        return self.sum_formula if self.sum_formula else self.label


if __name__ == "__main__":
    x = Compound(sum_formula="PhNMe2")
    print(x.molecular_weight)
    print(x.sum_formula)
    # print(x.sum_formula_dict["C"]["atom_obj"].info.atomic_weight)
    print(x.label)
    print(x.compact_sum_formula)
