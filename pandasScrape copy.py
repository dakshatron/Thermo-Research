import pandas as pd  # dealing with weird lists and datatypes
import requests  # for fetching HTML from URLs
import re as regex  # HTML parser
import os  # checks if file exists
from typing import List, Dict, Optional, Tuple, Any, Union
import cirpy # for chemical name (eg. (CH_3)2(CH_2O_2)CC(O)CH_3) to SMILES conversion

# pre-compile regex patterns to make it faster
preExpFactorPattern = regex.compile(r'(\d+\.\d+)\s*[Xx]?\s*10\s*<sup>\s*([+-]?\s*\d+)\s*</sup>', regex.IGNORECASE) # ignores alphabet case, ie. A vs. a
activEnergyPattern = regex.compile(r'e\s*<sup>\s*([+-]?\d+)\s*\[.*?\]/RT\s*</sup>', regex.IGNORECASE)
rxnPattern = regex.compile('<B>Reaction:</B>(.*?)(?:<BR>|$)', regex.IGNORECASE | regex.DOTALL)

def padListToThree(inputList: List[str]) -> List[str]:
    return inputList + ([''] * (3 - len(inputList)))

def extractParams(pageHTMLParam: str) -> Optional[Tuple[str, str, str, List[str], List[str]]]:
    """
    Extracts parameters from the HTML content (given as plain text) of a reaction page.
    
    Args:
        pageHTMLParam (str): The HTML content of the reaction page as a string

    Returns:
        Tuple with:
        - preExpFactorCoeff (str): Coefficient of the pre-exponential factor
        - preExpFactorPower (str): Power of ten of the pre-exponential factor
        - activEnergy (str): Activation energy
        - reactants (List[str]): List of reactants as strings
        - products (List[str]): List of products as strings
    """
    preExpFactorCoeff = None
    preExpFactorPower = None
    activEnergy = None
    reactants = []
    products = []
    
    preExpFactorMatchObj = regex.search(preExpFactorPattern, pageHTMLParam)
    if preExpFactorMatchObj:
        preExpFactorCoeff = preExpFactorMatchObj.group(1).strip()
        preExpFactorPower = preExpFactorMatchObj.group(2).strip()
    
    activEnergyMatchObj = regex.search(activEnergyPattern, pageHTMLParam)
    if activEnergyMatchObj:
        activEnergy = activEnergyMatchObj.group(1).strip()

    rxnMatchObj = regex.search(rxnPattern, pageHTMLParam)

    if rxnMatchObj:
        # Clean and normalize the reaction HTML string
        rxnHTML = rxnMatchObj.group(1).strip()
        rxnHTML = rxnHTML.replace('&nbsp;', ' ')
        rxnHTML = rxnHTML.replace('&middot;', '(.)')
        rxnHTML = rxnHTML.replace('→', '->')
        rxnHTML = rxnHTML.replace('<sub>', '')
        rxnHTML = rxnHTML.replace('</sub>', '')
        rxnHTML = rxnHTML.replace('â‰¡', '≡')
        rxnHTML = regex.sub(r'<.*?>', '', rxnHTML) # Strip all remaining HTML tags
        rxnHTML = regex.sub(r'\s+', ' ', rxnHTML).strip()
        rxnParts = rxnHTML.split('->')

        # split rxn, then split reactants and products
        reactants = rxnParts[0].split('+')
        products = rxnParts[1].split('+')
        reactants = padListToThree(reactants)
        products = padListToThree(products)
        reactants = [r.strip() for r in reactants]
        products = [p.strip() for p in products]
    else:
        reactants = ['', '', '']
        products = ['', '', '']


    

    firstReactant = rxnParts
    print(rxnParts)
    
    return preExpFactorCoeff, preExpFactorPower, activEnergy, reactants[0], reactants[2], reactants[2], products[0], products[1], products[2] 

def fetchAndExtract(url: str, rowIndex: int) -> Optional[Tuple[str, str, str, str, str, str, str, str, str]]:
    """
    Gets url from overarching function, extracts with extractParams
    
    Args:
        url (str): reaction page url
        rowIndex (int): index of row in dataframe

    Returns:
        Tuple with:
        - preExpFactorCoeff (str): Coefficient of the pre-exponential factor
        - preExpFactorPower (str): Power of ten of the pre-exponential factor
        - activEnergy (str): Activation energy
        - reactants (List[str]): List of reactants as strings
        - products (List[str]): List of products as strings
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        pageHTML = response.text
        
        extractedParams = extractParams(pageHTML)
        if extractedParams:
            return extractedParams
        else:
            return ('Parse Error',) * 5
    except requests.RequestException as e:
        print(f"Error fetching URL at row {rowIndex + 1}: {e}")
        return ('Url Fetch Error',) * 5

def scrapeDatabaseWithPandas(inputCSVPath: str, outputCSVPath: str) -> None:
    """
    Tells fetchAndExtract what url to parse iteratively, saving to new file

    Args:
        inputCSVPath (str): original web scrape file with links and other data
        outputCSVPath (str): fresh file
    """
    if not os.path.exists(inputCSVPath):
        raise FileNotFoundError(f"Input file {inputCSVPath} does not exist.")
        return


    try:
        dataframe = pd.read_csv(inputCSVPath)
        print("Successfully read input CSV file.")
    except Exception as e:
        print("Error reading the CSV file:", e)
        return
    
    urlColumn = dataframe.columns[3] # urls in 4th column, index 3
    preExpColumn = dataframe.columns[6]
    activEnergyColumn = dataframe.columns[8]
    rateConstantColumn = dataframe.columns[9]


    latestAllRows = []
    checkpointInterval = 50 # save every 50 rows
    checkpointPath = 'checkpoint.csv'
    newColumnNames = [
        'Pre-Exp Factor Coeff',
        'Pre-Exp Factor Power',
        'Activation Energy',
        'Reactant 1',
        'Reactant 2',
        'Reactant 3',
        'Product 1',
        'Product 2',
        'Product 3'
    ]

    for rowIndex, row in dataframe.iterrows():
    # Now you can access any column in this row:

        url = row[urlColumn]
        extractedParams = fetchAndExtract(url, rowIndex)
        latestAllRows.append(extractedParams)

        if (len(latestAllRows) % checkpointInterval == 0):
            temporaryDataframe = pd.DataFrame(latestAllRows, columns=newColumnNames)
            temporaryDataframe.to_csv(checkpointPath, index=False, encoding='utf-8')
            print(f"Checkpoint saved at {len(latestAllRows)} rows.")


        # --- Start of the simple progress logic ---
        
        # Get the human-readable row number (starts at 1)
        rowNumber = rowIndex + 1
        
        # Check if the row number is exactly one of our milestones
        if rowNumber < 70000:
            print(f"--- Milestone: '{rowNumber}' links scraped ---")
        if rowNumber % 100 == 0:
            print(f"--- Milestone: '{rowNumber}' links scraped")

    

    extractedDataframe = pd.DataFrame(latestAllRows, columns = newColumnNames)

    finalDataframe = pd.concat([dataframe, extractedDataframe], axis=1)

    try:
        finalDataframe.to_csv(outputCSVPath, index=False, encoding='utf-8')
        print("Extraction complete")
    except Exception as e:
        print("Error writing to output CSV file:", e)

def main():
    inputCSVPath = 'records.csv'
    outputCSVPath = 'new extracted.csv'
    
    try:
        scrapeDatabaseWithPandas(inputCSVPath, outputCSVPath)
    except Exception as e:
        print(f"An error occurred: {e}")

main()