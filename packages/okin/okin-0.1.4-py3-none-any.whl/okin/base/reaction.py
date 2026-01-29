from okin.base.compound import Compound
from okin.base.atom import Atom
import re
from okin.base.chem_logger import chem_logger

class Reaction():
    def __init__(self, reaction_string=None, educts=None, arrow_type=None, products=None):
        self.logger = chem_logger.getChild(self.__class__.__name__)
        # # sometimes it needs an ID >:( !Does it tho?
        # if id_:
        #     self.id_ = str(id_)

        self.arrow_dict = {"Equilibrium": "<=>", "FullHead": "->", "HalfHead": "<==>", "line": "--"}

        if isinstance(reaction_string, str):
            self.parse_reaction_string(reaction_string)
            # if arrow_type given overrule the one present in string
            if arrow_type:
                self.drawn_arrow = arrow_type
        
            
        else:
            self.parse_components(educts, arrow_type, products) 
            
    def parse_reaction_string(self, reaction_string):
        for arrow in self.arrow_dict.values():
            if arrow in reaction_string:
                temp_educts, temp_products = reaction_string.split(arrow)
                # split after + if it is not followed by } since charges are written as Ca{2+}
                educts = [Compound(sum_formula=ed.strip()) for ed in re.split(r"\+(?!})", temp_educts)]
                products = [Compound(sum_formula=pr.strip()) for pr in re.split(r"\+(?!})", temp_products)]
                drawn_arrow = arrow

        self.educts = educts
        self.drawn_arrow = drawn_arrow
        self.products = products
 
    def parse_components(self, educts, arrow_type, products):
        temp_educts = []
        for ed in educts:
            if isinstance(ed, Atom) or isinstance(ed, Compound):
                temp_educts.append(ed)
            else:
                temp_educts.append(Compound(sum_formula=ed))

        temp_products = []
        for pr in products:
            if isinstance(pr, Atom) or isinstance(pr, Compound):
                temp_products.append(pr)
            else:
                temp_products.append(Compound(sum_formula=pr))

        if arrow_type in self.arrow_dict.keys():
            drawn_arrow = self.arrow_dict[arrow_type]
        elif arrow_type in self.arrow_dict.values():
            drawn_arrow = arrow_type
        else:
            print(f"The arrow type '{arrow_type}' is not implemented and will be set to 'FullHead' arrow (->)")
            drawn_arrow = "->"
            self.arrow_type = "FullHead"
        
        self.educts = temp_educts
        self.drawn_arrow = drawn_arrow
        self.products = temp_products

    def __repr__(self):
        str_educts = " + ".join([ed.label for ed in self.educts])
        str_products = " + ".join([prod.label for prod in self.products])
        str_rct = str_educts + " " + self.drawn_arrow + " " + str_products
        return str_rct


class TEReaction(Reaction):
    # def __init__(self, reaction_string=None, id_=None, k_forward=None, k_forward_name=None, k_backward=None, k_backward_name=None):
    def __init__(self, id_, reaction_string=None, k_forward=None, k_forward_name=None, k_backward=None, k_backward_name=None, educts=None, arrow_type=None, products=None):
        super().__init__(reaction_string=reaction_string, educts=educts, arrow_type=arrow_type, products=products)

        self.logger = chem_logger.getChild(self.__class__.__name__)
        self.logger.debug(f"id = {id_}: {reaction_string}")


        if id_ == 0:
            raise ValueError("id_ is 0. add 1. Reaction numbers should start at 1.") # sorry my programming friends. it is for the greater good.
        self.id_ = id_

        self.k_forward = k_forward
        self.k_backward = k_backward
        self.k_forward_name = k_forward_name if k_forward_name else f"k{id_}"
        self.k_backward_name = k_backward_name if k_backward_name else f"kN{id_}"

        self.name = f"J{self.id_}" # J is convention from Antimony string
        self.create_rate_eq()

    def create_rate_eq(self):
        rate_eq = self.k_forward_name

        for ed in self.educts:
            rate_eq += "*"
            rate_eq += str(ed)

        if self.k_backward_name:
            rate_eq += f"-{self.k_backward_name}*" 

            for pr in self.products:
                rate_eq += str(pr)
                rate_eq += "*"
        
        # if there are no products it cuts the last letter instead of the *
        if rate_eq.endswith("*"):
            rate_eq = rate_eq[:-1]

        self.rate_eq = rate_eq
 
    def __repr__(self):
        str_educts = " + ".join([str(ed.label) for ed in self.educts])
        str_products = " + ".join([str(prod.label) for prod in self.products])
        rct_str = str_educts.strip() + " " + self.drawn_arrow + " " + str_products.strip()
        return f"{self.name}: {rct_str}"


def str_to_te(m_steps):
    rcts = []
    if isinstance(m_steps, list):
        for i, m_step in enumerate(m_steps):
            rct = TEReaction(id_=i+1, reaction_string=m_step)
            rcts.append(rct)
        return rcts

    elif isinstance(m_steps, str):
        return TEReaction(id_=1, reaction_string=m_steps)
    


def main():
    x = Reaction(reaction_string="A + Ca{2+} -> B{+} + D")
    print(x.educts[1].sum_formula_dict["Ca"]["atom_obj"].info)

    x = "A + B -> C"
    my_rct = TEReaction(reaction_string=x, id_=1)
    print(my_rct)


if __name__ == "__main__":
    import logging
    chem_logger.setLevel(logging.DEBUG)
    main()
