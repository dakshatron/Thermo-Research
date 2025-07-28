import pubchempy as pcp
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

formula = "NF2"
print(f"Attempting to find compound for: '{formula}' using 'name' search...")

try:
    # 1. Make the request and store the list of results
    compounds = pcp.get_compounds(formula, 'name')

    # 2. DIAGNOSTIC STEP: Check what PubChem returned. Is it an empty list?
    print(f"PubChem API returned: {compounds}")

    # 3. Check if the list is not empty before trying to access it
    if compounds:
        # 4. Safely get the first result
        methanol = compounds[0]
        
        # 5. DIAGNOSTIC STEP: Check the compound object itself
        print(f"Found compound object: {methanol}")

        # 6. Access the desired property
        smiles_string = methanol.canonical_smiles

        # 7. Final check to see if the property itself is None
        if smiles_string:
            print(f"\nSUCCESS! SMILES string is: {smiles_string}")
        else:
            print("\nERROR: Found a compound, but its SMILES string is None. The data may be incomplete.")
    else:
        # This is the most likely place your script is failing.
        print("\nERROR: PubChem search returned no results. Check your input and internet connection.")

except Exception as e:
    # This will catch other errors, like network timeouts or IndexError
    print(f"\nAn unexpected error occurred: {e}")

