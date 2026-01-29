import pandas as pd
import numpy as np
import sys

def topsis(input_file, weights, impacts, output_file):
    df = pd.read_csv(input_file)

    if df.shape[1] < 3:
        raise ValueError("Input file must contain at least 3 columns")

    data = df.iloc[:, 1:].astype(float)

    if len(weights) != data.shape[1] or len(impacts) != data.shape[1]:
        raise ValueError("Weights and impacts must match criteria count")

    normalized = data / np.sqrt((data ** 2).sum())
    weighted = normalized * weights

    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(weighted.iloc[:, i].max())
            ideal_worst.append(weighted.iloc[:, i].min())
        elif impacts[i] == '-':
            ideal_best.append(weighted.iloc[:, i].min())
            ideal_worst.append(weighted.iloc[:, i].max())
        else:
            raise ValueError("Impacts must be + or -")

    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    score = dist_worst / (dist_best + dist_worst)

    df["Topsis Score"] = score
    df["Rank"] = df["Topsis Score"].rank(ascending=False).astype(int)

    df.to_csv(output_file, index=False)

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: topsis <input_file> <weights> <impacts> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    weights = list(map(float, sys.argv[2].split(",")))
    impacts = sys.argv[3].split(",")
    output_file = sys.argv[4]

    topsis(input_file, weights, impacts, output_file)
    print("TOPSIS calculation completed.")
