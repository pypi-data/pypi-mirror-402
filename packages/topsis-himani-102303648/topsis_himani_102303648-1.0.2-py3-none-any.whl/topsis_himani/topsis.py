import sys
import os
import pandas as pd
import numpy as np

def topsis_run(input_file, weights, impacts, output_file):
    if not os.path.exists(input_file):
        print("Input file not found")
        return

    try:
        df = pd.read_csv(input_file)
    except:
        print("Invalid input file")
        return

    if df.shape[1] < 3:
        print("Input file must have at least 3 columns")
        return

    data = df.iloc[:, 1:]

    try:
        data = data.astype(float)
    except:
        print("All criteria values must be numeric")
        return

    w = weights.split(",")
    imp = impacts.split(",")

    if len(w) != data.shape[1] or len(imp) != data.shape[1]:
        print("Weights or impacts count mismatch")
        return

    try:
        w = np.array(w, dtype=float)
    except:
        print("Weights must be numeric")
        return

    for i in imp:
        if i not in ["+", "-"]:
            print("Impacts must be + or -")
            return

    # Normalization & weighted
    norm = np.sqrt((data ** 2).sum())
    weighted = (data / norm) * w

    best = []
    worst = []

    for i in range(len(imp)):
        if imp[i] == "+":
            best.append(weighted.iloc[:, i].max())
            worst.append(weighted.iloc[:, i].min())
        else:
            best.append(weighted.iloc[:, i].min())
            worst.append(weighted.iloc[:, i].max())

    best = np.array(best)
    worst = np.array(worst)

    d_best = np.sqrt(((weighted - best) ** 2).sum(axis=1))
    d_worst = np.sqrt(((weighted - worst) ** 2).sum(axis=1))

    score = d_worst / (d_best + d_worst)

    df["Topsis Score"] = score
    df["Rank"] = df["Topsis Score"].rank(ascending=False).astype(int)

    df.to_csv(output_file, index=False)
    print("TOPSIS completed successfully")

# CLI support
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 5:
        print("Usage: topsis.py <input_file> <weights> <impacts> <output_file>")
    else:
        topsis_run(args[1], args[2], args[3], args[4])
