import sys
import os
from .topsis import topsis

def main():
    if len(sys.argv) != 5:
        print("Usage: python -m topsis_naman_102303496 <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    result_file = sys.argv[4]
    
    if not os.path.exists(input_file):
        print("File not Found")
        sys.exit(1)
    
    df = __import__('pandas').read_csv(input_file)
    
    if len(df.columns) < 3:
        print("Input file must contain three or more columns")
        sys.exit(1)
    
    weights_list = weights.split(',')
    impacts_list = impacts.split(',')
    
    for col in df.columns[1:]:
        for val in df[col]:
            if not str(val).replace('.', '').replace('-', '').isdigit():
                print("From 2nd to last columns must contain numeric values only")
                sys.exit(1)
    
    n = len(df.columns) - 1
    if len(weights_list) != n or len(impacts_list) != n:
        print("Number of weights, number of impacts and number of columns must be the same")
        sys.exit(1)
    
    for imp in impacts_list:
        if imp not in ['+', '-']:
            print("Impacts must be either +ve or -ve")
            sys.exit(1)
    
    topsis(input_file, weights, impacts, result_file)

if __name__ == "__main__":
    main()
