
import sys
import pandas as pd
import numpy as np

def main():
    if len(sys.argv) != 5:
        print("Usage: topsis <inputfile> <weights> <impacts> <outputfile>")
        sys.exit(1)

    input_file, weights, impacts, output_file = sys.argv[1:]

    df = pd.read_csv(input_file)
    data = df.iloc[:, 1:].astype(float).values

    w = np.array(list(map(float, weights.split(","))))
    impacts = impacts.split(",")

    norm = data / np.sqrt((data ** 2).sum(axis=0))
    weighted = norm * w

    ideal_best = weighted.max(axis=0)
    ideal_worst = weighted.min(axis=0)

    for i, imp in enumerate(impacts):
        if imp == "-":
            ideal_best[i], ideal_worst[i] = ideal_worst[i], ideal_best[i]

    d_pos = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    d_neg = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    score = d_neg / (d_pos + d_neg)
    rank = score.argsort()[::-1].argsort() + 1

    df["Topsis Score"] = score
    df["Rank"] = rank
    df.to_csv(output_file, index=False)

    print("Result saved to", output_file)
