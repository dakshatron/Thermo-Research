# import pandas
import cirpy

# dataframe = pandas.read_csv('Filtered NIST Extracted.csv')

# for rowIndex, rowContents in dataframe.iterrows():
#     for colIndex, cellContents in enumerate(rowContents):
#         if isinstance(cellContents, str):
#             dataframe.iat[rowIndex, colIndex] = cellContents.replace("â‰¡", "#")

# dataframe.to_csv('Filtered NIST Extracted.csv')



smiles = cirpy.resolve("1,1-dimethylethyl 4-fluorophenyldisulfide", "smi")
print(smiles)

from pyopsin import PyOpsin as opsin

opsinObj = opsin()

smiles = opsinObj.to_smiles("Fe(CO)3(Î·2-CH3CH=CH2)")