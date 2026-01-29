import sys
import numpy as np
import pandas as pd
from argparse import ArgumentParser


def topsis_score(dataframe, weights, impacts):
    matrix = dataframe.iloc[:, 1:].astype(float).values

    # normalize columns
    norms = np.sqrt((matrix**2).sum(axis=0))
    scaled = matrix / norms

    # apply weights
    weighted = scaled * weights

    ideal = []
    anti_ideal = []

    for col_idx in range(weighted.shape[1]):
        col = weighted[:, col_idx]
        if impacts[col_idx] == "+":
            ideal.append(col.max())
            anti_ideal.append(col.min())
        else:
            ideal.append(col.min())
            anti_ideal.append(col.max())

    ideal = np.array(ideal)
    anti_ideal = np.array(anti_ideal)

    d_pos = np.linalg.norm(weighted - ideal, axis=1)
    d_neg = np.linalg.norm(weighted - anti_ideal, axis=1)

    return d_neg / (d_pos + d_neg)


def read_dataset(file_path):
    ext = file_path.lower()
    try:
        if ext.endswith("csv"):
            return pd.read_csv(file_path)
        elif ext.endswith("xlsx"):
            return pd.read_excel(file_path)
    except Exception:
        print("Error: Unable to load the input file")
        sys.exit(1)

    print("Error: Unsupported file format")
    sys.exit(1)


def main():
    parser = ArgumentParser(description="TOPSIS ranking utility")
    parser.add_argument("source")
    parser.add_argument("weight_list")
    parser.add_argument("impact_list")
    parser.add_argument("destination")

    args = parser.parse_args()
    df = read_dataset(args.source)

    try:
        weights = np.array([float(w) for w in args.weight_list.split(",")])
        impacts = args.impact_list.split(",")
    except Exception:
        print("Error: Failed to parse weights or impacts")
        sys.exit(1)

    if df.shape[1] != len(weights) + 1:
        print("Error: Number of criteria does not match")
        sys.exit(1)

    if len(weights) != len(impacts):
        print("Error: Weights and impacts length mismatch")
        sys.exit(1)

    if not all(i in ("+", "-") for i in impacts):
        print("Error: Impacts must be '+' or '-' only")
        sys.exit(1)

    scores = topsis_score(df, weights, impacts)

    output = df.copy()
    output["Topsis Score"] = scores
    output["Rank"] = (-scores).argsort().argsort() + 1

    output.to_csv(args.destination, index=False)
    print("Results saved to", args.destination)


if __name__ == "__main__":
    main()
