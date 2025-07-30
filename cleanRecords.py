import pandas

unfilteredDataframe = pandas.read_csv('NIST Extracted.csv')

columns2check = [
    'Pre-Exp Factor Coeff',
    'Pre-Exp Factor Power',
    'Activation Energy'
]

filteredDataframe = unfilteredDataframe[~unfilteredDataframe[columns2check].isnull().all(axis=1)]

filteredDataframe.to_csv('Filtered NIST Extracted.csv', index=False)