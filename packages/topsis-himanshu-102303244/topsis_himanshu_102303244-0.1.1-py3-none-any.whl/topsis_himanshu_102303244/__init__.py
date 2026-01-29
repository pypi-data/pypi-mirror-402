from argparse import ArgumentParser
import pandas as pd
import numpy as np
import sys


def topsis(df, weights, impacts):
    data = df.iloc[:, 1:].values.astype(float)

    norm = np.sqrt((data**2).sum(axis=0))
    norm_data = data / norm

    weighted = norm_data * weights

    ideal_best = []
    ideal_worst = []

    for j in range(weighted.shape[1]):
        if impacts[j] == "+":
            ideal_best.append(weighted[:, j].max())
            ideal_worst.append(weighted[:, j].min())
        else:
            ideal_best.append(weighted[:, j].min())
            ideal_worst.append(weighted[:, j].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    d_pos = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    d_neg = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    score = d_neg / (d_pos + d_neg)
    return score


def main() -> None:
    parser = ArgumentParser(description="TOPSIS command-line tool")

    parser.add_argument("input", help="Input CSV file")
    parser.add_argument("weights", help="Comma-separated weights (e.g. 1,2,3)")
    parser.add_argument("impacts", help="Comma-separated impacts (e.g. +,-,+)")
    parser.add_argument("output", help="Output CSV file")

    args = parser.parse_args()

    try:
        if args.input.endswith(".csv"):
            df = pd.read_csv(args.input)
        elif args.input.endswith(".xlsx"):
            df = pd.read_excel(args.input)
        else:
            print("Error: Unsupported file format. Use .csv or .xlsx")
            sys.exit(1)
    except Exception:
        print("Error: Unable to read input file")
        sys.exit(1)

    try:
        weights = np.array(list(map(float, args.weights.split(","))))
        impacts = args.impacts.split(",")
    except Exception:
        print(np.array(list(map(float, args.weights.split(",")))))
        print(args.impacts.split(","))
        print("Error: Invalid weights or impacts format")
        sys.exit(1)

    if len(weights) != len(impacts):
        print("Error: Weights and impacts length mismatch")
        sys.exit(1)

    if df.shape[1] - 1 != len(weights):
        print("Error: Number of weights must match number of criteria")
        sys.exit(1)

    if not all(i in ["+", "-"] for i in impacts):
        print("Error: Impacts must be + or -")
        sys.exit(1)

    scores = topsis(df, weights, impacts)

    df["Topsis Score"] = scores
    df["Rank"] = df["Topsis Score"].rank(ascending=False).astype(int)

    df.to_csv(args.output, index=False)
    print(f"Results saved to {args.output}")


if __name__ == "__main__":
    main()
