import csv # spreadsheet editor
import requests # HTML getter
import re as regex # HTML parser
import os # checks if file exists
from typing import List, Dict, Optional, Tuple, Any, Union
import pandas as pd # dealing with weird lists and datatypes

# pre-compile regex patterns to make it faster
preExpFactorPattern = regex.compile(r'(\d+\.\d+)\s*[Xx]?\s*10\s*<sup>\s*([+-]?\s*\d+)\s*</sup>', regex.IGNORECASE) # ignores alphabet case, ie. A vs. a
activEnergyPattern = regex.compile(r'e\s*<sup>\s*([+-]?\d+\s*\[.*?\]/RT)\s*</sup>', regex.IGNORECASE)
rxnPattern = regex.compile('<B>Reaction:</B>(.*?)(?:<BR>|$)', regex.IGNORECASE)

def extractParams(pageHTMLParam: str) -> Optional[Tuple[str, str, str, list[str, str], list[str, str]]]:
    preExpFactorCoeff = None
    preExpFactorPower = None
    activEnergy = None
    reactants = []
    products = []


    preExpFactorMatchObj = regex.search(preExpFactorPattern, pageHTMLParam)
    if preExpFactorMatchObj:
        preExpFactorCoeff = preExpFactorMatchObj.group(1)
        preExpFactorPower = preExpFactorMatchObj.group(2)


    activEnergyMatchObj = regex.search(activEnergyPattern, pageHTMLParam)
    if activEnergyMatchObj:
        activEnergy = activEnergyMatchObj.group(1)


    rxnSearchMatchObj = regex.search(r'<B>Reaction:</B>(.*?)(?:<BR>|$)', pageHTMLParam, regex.DOTALL | regex.IGNORECASE)

    if rxnSearchMatchObj:
        rxnHTML = rxnSearchMatchObj.group(1).strip()
        rxnHTML = rxnHTML.replace('&nbsp;', ' ')
        rxnHTML = rxnHTML.replace('&middot;', ' (.) ') # rewrites radical/free valence electron 
        rxnHTML = rxnHTML.replace('→', '->')
        rxnHTML = rxnHTML.replace('<sub>', '_') # rewrites subscriptd
        rxnHTML = rxnHTML.replace('</sub>', '')
        rxnHTML = regex.sub(r'<.*?>', '', rxnHTML) # removes all HTML tags
        rxnHTML = regex.sub(r'\s+', ' ', rxnHTML).strip() # replaces multiple spaces with one

        if '->' not in rxnHTML:
            print("Reaction arrow not found")
            return None
        rxnParts = rxnHTML.split('->')
        if len(rxnParts) != 2:
            print("Reaction arrow not formatted right")
            return None

    reactants = rxnParts[0].strip()
    products = rxnParts[1].strip()

    reactants = regex.sub(r'\s*\+\s*', '+', reactants)
    products = regex.sub(r'\s*\+\s*', '+', products)

    reactants = [r.strip() for r in reactants.split('+') if r.strip()]
    products = [p.strip() for p in products.split('+') if p.strip()]

    if len(reactants) != 2 or len(products) != 2:
        return

    return preExpFactorCoeff, preExpFactorPower, activEnergy, reactants, products

def fetchNExtract(url: str, row_index: int) -> Optional[Tuple[str, str, str, List[str, str], List[str, str]]]:
    # fetches HTML from url in row row_index, extracts and returns tuple of parameters 

def extractDatabase(inputCSVPathParam: str, outputCSVPathParam: str) -> None:
    """
    Writes entire contents of records.csv iteratively (not all at once) to empty list processedRows, 
    
    :param inputCSVPPath: Path to the input CSV file.
    :param outputCSVPath: Path to the output CSV file.
    """
    if not os.path.exists(inputCSVPathParam):
        print(f"Input file {inputCSVPathParam} does not exist.")
        return

    try:
        with open(inputCSVPathParam, mode='r', newline='', encoding='utf-8') as inputFile:
            reader: Iterator[List[str]] = csv.reader(inputFile) # creater 'csv scanner'
            header: List[str] = next(reader) # saves first row's header titles
            allDataRows: List[List[str]] = list(reader)  # saves rest into 2D array/spreadsheet
    except Exception as e:
        print(f"Error reading the CSV file: {e}")
        return

    URLColumnIndex: int = 3
    processedRows: List[List[str]] = []

    for indexOfRow, rowContents in enumerate(allDataRows): 
    # enumerate adds counter to list of lists allDataRows
        originalCurrentRowContentsList: List[str] = list(rowContents) # creates shallow copy
        URL = rowContents[3].strip()

        if URL: # if URL not empty
            try:
                serverResponse = requests.get(URL, timeout=1000)
                serverResponse.raise_for_status()  # raises an error if failed to get page's HTML
                pageHTML = serverResponse.text  # converts to a string I think

                extractedParameters = extractParams(pageHTML)  # returns tuple we need to unpack

                if extractedParameters: # if extraction successful
                    preExpFactorCoeff, preExpFactorPower, activEnergy, reactants, products = extractedParameters
                    originalCurrentRowContentsList.append(preExpFactorCoeff if preExpFactorCoeff is not None else "N/A")
                    originalCurrentRowContentsList.append(preExpFactorPower if preExpFactorPower is not None else "N/A")
                    originalCurrentRowContentsList.append(activEnergy if activEnergy is not None else "N/A")
                    originalCurrentRowContentsList.append(reactants if reactants is not None else "N/A")
                    originalCurrentRowContentsList.append(' + '.join(products) if products is not None else "N/A")
                else:
                    originalCurrentRowContentsList.extend(['N/A'] * 5) 
            except requests.exceptions.RequestException as e:
                print(f"  Error fetching URL for row {indexOfRow + 1}: {e}")
                originalCurrentRowContentsList.extend(['Fetch Error'] * 4)
        else:
            originalCurrentRowContentsList.extend(['N/A'] * 5)  # if URL is e

        processedRows.append(originalCurrentRowContentsList)

        try:
            with open(outputCSVPathParam, mode = 'w', newline='', encoding='utf-8') as outputFile:
                CSVWriterObj = csv.writer(outputFile)
                CSVWriterObj.writerow(originalCurrentRowContentsList) # write each time
            print("Extraction complete.")
        except Exception as e:
            print("Error writing to the CSV file:", e)

def main():
    inputCSVPath = 'records.csv'
    outputCSVPath = 'extracted.csv'
    extractDatabase(inputCSVPath, outputCSVPath)

main()