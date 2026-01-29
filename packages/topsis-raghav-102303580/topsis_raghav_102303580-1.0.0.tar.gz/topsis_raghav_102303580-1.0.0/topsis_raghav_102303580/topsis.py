import sys
import os
import pandas as pd
import numpy as np

def error(msg):
    print("Error:", msg)
    sys.exit(1)

def main():
    # ---------------- ARGUMENT CHECK ----------------
    if len(sys.argv) != 5:
        error("Usage: python topsis.py <InputFile> <Weights> <Impacts> <OutputFile>")

    input_file, weights, impacts, output_file = sys.argv[1:]

    # ---------------- FILE CHECK ----------------
    if not os.path.isfile(input_file):
        error("Input file not found")

    try:
        df = pd.read_csv(input_file)
    except:
        error("Unable to read CSV file")

    # ---------------- COLUMN CHECK ----------------
    if df.shape[1] < 3:
        error("Input file must contain at least 3 columns")

    # dropping 1 column
    data = df.iloc[:, 1:]
    criteria_count = data.shape[1]

    # ---------------- NUMERIC CHECK ----------------
    if not np.all(data.applymap(np.isreal)):
        error("From 2nd to last columns must be numeric")

    # ---------------- WEIGHTS & IMPACTS ----------------
    weights = weights.split(",")
    impacts = impacts.split(",")

    if len(weights) != criteria_count:
        error("Number of weights must equal number of criteria")

    if len(impacts) != criteria_count:
        error("Number of impacts must equal number of criteria")

    try:
        weights = np.array(list(map(float, weights)))
    except:
        error("Weights must be numeric")

    for i in impacts:
        if i not in ['+', '-']:
            error("Impacts must be either + or -")

    # ---------------- NORMALIZATION ----------------
    norm = np.sqrt((data ** 2).sum())
    normalized = data / norm

    # ---------------- WEIGHTED MATRIX ----------------
    weighted = normalized * weights

    # ---------------- IDEAL BEST & WORST ----------------
    ideal_best = []
    ideal_worst = []

    for i in range(criteria_count):
        if impacts[i] == '+':
            ideal_best.append(weighted.iloc[:, i].max())
            ideal_worst.append(weighted.iloc[:, i].min())
        else:
            ideal_best.append(weighted.iloc[:, i].min())
            ideal_worst.append(weighted.iloc[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # ---------------- DISTANCES ----------------
    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    # ---------------- TOPSIS SCORE ----------------
    score = dist_worst / (dist_best + dist_worst)

    df["Topsis Score"] = score
    df["Rank"] = score.rank(ascending=False).astype(int)

    df.to_csv(output_file, index=False)
    print("TOPSIS analysis completed successfully")

if __name__ == "__main__":
    main()


