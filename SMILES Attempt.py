import pandas
import requests
import regex
import os
from typing import List, Dict, Optional, Tuple, Any, Union # allows specification of datatype 
from urllib.parse import quote

import cirpy
from pyopsin import PyOpsin as opsin

# allows access to live/dynamic HTML after pubchem page filled by Java (requests gets 'stale' HTML)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException

import time


# # sets up Selenium, this is all Chat idk, it just works lol
# myOptions = Options()
# # myOptions.add_argument("--headless") # I want to see it go to the page right now
# myOptions.add_argument("--no-sandbox")
# myOptions.add_argument("--disable-dev-shm-usage")
# myOptions.add_argument("--disable-gpu")
# myOptions.add_argument("--disable-extensions")

# # Network and automation options
# myOptions.add_argument("--remote-debugging-port=9222")
# myOptions.add_argument("--disable-background-networking")
# myOptions.add_argument("--disable-background-timer-throttling")
# myOptions.add_argument("--disable-renderer-backgrounding")
# myOptions.add_argument("--disable-backgrounding-occluded-windows")
# myOptions.add_argument("--remote-allow-origins=*")

# driver = webdriver.Chrome(options=myOptions)

conversionStats = {'attempted': 0, 'successful': 0, 'failed': 0} # dictionary I increment

rawDataframe = pandas.read_csv('Filtered NIST Extracted.csv')
processedDataframe = rawDataframe.copy()
cactusDataframe = rawDataframe.copy()
pubchemDataframe = rawDataframe.copy()
manualProcessingDataframe = rawDataframe.copy()

opsinObj = opsin()

def IUPAC2SMILES(reagentParam: str, rowIndexParam: int, columnNameParam: str) -> bool:
    """
    converts reagents in IUPAC form to SMILES, then replaces corresponding entry in csv

    useful rows save to 
    """
    global processedDataframe, manualProcessingDataframe, conversionStats
    try:
        smiles = opsinObj.to_smiles(reagentParam)
        if smiles != None:
            conversionStats['successful'] += 1
            processedDataframe.at[rowIndexParam, columnNameParam] = smiles
            return True
        # try cirpy as a fallback
        smiles = cirpy.resolve(reagentParam, 'smiles')
        if smiles!= None:
            conversionStats['successful'] += 1
            processedDataframe.at[rowIndexParam, columnNameParam] = smiles
            return True
        conversionStats['failed'] += 1
        return False
    except Exception as e:
        conversionStats['failed'] += 1
        return False

def struct2SMILES(reagentParam: str, rowIndexParam: int, columnNameParam: str):
    global cactusDataframe, pubchemDataframe
    # replaces entry with cactus.gov/reagentParam/smiles and pubchem/compound/reagent in two different pandas dataframes
    cactusLink = "https://cactus.nci.nih.gov/chemical/structure/" + quote(reagentParam) + "/smiles"
    cactusDataframe.at[rowIndexParam, columnNameParam] = cactusLink

    pubchemLink = "https://pubchem.ncbi.nlm.nih.gov/compound/" + quote(reagentParam)
    pubchemDataframe.at[rowIndexParam, columnNameParam] = pubchemLink

    return

relevantRows: list = []
for rowIndex, rowContents in rawDataframe.iterrows():
    columns2process = ['Reactant 1', 'Reactant 2', 'Reactant 3', 'Product 1', 'Product 2', 'Product 3']
    relevantRowBool = False

    for columnName in columns2process:
        reagent = str(rowContents[columnName])

        if not isinstance(reagent, str) or reagent.strip() == '': # skip if nothing there
            continue # onto next cell to the right
        
        letters = regex.findall(r'[A-Za-z]', reagent)
        lowercaseLetters = regex.findall(r'[a-z]', reagent)
        # simple, IUPAC names (eg. 2-methylpentante) have mostly lowercase letters, 
        # structural formulas have at most 1/2 lowercase letters (eg. AlBr)
        # so that's how I sort them
        conversionStats['attempted'] += 1

        if len(letters) == 0:
            continue
        ratio = len(lowercaseLetters) / len(letters)
        
        if ratio < 0.5:
            struct2SMILES(reagent, rowIndex, columnName)
            continue
        else:
            relevantRowBool = True
    if relevantRowBool:
        relevantRows.append(rowIndex)

pubchemDataframe = pubchemDataframe.loc[relevantRows]
cactusDataframe = cactusDataframe.loc[relevantRows]

pubchemDataframe.to_csv('pubchem.csv', index=False)
cactusDataframe.to_csv('cactus.csv', index=False)

processedRows: list = []
rawRows: list = []
for rowIndex, rowContents in rawDataframe.iterrows():
    columns2process = ['Reactant 1', 'Reactant 2', 'Reactant 3', 'Product 1', 'Product 2', 'Product 3']
    processedRowBool = False

    for columnName in columns2process:
        reagent = rowContents[columnName]

        if not isinstance(reagent, str) or reagent.strip() == '': # skip if nothing there
            continue # onto next cell to the right
        
        letters = regex.findall(r'[A-Za-z]', reagent)
        lowercaseLetters = regex.findall(r'[a-z]', reagent)
        # simple, IUPAC names (eg. 2-methylpentante) have mostly lowercase letters, 
        # structural formulas have at most 1/2 lowercase letters (eg. AlBr)
        # so that's how I sort them
        conversionStats['attempted'] += 1

        if len(letters) == 0:
            continue
        ratio = len(lowercaseLetters) / len(letters)

        if ratio >= 0.5:
            processedRowBool = IUPAC2SMILES(reagent, rowIndex, columnName)
            continue
    if processedRowBool:
        processedRows.append(rowIndex)
    else:
        rawRows.append(rowIndex)

processedDataframe = processedDataframe.loc[processedRows]
manualProcessingDataframe = manualProcessingDataframe.loc[rawRows]

processedDataframe.to_csv('processed.csv', index=False)
manualProcessingDataframe.to_csv('unprocessed.csv', index=False)

