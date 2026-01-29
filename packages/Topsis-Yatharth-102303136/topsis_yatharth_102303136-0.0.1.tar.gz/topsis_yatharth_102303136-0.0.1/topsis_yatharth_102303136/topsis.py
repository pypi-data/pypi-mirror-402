import sys
import pandas as pd
import numpy as np

def topsis(input_file, weights, impacts, output_file):
    data = pd.read_csv(input_file)

    if data.shape[1] < 3:
        raise Exception("Input file must contain at least 3 columns")

    matrix = data.iloc[:, 1:].values.astype(float)

    weights = np.array(weights)
    impacts = np.array(impacts)

    if matrix.shape[1] != len(weights) or matrix.shape[1] != len(impacts):
        raise Exception("Weights, impacts and criteria count mismatch")

    norm = matrix / np.sqrt((matrix ** 2).sum(axis=0))
    weighted = norm * weights

    ideal_best = np.where(impacts == '+',
                          weighted.max(axis=0),
                          weighted.min(axis=0))
    ideal_worst = np.where(impacts == '+',
                           weighted.min(axis=0),
                           weighted.max(axis=0))

    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    score = dist_worst / (dist_best + dist_worst)

    data["Topsis Score"] = score
    data["Rank"] = data["Topsis Score"].rank(ascending=False).astype(int)

    data.to_csv(output_file, index=False)

def main():
    if len(sys.argv) != 5:
        print("Usage: topsis <input_file> <weights> <impacts> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    weights = list(map(float, sys.argv[2].split(",")))
    impacts = sys.argv[3].split(",")
    output_file = sys.argv[4]

    topsis(input_file, weights, impacts, output_file)

if __name__ == "__main__":
    main()
