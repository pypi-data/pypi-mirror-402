from chem_sim.rate_equation import RateEquation

def rate_eq_test():
    rcts = [
        "A + cat <=> cat1",
        "cat1 -> P + cat",
        ]

    # print(my_rcts)
    my_rate_eq = RateEquation(reactions=rcts, show_used_reactions=True, show_steady_states=True)
    my_rate_eq.show_latex_rate_law()
    print(my_rate_eq.debug_string)

rate_eq_test()