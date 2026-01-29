import sys
import pandas as pd
import numpy as np
import os

def topsis(input_file, weights, impacts, output_file):

    
    if not os.path.exists(input_file):
        print("Error: Input file not found")
        sys.exit(1)

    
    try:
        df = pd.read_excel(input_file)
    except:
        print("Error: Unable to read input file")
        sys.exit(1)


    if df.shape[1] < 3:
        print("Error: Input file must contain three or more columns")
        sys.exit(1)


    data = df.iloc[:, 1:].copy()

    for col in data.columns:
        if not pd.api.types.is_numeric_dtype(data[col]):
            print("Error: All columns from 2nd to last must be numeric")
            sys.exit(1)

    weights = weights.split(",")
    impacts = impacts.split(",")


    if len(weights) != data.shape[1] or len(impacts) != data.shape[1]:
        print("Error: Number of weights, impacts and criteria must be equal")
        sys.exit(1)


    try:
        weights = np.array(weights, dtype=float)
    except:
        print("Error: Weights must be numeric")
        sys.exit(1)

 
    for impact in impacts:
        if impact not in ['+', '-']:
            print("Error: Impacts must be either + or -")
            sys.exit(1)

    norm_data = data / np.sqrt((data ** 2).sum())


    weighted_data = norm_data * weights


    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(weighted_data.iloc[:, i].max())
            ideal_worst.append(weighted_data.iloc[:, i].min())
        else:
            ideal_best.append(weighted_data.iloc[:, i].min())
            ideal_worst.append(weighted_data.iloc[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    dist_best = np.sqrt(((weighted_data - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted_data - ideal_worst) ** 2).sum(axis=1))

    topsis_score = dist_worst / (dist_best + dist_worst)

    df["Topsis Score"] = topsis_score
    df["Rank"] = df["Topsis Score"].rank(ascending=False, method='dense').astype(int)

    
    df.to_excel(output_file, index=False)
    print("TOPSIS analysis completed successfully")



def main():
    if len(sys.argv) != 5:
        print("Usage: python topsis.py <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        sys.exit(1)

    _, input_file, weights, impacts, output_file = sys.argv
    topsis(input_file, weights, impacts, output_file)

if __name__ == "__main__":
    main()
