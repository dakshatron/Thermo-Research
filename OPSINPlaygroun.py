from pyopsin import PyOpsin
import pandas as pd  # dealing with weird lists and datatypes
import requests  # for fetching HTML from URLs
import regex  # HTML parser
import os  # checks if file exists
from typing import List, Dict, Optional, Tuple, Any, Union
import cirpy # for chemical name (eg. (CH_3)2(CH_2O_2)CC(O)CH_3) to SMILES conversion

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
import time





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

filteredDataframe = filteredDataframe.replace('_', '', regex=True)  # removes underscores
filteredDataframe.to_csv('IUPAC Conversion Test.csv', index=False)  # save the cleaned dataframe


### Select all kinetic columns at once, then apply axis=1
# kineticColumns = ['Pre-Exp Factor Coeff', 'Pre-Exp Factor Power', 'Activation Energy']
# kineticDataMask = withIUPACdataframe[kineticColumns].notna().all(axis=1) # creates mask (true false matrix) true for rows with full data

# products_mask = (withIUPACdataframe['Product 1'].fillna('').str.lower() == 'products') & \
#                 (withIUPACdataframe['Product 2'].fillna('').str.strip() == '') & \
#                 (withIUPACdataframe['Product 3'].fillna('').str.strip() == '')

# finalMask = kineticDataMask & ~products_mask

# filteredDataframe.insert(0, 'ID', range(1, len(filteredDataframe) + 1)) # reset index after filtering
# filteredDataframe.to_csv('IUPAC Conversion Test.csv', index=False)
myOptions = Options()
# myOptions.add_argument("--headless")  # Run without opening a browser window
# Essential stability options
myOptions.add_argument("--no-sandbox")
myOptions.add_argument("--disable-dev-shm-usage")
myOptions.add_argument("--disable-gpu")
myOptions.add_argument("--disable-extensions")

# Network and automation options
myOptions.add_argument("--remote-debugging-port=9222")
myOptions.add_argument("--disable-background-networking")
myOptions.add_argument("--disable-background-timer-throttling")
myOptions.add_argument("--disable-renderer-backgrounding")
myOptions.add_argument("--disable-backgrounding-occluded-windows")

# service = Service(ChromeDriverManager().install())
# Add this crucial option for modern Chrome versions
myOptions.add_argument("--remote-allow-origins=*")

driver = webdriver.Chrome(options=myOptions)

"""Test if Chrome can access external websites"""
test_urls = [
    "https://www.google.com",
    "https://httpbin.org/get",  # Simple test endpoint
    "https://pubchem.ncbi.nlm.nih.gov"  # Your target site
]

for url in test_urls:
    try:
        driver.get(url)
        current_url = driver.current_url
        
        if not current_url.startswith("data:"):
            print(f"Successfully accessed: {url}")
        else:
            print(f"Failed to access: {url}")
            
    except Exception as e:
        print(f"Error accessing {url}: {e}")

def structural2SMILES(structuralFormula: str) -> Optional[str]:
    maxRetries = 3
    retryDelay = 1 # seconds, I think
    
    for attempt in range(maxRetries):
        try:
            pubchemUrl = f"https://pubchem.ncbi.nlm.nih.gov/compound/" + structuralFormula
            print(f"Navigating to PubChem URL: {pubchemUrl}")
            driver.get(pubchemUrl)
            time.sleep(1)
            currentUrl = driver.current_url
            if currentUrl != pubchemUrl:
                print(f"Redirected to: {currentUrl}")
                return "None"
            if "404" in driver.title or "not found" in driver.page_source.lower():
                return "None"
            break
        except (WebDriverException, TimeoutException) as e:
            if attempt < (maxRetries - 1):
                time.sleep(retryDelay * (attempt + 1))  # gives it some time to recover
            else:
                return "None"
        except Exception as e:
            return "None"
    wait = WebDriverWait(driver, 10)
    try:
        smilesContainer = wait.until(
            EC.presence_of_element_located((By.XPATH, "//section[text()='SMILES']"))
        )
        smilesDiv = smilesContainer.find_element(By.XPATH, ".//div[@class='break-words space-y-1']")
        smiles = smilesDiv.text.strip()
    except NoSuchElementException:
        return "None"
    return smiles

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
                    smiles = structural2SMILES(reagent)
                    
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