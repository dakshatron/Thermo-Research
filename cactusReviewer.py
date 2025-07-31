import pandas
import numpy as np
import typing
import pubchempy



cactusDataframe = pandas.read_csv('cactus.csv')

columns2process = ['Reactant 1', 'Reactant 2', 'Reactant 3', 'Product 1', 'Product 2', 'Product 3']

def cactusURLchecker(cellContents: str) -> bool:
    if pandas.isna(cellContents):
        return True
    elif isinstance(cellContents, str):
        if cellContents.startswith('https://cactus.nci.nih.gov/chemical/structure/'):
            return True
        elif cellContents in ['[None]', '', 'nan', 'NaN']:
            return True
        else:
            return False
    else:
        return False
    
filteredCactusDataframe = cactusDataframe[cactusDataframe[columns2process].apply(lambda row: all(cactusURLchecker(x) for x in row), axis=1)]
filteredCactusDataframe.to_csv('Processed Cactus.csv', index=False)

print("Successfully converted")
