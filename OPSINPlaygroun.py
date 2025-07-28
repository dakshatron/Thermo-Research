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

withIUPACdataframe.insert(0, 'ID', range(1, len(withIUPACdataframe) + 1))

# Select all kinetic columns at once, then apply axis=1
kinetic_columns = ['Pre-Exp Factor Coeff', 'Pre-Exp Factor Power', 'Activation Energy']
completeKineticMask = withIUPACdataframe[kinetic_columns].notna().all(axis=1)
filteredDataframe = withIUPACdataframe[completeKineticMask].copy()


for rowIndex, rowContents in filteredDataframe['Reactant 1'].items():
    letters = regex.findall(r'[A-Za-z]', rowContents)
    lowercaseLetters = regex.findall(r'[a-z]', rowContents)

    if len(letters) == 0 or len(lowercaseLetters) == 0:
        continue

    ratio = len(lowercaseLetters) / len(letters)
    if ratio < 0.5:
        continue
    if ratio == 0.5 or ratio > 0.5:
        conversionStats['attempted'] += 1
        try:
            smiles = opsin.to_smiles(rowContents)
            filteredDataframe.loc[rowIndex, 'Reactant 1'] = smiles
            convertedRowsList.append(rowIndex)
            conversionStats['successful'] += 1
        except Exception as e:
            conversionStats['failed'] += 1

for rowIndex, rowContents in filteredDataframe['Reactant 2'].items():
    letters = regex.findall(r'[A-Za-z]', rowContents)
    lowercaseLetters = regex.findall(r'[a-z]', rowContents)

    if len(letters) == 0 or len(lowercaseLetters) == 0:
        continue

    ratio = len(lowercaseLetters) / len(letters)
    if ratio < 0.5:
        continue
    if ratio == 0.5 or ratio > 0.5:
        conversionStats['attempted'] += 1
        try:
            smiles = opsin.to_smiles(rowContents)
            filteredDataframe.loc[rowIndex, 'Reactant 1'] = smiles
            convertedRowsList.append(rowIndex)
            conversionStats['successful'] += 1
        except Exception as e:
            conversionStats['failed'] += 1

convertedDataframe = filteredDataframe.loc[convertedRowsList]

convertedDataframe.to_csv('converted.csv', index=False)