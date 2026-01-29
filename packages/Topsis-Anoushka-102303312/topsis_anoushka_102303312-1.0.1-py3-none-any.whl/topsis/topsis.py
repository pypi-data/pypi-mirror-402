import sys
import pandas as pd
import numpy as np
import os

def run():

    if len(sys.argv) != 5:
        print("Usage: topsis <inputfile> <weights> <impacts> <outputfile>")
        sys.exit(1)

    input_file = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    output_file = sys.argv[4]

    if not os.path.exists(input_file):
        print("Error: Input file not found")
        sys.exit(1)

    data = pd.read_csv(input_file)

    if data.shape[1] < 3:
        print("Error: File must contain at least 3 columns")
        sys.exit(1)

    try:
        matrix = data.iloc[:, 1:].astype(float)
    except:
        print("Error: Non-numeric values present")
        sys.exit(1)

    weights = list(map(float, weights.split(",")))
    impacts = impacts.split(",")

    if len(weights) != matrix.shape[1] or len(impacts) != matrix.shape[1]:
        print("Error: Weights, impacts & columns count mismatch")
        sys.exit(1)

    for i in impacts:
        if i not in ['+', '-']:
            print("Error: Impacts must be + or -")
            sys.exit(1)

    norm = np.sqrt((matrix ** 2).sum())
    normalized = matrix / norm
    weighted = normalized * weights

    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(weighted.iloc[:, i].max())
            ideal_worst.append(weighted.iloc[:, i].min())
        else:
            ideal_best.append(weighted.iloc[:, i].min())
            ideal_worst.append(weighted.iloc[:, i].max())

    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    score = dist_worst / (dist_best + dist_worst)

    data["Topsis Score"] = score
    data["Rank"] = data["Topsis Score"].rank(ascending=False).astype(int)

    data.to_csv(output_file, index=False)
    print("TOPSIS Result Saved Successfully as:", output_file)
