import pandas as pd
import numpy as np
import sys
import os

def topsis(input_file, weights, impacts, output_file):
    df = pd.read_csv(input_file)

    if df.shape[1] < 3:
        raise ValueError("Input file must contain three or more columns")

    data = df.iloc[:, 1:].values

    weights = list(map(float, weights.split(',')))
    impacts = impacts.split(',')

    if len(weights) != data.shape[1] or len(impacts) != data.shape[1]:
        raise ValueError("Number of weights and impacts must match criteria count")

    if not all(i in ['+', '-'] for i in impacts):
        raise ValueError("Impacts must be + or -")

    norm = data / np.sqrt((data ** 2).sum(axis=0))
    weighted = norm * weights

    ideal_best = []
    ideal_worst = []

    for i in range(data.shape[1]):
        if impacts[i] == '+':
            ideal_best.append(weighted[:, i].max())
            ideal_worst.append(weighted[:, i].min())
        else:
            ideal_best.append(weighted[:, i].min())
            ideal_worst.append(weighted[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    score = dist_worst / (dist_best + dist_worst)
    df["Topsis Score"] = score
    df["Rank"] = pd.Series(score).rank(ascending=False)

    df.to_csv(output_file, index=False)

def main():
    if len(sys.argv) != 5:
        print("Usage: python -m topsis_suhani_102313038 <input> <weights> <impacts> <output>")
        sys.exit(1)

    _, input_file, weights, impacts, output_file = sys.argv
    topsis(input_file, weights, impacts, output_file)

if __name__ == "__main__":
    main()
