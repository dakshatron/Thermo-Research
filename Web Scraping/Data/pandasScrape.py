import pandas as pd  # dealing with weird lists and datatypes
import requests  # for fetching HTML from URLs
import re as regex  # HTML parser
import os  # checks if file exists
from typing import List, Dict, Optional, Tuple, Any, Union # allows specification of datatype 
import cirpy # for chemical name (eg. (CH_3)2(CH_2O_2)CC(O)CH_3) to SMILES conversion

# pre-compile regex patterns to make it faster
preExpFactorPattern = regex.compile(r'(\d+\.\d+)\s*[Xx]?\s*10\s*<sup>\s*([+-]?\s*\d+)\s*</sup>', regex.IGNORECASE) # ignores alphabet case, ie. A vs. a
activEnergyPattern = regex.compile(r'e\s*<sup>\s*([+-]?\d+)\s*\[.*?\]/RT\s*</sup>', regex.IGNORECASE)
rxnPattern = regex.compile(r'<B>Reaction:</B>(.*?)(?:<BR>|$)', regex.IGNORECASE | regex.DOTALL)
temperaturePattern = regex.compile(r'<B>Temperature:</B>\s*(?:&nbsp;)*\s*([0-9]+(?:\.?[0-9]*)?\s*K?)(?:\s*-\s*([0-9]+(?:\.?[0-9]*)?\s*K?))?', regex.IGNORECASE)
reactionOrderPattern = regex.compile(r'<B>Reaction\s+Order:</B>\s*(?:&nbsp;|\s)*(\d)', regex.IGNORECASE)
tempRatioExpPattern = regex.compile(r'\(T\s*/298 \s* K\) \s* <sup> (-?\d+)', regex.IGNORECASE)

def extractParams(pageHTMLParam: str) -> Optional[Tuple[str, str, str, List[str], List[str], str]]:
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
    preExpFactorCoeff = ''
    preExpFactorPower = ''
    activEnergy = ''
    temperature = ''
    reactionOrder = ''
    tempRatioExp = ''
    reactants = ['', '', '']
    reactantsRaw = []
    products = ['', '', '']
    productsRaw = []
    rxnParts = []
    
    temperatureMatchObj = regex.search(temperaturePattern, pageHTMLParam)
    if temperatureMatchObj:
        temperature = temperatureMatchObj.group(1).strip() # (1) refers to first 'capturing group' (regex only captures stuff inside ()s, called capturing groups)

    reactionOrderMatchObj = regex.search(reactionOrderPattern, pageHTMLParam)
    if reactionOrderMatchObj:
        reactionOrder = reactionOrderMatchObj.group(1).strip()

    tempRatioExpMatchObj = regex.search(tempRatioExpPattern, pageHTMLParam)
    if tempRatioExpMatchObj:
        tempRatioExp = tempRatioExpMatchObj.group(1).strip()

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
        rxnHTML = rxnHTML.replace('&plus;', '+')
        rxnHTML = rxnHTML.replace('&plus', '+')
        rxnHTML = rxnHTML.replace('&middot;', '(.)')
        rxnHTML = rxnHTML.replace('((.))', '(.)')
        rxnHTML = rxnHTML.replace('⇒', '->')
        rxnHTML = rxnHTML.replace('⟶', '->')
        rxnHTML = rxnHTML.replace('→', '->')
        rxnHTML = rxnHTML.replace('<sub>', '')
        rxnHTML = rxnHTML.replace('</sub>', '')
        rxnHTML = rxnHTML.replace('â‰¡', '≡')
        rxnHTML = regex.sub(r'<.*?>', '', rxnHTML) # Strip all remaining HTML tags
        rxnHTML = regex.sub(r'\s+', ' ', rxnHTML).strip()
        rxnParts = rxnHTML.split('->')

        # split rxn, then split reactants and products
        if len(rxnParts) >= 2:
            reactantsRaw = rxnParts[0].split('+')
            productsRaw = rxnParts[1].split('+')
        else:
            return ('Parse Error',) * 10
        
        # replaces empty entries of reactants list; doing this to avoid out of index error
        for i in range(3):
            if len(reactantsRaw) > i:
                reactants[i] = reactantsRaw[i]
            if len(productsRaw) > i:
                products[i] = productsRaw[i]

        reactants = [r.strip() for r in reactants]
        products = [p.strip() for p in products]

    print(rxnParts)
    print(reactants)
    print(products)
    
    return preExpFactorCoeff, preExpFactorPower, activEnergy, reactants[0], reactants[1], reactants[2], products[0], products[1], products[2], temperature, reactionOrder, tempRatioExp 

