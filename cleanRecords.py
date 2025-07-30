import pandas as pd
import csv

recordsDataframe = pd.read_csv("NIST Extracted.csv")
usefulRows = []

for rowIndex, rowContents in recordsDataframe.iterrows():
    rowContentsStrings = [str(x).strip() for x in rowContents.values]
    useless = any((val in ['NaN', '#NUM!', 'Products', 'Adducts', 'products', 'adducts', 'nan', 'None'] for val in rowContentsStrings))

    if not useless:
        usefulRows.append(rowIndex)

mask = recordsDataframe.index.isin(usefulRows)
filteredDataframe = recordsDataframe[mask].reset_index(drop=True)
filteredDataframe.to_csv('Filtered Records.csv', index=False)
