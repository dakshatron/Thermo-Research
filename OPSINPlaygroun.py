from pyopsin import PyOpsin
import pandas as pd  # dealing with weird lists and datatypes
import requests  # for fetching HTML from URLs
import regex  # HTML parser
import os  # checks if file exists
from typing import List, Dict, Optional, Tuple, Any, Union
import cirpy # for chemical name (eg. (CH_3)2(CH_2O_2)CC(O)CH_3) to SMILES conversion

# Create an OPSIN object
opsin = PyOpsin()

conversionStats = []
conversionStats = {'attempted': 0, 'successful': 0, 'failed': 0}

convertedDataframe = pd.DataFrame()

convertedRowsList = []

try:
    # Load the IUPAC data from a CSV file
    filteredDataframe = pd.read_csv('IUPAC Conversion Test.csv')
    print("IUPAC data loaded successfully.")
except FileNotFoundError:
    print("IUPAC data file not found. Please ensure 'checkpoint.csv' exists in the current directory.")

### Select all kinetic columns at once, then apply axis=1
# kineticColumns = ['Pre-Exp Factor Coeff', 'Pre-Exp Factor Power', 'Activation Energy']
# kineticDataMask = withIUPACdataframe[kineticColumns].notna().all(axis=1) # creates mask (true false matrix) true for rows with full data

# products_mask = (withIUPACdataframe['Product 1'].fillna('').str.lower() == 'products') & \
#                 (withIUPACdataframe['Product 2'].fillna('').str.strip() == '') & \
#                 (withIUPACdataframe['Product 3'].fillna('').str.strip() == '')

# finalMask = kineticDataMask & ~products_mask

# filteredDataframe.insert(0, 'ID', range(1, len(filteredDataframe) + 1)) # reset index after filtering
# filteredDataframe.to_csv('IUPAC Conversion Test.csv', index=False)
    
usefulRows = []
for rowIndex, rowContents in filteredDataframe.iterrows():
    columns2process = ['Reactant 1', 'Reactant 2', 'Reactant 3', 'Product 1', 'Product 2', 'Product 3']
    usefulBool = True

    for columnName in columns2process:
        reagent = rowContents[columnName]
        if isinstance(reagent, str):
            conversionStats['attempted'] += 1
            letters = regex.findall(r'[A-Za-z]', reagent)
            lowercaseLetters = regex.findall(r'[a-z]', reagent)
            

            if len(letters) == 0 or len(lowercaseLetters) == 0:
                usefulBool = False
                continue

            ratio = len(lowercaseLetters) / len(letters)
            # if ratio < 0.5:
            #     usefulBool = False
            #     conversionStats['failed'] += 1
            #     continue
            smiles = opsin.to_smiles(reagent)
            if smiles != None:
                conversionStats['successful'] += 1
                filteredDataframe.at[rowIndex, columnName] = smiles
            else:
                smiles = cirpy.resolve(reagent, 'smiles')
                if smiles != None:
                    conversionStats['successful'] += 1
                    filteredDataframe.at[rowIndex, columnName] = smiles
                else:
                    conversionStats['failed'] += 1
                    usefulBool = False
    if usefulBool is True:
        usefulRows.append(rowIndex) 
filteredDataframe = filteredDataframe.loc[usefulRows]
columns2process = ['Reactant 1', 'Reactant 2', 'Reactant 3', 'Product 1', 'Product 2', 'Product 3']

filteredDataframe = filteredDataframe[
    ~filteredDataframe[columns2process].astype(str).apply(
        lambda x: x.str.contains(r'\[None\]', na=False)
    ).any(axis=1)
]

filteredDataframe.to_csv('converted.csv', index=False)
print(f"Conversion statistics: {conversionStats}")