def fetchAndExtract(url: str, rowIndex: int) -> Optional[Tuple[str, str, str, str, str, str, str, str, str, str, str]]:
    """
    Gets url from overarching function, extracts with extractParams
    
    Args:
        url (str): reaction page url from NIST 
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
        pageHTML = response.text # turns it into a string so regex can parse
        
        extractedParams = extractParams(pageHTML)
        if extractedParams:
            return extractedParams
        elif not extractedParams or len(extractedParams) != 10:
            return ('Parse Error',) * 10
    except requests.RequestException as e:
        print(f"Error fetching URL at row {rowIndex + 1}: {e}")
        return ('Url Fetch Error',) * 10

def scrapeDatabaseWithPandas(inputCSVPath: str, outputCSVPath: str) -> None:
    """
    Tells fetchAndExtract what url to parse iteratively, saving to new file

    Args:
        inputCSVPath (str): original 'NIST Records.csv' file from the dude on github, with links and other data
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

    latestAllRows = [] # temporary array I save to every time
    checkpointInterval = 50 # save every 50 rows
    checkpointPath = 'checkpoint.csv'

    # for cross reference with original 'NIST Records.csv' file
    columns2keep = [
        'RecordID',
        'RID',
        'Squib',
        'ReactionOrder'
    ]
    originalDataSubset = dataframe[columns2keep].copy()
    newColumnNames = [
        'Pre-Exp Factor Coeff',
        'Pre-Exp Factor Power',
        'Activation Energy',
        'Reactant 1',
        'Reactant 2',
        'Reactant 3',
        'Product 1',
        'Product 2',
        'Product 3',
        'Temperature',
        'Reaction Order',
        'Temperature Ratio Exponent'
    ]

    for rowIndex, rowContents in dataframe.iterrows():

        url = rowContents[urlColumn]
        extractedParams = fetchAndExtract(url, rowIndex)
        latestAllRows.append(extractedParams)

        if (len(latestAllRows) % checkpointInterval == 0): # if divisible by checkpoint, save
            try:
                # get processed rows from original subset, works like a mask i think
                processedOriginalRows = originalDataSubset.iloc[:len(latestAllRows)]
                
                # Create extracted dataframe
                extractedDataframe = pd.DataFrame(latestAllRows, columns=newColumnNames)
                
                # Combine extracted dataframe with stuff I want to keep from old
                combinedDataframe = pd.concat([
                    processedOriginalRows.reset_index(drop=True), 
                    extractedDataframe
                ], axis=1)
                
                # Save checkpoint
                combinedDataframe.to_csv(checkpointPath, index=False, encoding='utf-8')
                print(f"Checkpoint saved at {len(latestAllRows)} rows with {combinedDataframe.shape[1]} columns.")
                
            except Exception as e:
                print(f"Checkpoint save failed: {e}")

        rowNumber = rowIndex + 1
        
        # Check if the row number is exactly one of our milestones
        if rowNumber < 70000:
            print(f"--- Milestone: '{rowNumber}' links scraped ---")
        if rowNumber % 100 == 0:
            print(f"--- Milestone: '{rowNumber}' links scraped")

    extractedDataframe = pd.DataFrame(latestAllRows, columns = newColumnNames) # I think it already was a dataframe but this made it work soooo

    

    # finalDataframe = pd.concat([dataframe, extractedDataframe], axis=1) # this is wrong, extracted has duplicate junk

    try:
        extractedDataframe.to_csv(outputCSVPath, index=False, encoding='utf-8')
        print("Extraction complete")
    except Exception as e:
        print("Error writing to output CSV file:", e)

def main():
    inputCSVPath = 'NIST Records.csv'
    outputCSVPath = 'extracted.csv'
    
    try:
        scrapeDatabaseWithPandas(inputCSVPath, outputCSVPath)
    except Exception as e:
        print(f"An error occurred: {e}")

main()