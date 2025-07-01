import requests
from bs4 import BeautifulSoup
import re as regex # string pattern parser
from typing import List, Dict, Optional, Tuple, Any

# # URL of NIST page to scrape
# URL = "https://kinetics.nist.gov/kinetics/Detail?id=1992BAU/COB411-429:29"

# # Fetch content from the URL
# page = requests.get(URL)

# # Create soup object
# pageSoup = BeautifulSoup(page.content, "lxml")




# text = "673.59x10<sup> + 11</sup> [cm<sup>3</sup>/molecule s]  e<sup> -238 [kJ/mole]/RT</sup><BR>"
# print(regex.findall(r'(\d+\.\d+)\s*[Xx]?\s*10\s*<sup>\s*([+-]?\s*\d+)\s*</sup>', text))
# print(regex.findall(r'e\s*<sup>\s*([+-]?\s*\d+)', text))

# newText = "5      +    3"
# print(regex.findall(r'(\d)\s*\+\s*(\d)', newText))

equation: str = """<B>Reaction:</B>&nbsp;&nbsp; <a href="https://webbook.nist.gov/cgi/cbook.cgi?ID=74840&amp;Units=SI" target=_blank onMouseOver="showPicture('https://webbook.nist.gov/cgi/cbook.cgi?Struct=74840&Type=Solid',event);" onMouseOut="Hide('iAlt');">C<sub>2</sub>H<sub>6</sub></a> + <a href="https://webbook.nist.gov/cgi/cbook.cgi?ID=7782447&amp;Units=SI" target=_blank onMouseOver="showPicture('https://webbook.nist.gov/cgi/cbook.cgi?Struct=7782447&Type=Solid',event);" onMouseOut="Hide('iAlt');">O<sub>2</sub></a> → <a href="https://webbook.nist.gov/cgi/cbook.cgi?ID=2025561&amp;Units=SI" target=_blank onMouseOver="showPicture('https://webbook.nist.gov/cgi/cbook.cgi?Struct=2025561',event);" onMouseOut="Hide('iAlt');">&middot;C<sub>2</sub>H<sub>5</sub></a> + <a href="https://webbook.nist.gov/cgi/cbook.cgi?ID=3170830&amp;Units=SI" target=_blank onMouseOver="showPicture('https://webbook.nist.gov/cgi/cbook.cgi?Struct=3170830',event);" onMouseOut="Hide('iAlt');">HO<sub>2</sub></a><BR>"""
def rxnExtractor(pageHTML: str) -> str:
    # error handling; instead of direct assignment, checks if found or not before assigning
    rxnSearchMatch = regex.search(r'<B>Reaction:</B>(.*?)(?:<BR>|$)', pageHTML, regex.DOTALL | regex.IGNORECASE)
    if not rxnSearchMatch:
        return "Reaction information not found in the provided HTML snippet."

    cleanedRxn = rxnSearchMatch.group(1).strip()
    cleanedRxn = cleanedRxn.replace('&nbsp;', ' ')
    cleanedRxn = cleanedRxn.replace('&middot;', '/dot ') # rewrites radical/free valence electron 
    cleanedRxn = cleanedRxn.replace('→', '->')
    cleanedRxn = cleanedRxn.replace('<sub>', '_') # rewrites subscriptd
    cleanedRxn = cleanedRxn.replace('</sub>', '')
    cleanedRxn = regex.sub(r'<.*?>', '', cleanedRxn) # removes all HTML tags
    cleanedRxn = regex.sub(r'\s+', ' ', cleanedRxn).strip() # replaces multiple spaces with one

    if '->' not in cleanedRxn:
        return "Reaction arrow not found in the provided HTML snippet."
    rxnParts = cleanedRxn.split('->')
    if len(rxnParts) != 2:
        return "Reaction arrow not formatted correctly in the provided HTML snippet."

    reactants = rxnParts[0].strip()
    products = rxnParts[1].strip()

    reactants = regex.sub(r'\s*\+\s*', '+', reactants)
    products = regex.sub(r'\s*\+\s*', '+', products)

    reactants = reactants.split('+')
    products = products.split('+')

    if len(reactants) != 2 or len(products) != 2:
        return "Reaction does not have exactly two reactants and two products."

    return reactants, products
reactants, products = rxnExtractor(equation)
print(f"List of reactants: {reactants}, while list of products: {products}")