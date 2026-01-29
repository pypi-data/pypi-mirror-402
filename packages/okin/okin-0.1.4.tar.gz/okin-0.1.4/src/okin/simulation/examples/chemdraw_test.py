from chem_sim.cd_parser import CDParser

def chemdraw_extract_test(path):
    my_cd = CDParser(file_path=path, draw=True)
    my_rcts = my_cd.find_reactions()

    for rct in my_rcts:
        print(rct)

for path in ["./examples/a.cdxml", "./examples/b.cdxml"]:
    chemdraw_extract_test(path)