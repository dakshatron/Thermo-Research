import csv
import requests
import re as regex
import os
from typing import List, Tuple, Optional, Iterator

# --- Pre-compiled Regex Patterns (These are good) ---
preExpFactorPattern = regex.compile(r'(\d+\.\d+)\s*[Xx]?\s*10\s*<sup>\s*([+-]?\s*\d+)\s*</sup>', regex.IGNORECASE)
activEnergyPattern = regex.compile(r'e\s*<sup>\s*([+-]?\d+\s*\[.*?\]/RT)\s*</sup>', regex.IGNORECASE)
rxnPattern = regex.compile(r'<B>Reaction:</B>(.*?)(?:<BR>|$)', regex.IGNORECASE | regex.DOTALL)

# --- Refactored Extraction Function ---
def extractParams(html_content: str) -> Optional[Tuple[Optional[str], Optional[str], Optional[str], List[str], List[str]]]:
    """
    Extracts all possible data from raw HTML. Returns a tuple where missing items are None.
    """
    preExpFactorCoeff = None
    preExpFactorPower = None
    activEnergy = None
    reactants = []
    products = []

    # --- Extract data using patterns ---
    preExpFactorMatchObj = preExpFactorPattern.search(html_content)
    if preExpFactorMatchObj:
        preExpFactorCoeff = preExpFactorMatchObj.group(1).strip()
        preExpFactorPower = preExpFactorMatchObj.group(2).strip()

    activEnergyMatchObj = activEnergyPattern.search(html_content)
    if activEnergyMatchObj:
        activEnergy = activEnergyMatchObj.group(1).strip()

    # FIX: Use the function's parameter 'html_content', not a global variable
    rxnSearchMatchObj = rxnPattern.search(html_content)
    if rxnSearchMatchObj:
        rxnHTML = rxnSearchMatchObj.group(1).strip()
        # Cleaning steps
        rxnHTML = rxnHTML.replace('&nbsp;', ' ').replace('&middot;', ' (.) ').replace('→', '->')
        rxnHTML = regex.sub(r'</?sub>', '', rxnHTML)
        rxnHTML = regex.sub(r'<.*?>', '', rxnHTML)
        rxnHTML = regex.sub(r'\s+', ' ', rxnHTML).strip()

        if '->' in rxnHTML:
            parts = rxnHTML.split('->')
            if len(parts) == 2:
                reactants_str = parts[0].strip()
                products_str = parts[1].strip()
                reactants = [r.strip() for r in reactants_str.split('+') if r.strip()]
                products = [p.strip() for p in products_str.split('+') if p.strip()]
    
    # Return the tuple of results, which may contain None values
    return preExpFactorCoeff, preExpFactorPower, activEnergy, reactants, products

# --- Refactored Main Automation Function ---
def extractDatabase(csv_path: str, url_column_name: str) -> None:
    """
    Reads a CSV, scrapes data for each URL, and overwrites the file with the new data.
    """
    if not os.path.exists(csv_path):
        print(f"Error: Input file '{csv_path}' does not exist.")
        return

    # --- Step 1: Read all data into memory ---
    try:
        with open(csv_path, mode='r', newline='', encoding='utf-8') as inputFile:
            reader: Iterator[List[str]] = csv.reader(inputFile)
            header: List[str] = next(reader)
            allDataRows: List[List[str]] = list(reader)
    except Exception as e:
        print(f"Error reading the CSV file: {e}")
        return

    # --- Step 2: Prepare for processing ---
    # FIX: Initialize the list to store results
    processedRows = []
    
    # Find the URL column index dynamically for robustness
    try:
        url_column_index = header.index(url_column_name)
    except ValueError:
        print(f"Error: Column '{url_column_name}' not found in headers: {header}")
        return
    
    # Add new headers if they don't already exist
    new_headers = ['Pre_exp_Coeff', 'Pre_exp_Power', 'Activation_Energy', 'Reactants', 'Products']
    for h in new_headers:
        if h not in header:
            header.append(h)

    # --- Step 3: Loop through data, scrape, and build the results ---
    for indexOfRow, rowContents in enumerate(allDataRows):
        currentRowContentsList: List[str] = list(rowContents)
        URL = currentRowContentsList[url_column_index].strip() if len(currentRowContentsList) > url_column_index else ""

        if URL:
            try:
                serverResponse = requests.get(URL, timeout=10)
                serverResponse.raise_for_status()
                pageHTML = serverResponse.text

                extractedParameters = extractParams(pageHTML)

                if extractedParameters:
                    coeff, power, energy, reactants, products = extractedParameters
                    # Append new data
                    currentRowContentsList.append(coeff if coeff is not None else "N/A")
                    currentRowContentsList.append(power if power is not None else "N/A")
                    currentRowContentsList.append(energy if energy is not None else "N/A")
                    currentRowContentsList.append(' + '.join(reactants) if reactants else "N/A")
                    currentRowContentsList.append(' + '.join(products) if products else "N/A")
                else:
                    currentRowContentsList.extend(['Extraction Failed'] * 5)
            except requests.exceptions.RequestException as e:
                print(f"  Error fetching URL for row {indexOfRow + 1}: {e}")
                currentRowContentsList.extend(['Fetch Error'] * 5)
        else:
            currentRowContentsList.extend(['No URL'] * 5)
        
        # Ensure row has the correct number of columns before adding it
        while len(currentRowContentsList) < len(header):
            currentRowContentsList.append("N/A")
            
        processedRows.append(currentRowContentsList)

    # --- Step 4: Write the processed data back to the original file ---
    try:
        with open(csv_path, mode='w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(header) # Write the updated header
            writer.writerows(processedRows) # Write all the modified data
        print(f"\nProcessing complete. File '{csv_path}' has been updated.")
    except Exception as e:
        print(f"Error writing data back to CSV: {e}")

# --- Script Execution ---
if __name__ == '__main__':
    input_csv_file = 'records.csv'
    url_header_name = 'NIST_URL' # Change this to match the exact name in your CSV
    # Create a dummy file for testing if 'records.csv' doesn't exist
    if not os.path.exists(input_csv_file):
        print(f"Creating dummy file '{input_csv_file}' for testing.")
        dummy_data = [
            ['Reaction_ID', 'Reactants', 'Products', 'NIST_URL'],
            ['R1', 'H + O2', 'OH + O', 'https://kinetics.nist.gov/kinetics/Detail?id=1997DEM/SAN1-266:244'],
            ['R2', 'CH3 + H', 'CH4', 'https://kinetics.nist.gov/kinetics/Detail?id=1991BAU/COB1050-1083:2'],
        ]
        with open(input_csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(dummy_data)
    
    extractDatabase(input_csv_file, url_header_name)
