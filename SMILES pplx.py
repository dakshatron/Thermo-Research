import pandas
import requests
import regex
import os
from typing import List, Dict, Optional, Tuple, Any, Union 
from urllib.parse import quote

import cirpy
from pyopsin import PyOpsin as opsin

# --- Setup ---
conversionStats = {'attempted': 0, 'successful': 0, 'failed': 0}

rawDataframe = pandas.read_csv('Filtered NIST Extracted.csv')
processedDataframe = rawDataframe.copy()
cactusDataframe = rawDataframe.copy()
pubchemDataframe = rawDataframe.copy()

opsinObj = opsin()

# --- Functions ---
def IUPAC2SMILES(reagentParam: str, rowIndexParam: int, columnNameParam: str) -> bool:
    """
    Attempts to convert an IUPAC-like name to SMILES using OPSIN and CIRpy.
    Returns True on success, False on failure.
    """
    global processedDataframe, conversionStats
    try:
        # Attempt 1: OPSIN
        smiles = opsinObj.to_smiles(reagentParam)
        if smiles:
            conversionStats['successful'] += 1
            processedDataframe.at[rowIndexParam, columnNameParam] = smiles
            return True

        # Attempt 2: CIRpy
        smiles = cirpy.resolve(reagentParam, 'smiles')
        if smiles:
            conversionStats['successful'] += 1
            processedDataframe.at[rowIndexParam, columnNameParam] = smiles
            return True

        # Both failed
        conversionStats['failed'] += 1
        return False
    except Exception:
        conversionStats['failed'] += 1
        return False

def struct2SMILES(reagentParam: str, rowIndexParam: int, columnNameParam: str):
    """Generates URLs for structural formulas."""
    global cactusDataframe, pubchemDataframe
    cactusLink = f"https://cactus.nci.nih.gov/chemical/structure/{quote(reagentParam)}/smiles"
    cactusDataframe.at[rowIndexParam, columnNameParam] = cactusLink
    
    pubchemLink = f"https://pubchem.ncbi.nlm.nih.gov/compound/{quote(reagentParam)}"
    pubchemDataframe.at[rowIndexParam, columnNameParam] = pubchemLink

# --- Main Processing Loop ---

# Initialize lists to hold the indices of rows for each category
structural_formula_rows = []
successful_conversion_rows = []
failed_conversion_rows = []

# A single loop to process and classify each row
for rowIndex, rowContents in rawDataframe.iterrows():
    columns2process = ['Reactant 1', 'Reactant 2', 'Reactant 3', 'Product 1', 'Product 2', 'Product 3']
    
    # Flags to track the status of the entire row
    row_has_structural_formulas = False
    row_has_failed_conversions = False
    row_has_any_compounds = False
    
    for columnName in columns2process:
        reagent = rowContents[columnName]
        
        if not isinstance(reagent, str) or not reagent.strip():
            continue
        
        row_has_any_compounds = True
        letters = regex.findall(r'[A-Za-z]', reagent)
        
        if not letters:
            continue
            
        lowercaseLetters = regex.findall(r'[a-z]', reagent)
        ratio = len(lowercaseLetters) / len(letters)
        
        conversionStats['attempted'] += 1
        
        if ratio < 0.5:
            # This looks like a structural formula
            struct2SMILES(reagent, rowIndex, columnName)
            row_has_structural_formulas = True
        else:
            # This looks like an IUPAC name, attempt conversion
            if not IUPAC2SMILES(reagent, rowIndex, columnName):
                row_has_failed_conversions = True
    
    # Now, classify the row based on its overall status
    if not row_has_any_compounds:
        continue # Skip empty rows
    
    # Prioritized classification
    if row_has_structural_formulas:
        structural_formula_rows.append(rowIndex)
    elif row_has_failed_conversions:
        failed_conversion_rows.append(rowIndex)
    else:
        # Only if it has no structural formulas AND no failed conversions
        successful_conversion_rows.append(rowIndex)

# --- Final DataFrame Creation and Saving ---

# Use the collected indices to create the final, correctly filtered DataFrames
final_processed = processedDataframe.loc[successful_conversion_rows].copy()
final_cactus = cactusDataframe.loc[structural_formula_rows].copy()
final_pubchem = pubchemDataframe.loc[structural_formula_rows].copy()
# You can also create a DataFrame for failed rows if you want to inspect them
final_failed = rawDataframe.loc[failed_conversion_rows].copy()

# Save the results to separate files
final_processed.to_csv('processed.csv', index=False)
final_cactus.to_csv('cactus.csv', index=False)
final_pubchem.to_csv('pubchem.csv', index=False)
final_failed.to_csv('failed_conversions.csv', index=False)


# --- Diagnostic Output ---
print("="*40)
print("NIST Database Conversion Summary")
print("="*40)
print(f"Total Reactions Processed: {len(rawDataframe)}")
print(f"✅ Reactions with 100% Successful SMILES Conversions: {len(successful_conversion_rows)}")
print(f"   -> Saved to 'processed.csv'")
print(f"🔧 Reactions with Structural Formulas (for Selenium): {len(structural_formula_rows)}")
print(f"   -> URLs saved to 'cactus.csv' and 'pubchem.csv'")
print(f"❌ Reactions with Failed Conversions (for manual review): {len(failed_conversion_rows)}")
print(f"   -> Saved to 'failed_conversions.csv'")
print("-"*40)
print("Conversion Statistics:")
print(f"  Total conversion attempts: {conversionStats['attempted']}")
print(f"  Successful: {conversionStats['successful']}")
print(f"  Failed: {conversionStats['failed']}")
if conversionStats['attempted'] > 0:
    print(f"  Success Rate: {(conversionStats['successful'] / conversionStats['attempted'])*100:.1f}%")
print("="*40)

