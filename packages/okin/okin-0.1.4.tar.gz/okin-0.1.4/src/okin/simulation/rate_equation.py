import sympy as sp
from sympy.printing.preview import preview
from okin.base.reaction import TEReaction
from okin.base.chem_logger import chem_logger

# every compound inside of the catalytic cycle has to be numbered cat<numbers_in_order> 
# e.g. cat1 has to be the first intermediate that shows up
# every compound outside of the catalytic cylcle needs to have another format (whatever you like)
# the product has to be named P

#TODO check if it works with non-linear reaction mechanisms

class RateEquation():
    def __init__(self, reactions, show_used_reactions=False, show_steady_states=False):
        self.logger = chem_logger.getChild(self.__class__.__name__)

        self.log_string = ""
        self.debug_string = ""
        if isinstance(reactions[0], str):
            reactions = [TEReaction(reaction_string=r, id_=i+1) for i, r in enumerate(reactions)]    
        self.reactions = reactions
        self.logger.info(f"reactions = {self.reactions[0].products}")
        
        
        if show_used_reactions:
            self.log_string += "Used reactions:\n"
            for rct in self.reactions:
                self.log_string += f"{rct}\n"
                # print(rct)
      
        self.nr_cat_outside_ss = 0
        
        self.parse_backwards_reactions()
        self.find_all_chems()
        self.find_mass_balance()
        self.add_k_to_reactions()

        self.steady_state_list = []
        
        for cat_species in self.mass_balance_set:
            # add space for clear identification and not just match "cat" with everything
            if len(cat_species) > 3:
                # this only gets steady-state for intermediates inside the cycle and not for inhibited products like catI
                if cat_species[3:].isdigit():
                    steady_state = self.find_steady_state(cat_species)
                    self.logger.debug(f"cat_species: {cat_species} has steady_state: {steady_state}")
                    
                    self.steady_state_list.append(steady_state)

        self.find_rate_law()
        self.logger.debug(f"rate_law: {self.rate_law}")

        if show_steady_states:
            # print("Used steady states")
            self.log_string += "\nUsed steady states\n"
            for intermediate_nr, ss in enumerate(self.steady_state_list):
                # print(f"d[cat{intermediate_nr+1}]/dt = {ss}")
                self.log_string += f"d[cat{intermediate_nr+1}]/dt = {ss}\n"
            
            # print(f"d[P]/dt = {self.rate_law}")
            self.log_string += f"d[P]/dt = {self.rate_law}\n"

        self.calculate_rate_eq()

        self.final_rate_law = sp.simplify(self.final_rate_law)
        self.latex_rate_law = sp.latex(self.final_rate_law)
        self.log_string += f"\nRate law as latex:\n{self.latex_rate_law}\n_______________________\n"

        self.logger.debug("\n")

    def find_all_chems(self):
        unique_chems = set()
        
        for rct in self.reactions:
            for chem_obj in (rct.educts + rct.products):
                chem = str(chem_obj)
                if chem.startswith("cat"):
                    continue
                unique_chems.add(chem)
        self.chems = list(unique_chems)

    def find_mass_balance(self) -> None:
        mass_balance_set = set()
        for rct in self.reactions:
            for species in (rct.educts + rct.products):
                if species.label.startswith("cat"):
                    
                    mass_balance_set.add(str(species))

        self.mass_balance_set = list(mass_balance_set)

        # gives cat number if there is a number
        def get_cat_nr(x):
            if len(x) >= 4:
                if x[3].isdigit():
                    return int(x[3])
                else:
                    self.nr_cat_outside_ss += 1
                    return 0
            else:
                self.nr_cat_outside_ss += 1
                return 0

        self.mass_balance_set.sort(key=get_cat_nr)
        
    def parse_backwards_reactions(self) -> None:
        new_rcts = []

        for i in range(len(self.reactions)):
            rct = self.reactions[i]
            print(f"Now parsing {rct}")
            if rct.drawn_arrow == "<==>" or rct.drawn_arrow == "<=>":
                forward_rct = TEReaction(educts=rct.educts, arrow_type="FullHead", products=rct.products, id_=str(rct.id_))
                backward_rct = TEReaction(educts=rct.products, arrow_type="FullHead", products=rct.educts, id_="-"+str(rct.id_))
                    
                new_rcts.append(forward_rct)
                new_rcts.append(backward_rct)

            # this else statement maintains order
            else:
                new_rcts.append(rct)

        self.reactions = new_rcts
        
    def add_k_to_reactions(self) -> None:
        prev_id = 0
        k = 0
        
        for i in range(len(self.reactions)):
            rct = self.reactions[i]
            
            # if it is backwards rct do not increment k
            if not abs(int(rct.id_)) == abs(prev_id):
                k += 1

            # make k_-1  for backwards reactions
            if int(rct.id_) > 0:
                k_sign = ""
            else:
                k_sign = "N"

            # rct.educts.append(CDText(f"k{k_sign}{str(k)}"))
            rct.educts.append(f"k{k_sign}{str(k)}")
            prev_id = int(rct.id_)

    def find_rate_law(self):
        rate_law = ""

        for rct in self.reactions:
            for educt_obj in rct.educts:
                educt = str(educt_obj).strip()
            
                # for rate law
                if "P" == educt:
                    rate_law += " - "
                    rate_law += "*".join([str(educt_obj) for educt_obj in rct.educts])

            for product_obj in rct.products:
                product = str(product_obj).strip()
                # for rate law
                if "P" == product:
                    rate_law += " + "
                    rate_law += "*".join([str(educt_obj) for educt_obj in rct.educts])


        self.rate_law = rate_law[3:]
                                         
    def find_steady_state(self, cat_species):
        # print(f"Now finding ss for {cat_species}")

        steady_state = ""

        for rct in self.reactions:
            # you can do this in one loop and much prettier but I dont want to
            for educt_obj in rct.educts:
                educt = str(educt_obj)
                if cat_species == educt:          
                    steady_state += " - "
                    steady_state += "*".join([str(educt_obj) for educt_obj in rct.educts])

                

            for product_obj in rct.products:
                product = str(product_obj)
                if cat_species == product:
                    steady_state += " + "
                    steady_state += "*".join([str(educt_obj) for educt_obj in rct.educts])

        # delete leading " + "
        return steady_state[1:]
    
    def calculate_rate_eq(self) -> None:
        cat, cat_total = sp.symbols("cat cat_total")

        mass_balance = sp.sympify(" + ".join(self.mass_balance_set))-cat_total

        self.log_string += f"mass balance: (0 = {mass_balance})\n"

        cat_ = sp.solve(mass_balance, cat)[0]

        self.debug_string += f"Solved MassBalance cat = {cat_}\n\n"

        # sympify everything that is used and replace cat with mass balance everywhere
        for i in range(len(self.steady_state_list)):
            ss_ = sp.sympify(self.steady_state_list[i])
            ss = ss_.subs({cat: cat_})
            self.debug_string += f"now replacing ({cat}) for ({cat_}) in ({ss_})\nResulting in {ss}\n\n"
            self.steady_state_list[i] = ss

        self.rate_law = sp.sympify(self.rate_law).subs({cat: cat_})

        # important loop here
        for i in range(len(self.steady_state_list)-1):
            intermediate_to_solve_for = self.mass_balance_set[i + self.nr_cat_outside_ss]
            current_steady_state = self.steady_state_list[i]

            solved_steady_state = sp.solve(current_steady_state, intermediate_to_solve_for)[0]
            self.logger.debug(f"now replacing {intermediate_to_solve_for} in all steady_states with {solved_steady_state}\n")

            # replace the intermediate to solved for in all steady state equations yet to come            
            self.debug_string += "Starting to replace in all SS\n\n"
            for j in range(i+1, len(self.steady_state_list)): # this +1 only eliminates current ss which comes out to 0 always. (I HOPE. NOT SURE. #TODO MAKE SURE)
                print_helper = self.steady_state_list[j]
                self.steady_state_list[j] = sp.simplify(self.steady_state_list[j].subs({intermediate_to_solve_for: solved_steady_state}))
                self.debug_string += f"now replacing ({intermediate_to_solve_for}) in {print_helper} with ({solved_steady_state})\nResulting in {self.steady_state_list[j]}\n\n"
            self.debug_string += "END to replace in all SS\n\n"
                

        # do last calculation by "hand"
        last_steady_state_before_product = self.steady_state_list[-1]
        last_intermediate = self.mass_balance_set[-1]
        solved_equation = sp.solve(last_steady_state_before_product, last_intermediate)[0]
        final_rate_law = self.rate_law.subs({self.mass_balance_set[-1]: solved_equation})

        self.debug_string += f"now replacing ({last_intermediate}) with ({solved_equation}) in ({self.rate_law}) \nResulting in {final_rate_law}\n\n"

        # A*B*cat_total*k1*k2*k3/(A*B*k1*k3 + A*k1*k2 + A*k1*kN2 + B*k2*k3 + B*k3*kN1 + kN1*kN2)
        # A*B*cat_total*k1*k2*k3/(A*B*k1*k3 + A*k1*k2 + A*k1*kN2 + B*k2*k3 + B*k3*kN1 + kN1*kN2)

        #! here only formatting output no more math

        # if you move this down everything breaks.
        final_rate_law = sp.parse_expr(str(final_rate_law), {'kN1': sp.Symbol('k_{-1}'), "cat_total": sp.Symbol('cat_0'), 'kN2': sp.Symbol('k_{-2}'), 'kN3': sp.Symbol('k_{-3}'), 'kN4': sp.Symbol('k_{-4}'), 'kN5': sp.Symbol('k_{-5}'), 'kN6': sp.Symbol('k_{-6}'), 'kN7': sp.Symbol('k_{-7}'), 'kN8': sp.Symbol('k_{-8}')})

        k_list = ['k1', 'k2', 'k3', 'k4', 'k5', 'k6', 'k7', 'k8', 'k_{-1}', 'k_{-2}', 'k_{-3}', 'k_{-4}', 'k_{-5}', 'k_{-6}', 'k_{-7}', 'k_{-8}']

        for fac in final_rate_law.free_symbols:
            str_fac = str(fac)
            # print(final_rate_law.free_symbols)
            if str_fac not in k_list:
                a = sp.Symbol(f"[{str_fac}]")
                if "_" in str_fac:
                    pass
                else:
                    final_rate_law = final_rate_law.xreplace({fac:a})

        self.logger.debug(f"final_rate_law = {final_rate_law}")
        self.final_rate_law = sp.simplify(final_rate_law)

    def show_latex_rate_law(self, path=None):
        sp.init_printing()
        if path:
            preview(self.final_rate_law, viewer="file", filename=path)
        else:
            try:
                preview(self.final_rate_law)
            except RuntimeError:
                pass
            print("________________")
            print(self.final_rate_law)
            print("________________")


    def __repr__(self):
        return str(self.final_rate_law)

    def working_savety_calculate_rate_eq(self) -> None:
        #* I know version control should be done with git. But I have to look stuff up sometimes and dont want to roll back everytime.
        cat, cat_total = sp.symbols("cat cat_total")

        mass_balance = sp.sympify(" + ".join(self.mass_balance_set))-cat_total

        cat_ = sp.solve(mass_balance, cat)[0]


        # sympify everything that is used and replace cat with mass balance everywhere
        for i in range(len(self.steady_state_list)):
            ss = sp.sympify(self.steady_state_list[i])
            ss = ss.subs({cat: cat_})
            self.steady_state_list[i] = ss

        self.rate_law = sp.sympify(self.rate_law).subs({cat: cat_})


        new_ss = "cat1"
        for i in range(len(self.steady_state_list)):
            # intermediate has to be a non empty string so we get this instead of "if not intermediate:"
            intermediate = self.mass_balance_set[i + self.nr_cat_outside_ss]
            
            # #* why does this exist?
            # if intermediate == "0" :
            #     break

            # leave out steady state for "cat" since not needed
            curr_ss = self.steady_state_list[i]


            self.logger.debug(f"replace {intermediate} with {new_ss} in {curr_ss}")
            curr_ss = curr_ss.subs({intermediate: new_ss})
            new_ss = sp.solve(curr_ss, intermediate)[0]
            self.logger.debug(f"Result: {new_ss}")
            # keep track of this for easier rate law
            prev_intermediate = intermediate


        # print(prev_intermediate)
        # print(intermediate)
        # final_rate_law = self.rate_law.subs({prev_intermediate: new_ss})

        #! here only formatting output no more math

        # if you move this down everything breaks.
        final_rate_law = sp.parse_expr(str(final_rate_law), {'kN1': sp.Symbol('k_{-1}'), "cat_total": sp.Symbol('cat0'), 'kN2': sp.Symbol('k_{-2}'), 'kN3': sp.Symbol('k_{-3}'), 'kN4': sp.Symbol('k_{-4}'), 'kN5': sp.Symbol('k_{-5}'), 'kN6': sp.Symbol('k_{-6}'), 'kN7': sp.Symbol('k_{-7}'), 'kN8': sp.Symbol('k_{-8}')})



        k_list = ['k1', 'k2', 'k3', 'k4', 'k5', 'k6', 'k7', 'k8', 'k9', 'k_{-1}', 'k_{-2}', 'k_{-3}', 'k_{-4}', 'k_{-5}', 'k_{-6}', 'k_{-7}', 'k_{-8}', 'k_{-9}']


        for fac in final_rate_law.free_symbols:
            str_fac = str(fac)
            # print(final_rate_law.free_symbols)
            if str_fac not in k_list:
                a = sp.Symbol(f"[{str_fac}]")
                if "_" in str_fac:
                    pass
                else:
                    final_rate_law = final_rate_law.xreplace({fac:a})


        # print(final_rate_law)
        preview(final_rate_law)
        


def main() -> None:
    rcts = ["A + cat <=> cat1", "cat1 <=> cat2", "cat2 + B -> P + cat"]

    x = RateEquation(reactions=rcts, show_used_reactions=True, show_steady_states=True)
    
    x.show_latex_rate_law()

    print(x.debug_string)

if __name__ == "__main__":
    main()

    
