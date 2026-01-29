import sys
import pandas as pd
import numpy as np
import os


def topsis(input_file, weights, impacts, output_file):

    # ---------- File existence ----------
    if not os.path.isfile(input_file):
        print("Error: Input file not found")
        sys.exit(1)

    data = pd.read_csv(input_file)

    if data.shape[1] < 3:
        print("Error: Input file must contain at least 3 columns")
        sys.exit(1)

    matrix = data.iloc[:, 1:].values

    # ---------- Numeric check ----------
    if not np.issubdtype(matrix.dtype, np.number):
        print("Error: From 2nd to last columns must be numeric")
        sys.exit(1)

    weights = list(map(float, weights.split(",")))
    impacts = impacts.split(",")

    if len(weights) != matrix.shape[1] or len(impacts) != matrix.shape[1]:
        print("Error: Number of weights, impacts and columns must be same")
        sys.exit(1)

    if not all(i in ['+', '-'] for i in impacts):
        print("Error: Impacts must be + or -")
        sys.exit(1)

    # ---------- Normalization ----------
    norm = np.sqrt((matrix ** 2).sum(axis=0))
    normalized = matrix / norm

    # ---------- Weighted normalized matrix ----------
    weighted = normalized * weights

    # ---------- Ideal best & worst ----------
    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(weighted[:, i].max())
            ideal_worst.append(weighted[:, i].min())
        else:
            ideal_best.append(weighted[:, i].min())
            ideal_worst.append(weighted[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # ---------- Distance ----------
    d_pos = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    d_neg = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    # ---------- Topsis score ----------
    score = d_neg / (d_pos + d_neg)

    data["Topsis Score"] = score
    data["Rank"] = data["Topsis Score"].rank(ascending=False).astype(int)

    data.to_csv(output_file, index=False)
    print("Output saved to", output_file)


def main():
    if len(sys.argv) != 5:
        print("Usage: topsis <inputFile> <weights> <impacts> <outputFile>")
        sys.exit(1)

    topsis(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])


# ---------- Entry point ----------
if __name__ == "__main__":
    main()
