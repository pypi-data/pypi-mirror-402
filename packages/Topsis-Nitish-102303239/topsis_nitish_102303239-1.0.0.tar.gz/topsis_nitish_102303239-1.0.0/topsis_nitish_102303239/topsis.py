import sys
import pandas as pd
import numpy as np
import os

def topsis(input_file, weights, impacts, output_file):

    # File existence check
    if not os.path.isfile(input_file):
        print("Error: Input file not found")
        sys.exit(1)

    # Read CSV
    try:
        data = pd.read_csv(input_file)
    except:
        print("Error: Unable to read CSV file")
        sys.exit(1)

    # Minimum column check
    if data.shape[1] < 3:
        print("Error: Input file must contain at least 3 columns")
        sys.exit(1)

    matrix = data.iloc[:, 1:].values

    # Numeric check
    try:
        matrix = matrix.astype(float)
    except:
        print("Error: All columns from 2nd to last must be numeric")
        sys.exit(1)

    weights = weights.split(",")
    impacts = impacts.split(",")

    if len(weights) != matrix.shape[1] or len(impacts) != matrix.shape[1]:
        print("Error: Number of weights, impacts and columns must be same")
        sys.exit(1)

    try:
        weights = np.array(weights, dtype=float)
    except:
        print("Error: Weights must be numeric")
        sys.exit(1)

    for i in impacts:
        if i not in ['+', '-']:
            print("Error: Impacts must be either + or -")
            sys.exit(1)

    # Normalization
    norm = np.sqrt((matrix ** 2).sum(axis=0))
    normalized = matrix / norm

    # Weighted normalized matrix
    weighted = normalized * weights

    # Ideal best and worst
    ideal_best = []
    ideal_worst = []

    for i in range(weighted.shape[1]):
        if impacts[i] == '+':
            ideal_best.append(max(weighted[:, i]))
            ideal_worst.append(min(weighted[:, i]))
        else:
            ideal_best.append(min(weighted[:, i]))
            ideal_worst.append(max(weighted[:, i]))

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # Distances
    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    # Score
    score = dist_worst / (dist_best + dist_worst)
    rank = score.argsort()[::-1] + 1

    # Output
    data["Topsis Score"] = score
    data["Rank"] = rank

    data.to_csv(output_file, index=False)
    print("Result saved to", output_file)


def main():
    if len(sys.argv) != 5:
        print("Usage: python -m topsis_nitish_102303239.topsis <InputDataFile> <Weights> <Impacts> <OutputFile>")
        sys.exit(1)

    _, input_file, weights, impacts, output_file = sys.argv
    topsis(input_file, weights, impacts, output_file)


if __name__ == "__main__":
    main()
