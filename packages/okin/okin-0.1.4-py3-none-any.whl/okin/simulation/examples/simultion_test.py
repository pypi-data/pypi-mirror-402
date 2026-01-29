from chem_sim.simulator import Simulator
# import matplotlib.pyplot as plt

def sim_test():
    # it does not matter what arrow representation is chosen as forward and backward reactions 
    # k-value are defined directly. 
    reactions = ["A+cat -> cat1", "cat1+B -> P + cat", "cat + I -> catI"]
    k_dict = {"k1":0.3, "kN1":0.05, "k2":0.8, "kN2":0, "k3":10000, "kN3":0}
    c_dict = {"A":1.0, "cat":0.06, "B":0.8, "I":0.015}

    sim1 = Simulator()
    sim1.setup(reactions, k_dict, c_dict)
    sim1.simulate(0, 200, 40, use_const_cat=True, selections=["time", "A", "P", "cat"])

    # sim1.result["cat"] = 0.05
    # plt.scatter(sim1.result["time"], sim1.result["A"])
    # plt.scatter(sim1.result["time"], sim1.result["P"])
    # plt.show()
    # sim1.result.to_csv("A10B08cat004_fast_deact.csv", index=False)


    c_dict = {"A":1.0, "cat":0.04, "B":0.8, "I":0.015}
    sim2 = Simulator()
    sim2.setup(reactions, k_dict, c_dict)
    sim2.simulate(0, 300, 40, use_const_cat=True, selections=["time", "A", "P", "cat"])
# 
#     sim2.result["cat"] = 0.03

    # plt.scatter(sim2.result["time"], sim2.result["A"])
    # plt.scatter(sim2.result["time"], sim2.result["P"])
    # plt.show()
    # sim2.result.to_csv("A10B08cat003_fast_deact.csv", index=False)

    from chem_kinetics.vtna import PointVTNA, ClassicVTNA

    c_vtna = ClassicVTNA(sim1.result, sim2.result, species_col_name="cat", product_col_name="P", time_col_name="time")
    c_vtna.show_plot()

    p_vtna = PointVTNA(sim2.result, sim1.result, species_col_name="cat", product_col_name="P", time_col_name="time")
    p_vtna.show_plot()

sim_test()