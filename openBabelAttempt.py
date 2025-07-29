import pybel

mol = pybel.readstring("smi", "CCl3OBr")
mol.write("smi").strip()
print(mol)