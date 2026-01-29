import sys
import pandas as pd
import numpy as np
import os

def main():
    if len(sys.argv) != 5:
        print("Usage: python topsis.py <inputfile> <weights> <impacts> <outputfile>")
        sys.exit(1)

    input_file, weights, impacts, output_file = sys.argv[1:]

    if not os.path.exists(input_file):
        print("Input file not found")
        sys.exit(1)

    data = pd.read_csv(input_file)

    if data.shape[1] < 3:
        print("File must contain at least 3 columns")
        sys.exit(1)

    matrix = data.iloc[:, 1:].values

    weights = list(map(float, weights.split(',')))
    impacts = impacts.split(',')

    if len(weights) != matrix.shape[1] or len(impacts) != matrix.shape[1]:
        print("Weights/Impacts count mismatch")
        sys.exit(1)

    norm = matrix / np.sqrt((matrix ** 2).sum(axis=0))
    weighted = norm * weights

    ideal_best, ideal_worst = [], []

    for j in range(matrix.shape[1]):
        if impacts[j] == '+':
            ideal_best.append(weighted[:, j].max())
            ideal_worst.append(weighted[:, j].min())
        else:
            ideal_best.append(weighted[:, j].min())
            ideal_worst.append(weighted[:, j].max())

    s_pos = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    s_neg = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    score = s_neg / (s_pos + s_neg)
    rank = score.argsort()[::-1].argsort() + 1

    data["Topsis Score"] = score
    data["Rank"] = rank
    data.to_csv(output_file, index=False)

    print("TOPSIS completed successfully")

if __name__ == "__main__":
    main()
