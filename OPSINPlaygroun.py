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
    withIUPACdataframe = pd.read_csv('IUPAC Conversion Test.csv')
    print("IUPAC data loaded successfully.")
except FileNotFoundError:
    print("IUPAC data file not found. Please ensure 'checkpoint.csv' exists in the current directory.")

# Select all kinetic columns at once, then apply axis=1
kineticColumns = ['Pre-Exp Factor Coeff', 'Pre-Exp Factor Power', 'Activation Energy']
kineticDataMask = withIUPACdataframe[kineticColumns].notna().all(axis=1) # creates mask (true false matrix) true for rows with full data

products_mask = (withIUPACdataframe['Product 1'].fillna('').str.lower() == 'products') & \
                (withIUPACdataframe['Product 2'].fillna('').str.strip() == '') & \
                (withIUPACdataframe['Product 3'].fillna('').str.strip() == '')

finalMask = kineticDataMask & ~products_mask

filteredDataframe = withIUPACdataframe[finalMask].copy()
filteredDataframe.insert(0, 'ID', range(1, len(filteredDataframe) + 1)) # reset index after filtering
filteredDataframe.to_csv('IUPAC Conversion Test.csv', index=False)

# def iupac2smiles(iupac: str) -> Optional[str]:
#     """
#     Converts an IUPAC name to a SMILES string using OPSIN.
    
#     Args:
#         iupac (str): The IUPAC name to convert.
        
#     Returns:
#         Optional[str]: The SMILES string if conversion is successful, None otherwise.
#     """
#     letters = regex.findall(r'[A-Za-z]', rowContents)
#     lowercaseLetters = regex.findall(r'[a-z]', rowContents)

#     if len(letters) == 0 or len(lowercaseLetters) == 0:
#         continue
#     try:
#         smiles = opsin.to_smiles(iupac)
#         return smiles
#     except Exception as e:
#         return None
    


for rowIndex, rowContents in filteredDataframe.iterrows():
    reactant1 = rowContents['Reactant 1']
    reactant2 = rowContents['Reactant 2']
    reactant3 = rowContents['Reactant 3']
    
    product1 = rowContents['Product 1']
    product2 = rowContents['Product 2']
    product3 = rowContents['Product 3']

    reagents = [reactant1, reactant2, reactant3, product1, product2, product3]

    for reagent in reagents:
        if isinstance(reagent, str):
            letters = regex.findall(r'[A-Za-z]', reagent)
            lowercaseLetters = regex.findall(r'[a-z]', reagent)

            if len(letters) == 0 or len(lowercaseLetters) == 0:
                continue

            ratio = len(lowercaseLetters) / len(letters)
            if ratio < 0.5: # insert structural converter when developed here
                continue
            if ratio == 0.5 or ratio > 0.5:
                conversionStats['attempted'] += 1
                try:
                    smiles = opsin.to_smiles(reagent)
                    filteredDataframe.at[rowIndex, col] = smiles
                    convertedRowsList.append(rowIndex)
                    conversionStats['successful'] += 1
                except Exception as e:
                    conversionStats['failed'] += 1

convertedDataframe = filteredDataframe.loc[convertedRowsList]

convertedDataframe.to_csv('converted.csv', index=False)
print(f"Conversion statistics: {conversionStats}")