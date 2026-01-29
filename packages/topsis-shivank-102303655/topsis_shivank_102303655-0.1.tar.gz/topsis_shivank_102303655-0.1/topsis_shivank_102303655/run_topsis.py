import sys
import pandas as pd
import topsis
import os

def main():
    print("TOPSIS program running")


if len(sys.argv) < 5:
    print('Insufficient arguments')
    sys.exit(1)

filename = sys.argv[1]
temp_file = 'temp_file_for_topsis.csv'
output_filepath = sys.argv[4]

try:
    data = pd.read_csv(filename)
    data_numeric = data.iloc[:, 1:]

    try:
        weights = [float(w) for w in sys.argv[2].split(',')]
    except ValueError:
        print("Error: Weights must be numeric and separated by commas.")
        sys.exit(1)
        
    impacts = sys.argv[3].split(',')

    if data.shape[1] < 3:
        print('Input Data contains less than 3 columns!')
        sys.exit(1)        
        
    numeric_cols = data_numeric.select_dtypes(include=['number'])
        
    if numeric_cols.shape[1] != data_numeric.shape[1]:
        print('Error: From 2nd to last columns, input data contains non-numeric values!')
        sys.exit(1)

    if len(weights) == len(impacts) and len(weights) == data_numeric.shape[1]:
        # print('Correct Shape')
        pass
    else:
        print('Error: Number of weights, impacts, and columns must be the same!')
        sys.exit(1)

    for i in impacts:
        if i not in ['+', '-']:
            print(f"Error: Impact '{i}' is not valid. Impacts must be either '+' or '-'.")
            sys.exit(1)


    print("CSV loaded. Shape:", data_numeric.shape)
    data_numeric.to_csv(temp_file, index=False)

    tp = topsis.Topsis(temp_file)
    results = tp.evaluate(weights, impacts)

    scores = [row[1] for row in results]
    ranks = [row[2] for row in results]

    data['Topsis Score'] = scores
    data['Rank'] = ranks

    print(data)
    data.to_csv(output_filepath,index=False)

except FileNotFoundError:
    print("Error: File not found.")
    sys.exit(1)
except Exception as ex:
    print(ex)
    sys.exit(1)