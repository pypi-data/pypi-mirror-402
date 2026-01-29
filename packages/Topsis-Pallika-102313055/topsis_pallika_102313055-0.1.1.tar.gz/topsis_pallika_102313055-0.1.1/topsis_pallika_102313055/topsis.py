import sys
import os
import pandas as pd
import numpy as np

def stop(msg):
    print("ERROR:", msg)
    sys.exit(1)

def main():
    if len(sys.argv) != 5:
        stop("Usage: python topsis.py <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")

    input_file = sys.argv[1]
    weights_str = sys.argv[2]
    impacts_str = sys.argv[3]
    output_file = sys.argv[4]

    if not os.path.exists(input_file):
        stop("Input file not found")

    df = pd.read_csv(input_file)

    if df.shape[1] < 3:
        stop("Input file must contain three or more columns")

    criteria = df.iloc[:, 1:]
    numeric_check = criteria.apply(pd.to_numeric, errors='coerce')
    if numeric_check.isnull().values.any():
        stop("From 2nd to last columns must contain numeric values only")

    criteria = numeric_check

    weights = weights_str.split(',')
    impacts = impacts_str.split(',')

    if len(weights) != criteria.shape[1] or len(impacts) != criteria.shape[1]:
        stop("Number of weights, impacts and criteria columns must be equal")

    weight_values = []
    for w in weights:
        if w.replace('.', '', 1).isdigit():
            weight_values.append(float(w))
        else:
            stop("Weights must be numeric and comma separated")

    weights = np.array(weight_values)

    for i in impacts:
        if i not in ['+', '-']:
            stop("Impacts must be either + or -")

    norm_matrix = criteria / np.sqrt((criteria ** 2).sum(axis=0))
    weighted_matrix = norm_matrix * weights

    ideal_best = []
    ideal_worst = []

    for idx, sign in enumerate(impacts):
        col = weighted_matrix.iloc[:, idx]
        if sign == '+':
            ideal_best.append(col.max())
            ideal_worst.append(col.min())
        else:
            ideal_best.append(col.min())
            ideal_worst.append(col.max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    dist_best = np.sqrt(((weighted_matrix - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted_matrix - ideal_worst) ** 2).sum(axis=1))

    scores = dist_worst / (dist_best + dist_worst)

    df["Topsis Score"] = scores
    df["Rank"] = scores.rank(ascending=False, method="first").astype(int)

    df.to_csv(output_file, index=False)
    print("TOPSIS completed successfully. Output saved to:", output_file)

if __name__ == "__main__":
    main()
