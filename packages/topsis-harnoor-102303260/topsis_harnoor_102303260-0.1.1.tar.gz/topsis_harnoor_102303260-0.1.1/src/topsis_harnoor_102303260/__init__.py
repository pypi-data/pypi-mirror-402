import sys
import numpy as np
import pandas as pd
from argparse import ArgumentParser


def compute_topsis(table, wts, signs):
    values = table.iloc[:, 1:].to_numpy(dtype=float)

    col_norms = np.linalg.norm(values, axis=0)
    normalized = values / col_norms

    weighted_vals = normalized * wts

    best = np.zeros(weighted_vals.shape[1])
    worst = np.zeros(weighted_vals.shape[1])

    for idx, sgn in enumerate(signs):
        column = weighted_vals[:, idx]
        if sgn == "+":
            best[idx] = column.max()
            worst[idx] = column.min()
        else:
            best[idx] = column.min()
            worst[idx] = column.max()

    dist_best = np.sqrt(((weighted_vals - best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted_vals - worst) ** 2).sum(axis=1))

    return dist_worst / (dist_best + dist_worst)


def load_input(path):
    try:
        if path.lower().endswith(".csv"):
            return pd.read_csv(path)
        if path.lower().endswith(".xlsx"):
            return pd.read_excel(path)
    except Exception:
        pass

    print("Error: Failed to read input file")
    sys.exit(1)


def run():
    cli = ArgumentParser(prog="topsis", description="Compute TOPSIS rankings")
    cli.add_argument("input_file")
    cli.add_argument("weights")
    cli.add_argument("impacts")
    cli.add_argument("output_file")

    args = cli.parse_args()

    df = load_input(args.input_file)

    try:
        weight_vec = np.fromiter(
            (float(x) for x in args.weights.split(",")), dtype=float
        )
        impact_vec = args.impacts.split(",")
    except Exception:
        print("Error: Invalid weights or impacts")
        sys.exit(1)

    if len(weight_vec) != len(impact_vec):
        print("Error: Weights and impacts count must match")
        sys.exit(1)

    if df.shape[1] - 1 != len(weight_vec):
        print("Error: Criteria count mismatch")
        sys.exit(1)

    if any(x not in {"+", "-"} for x in impact_vec):
        print("Error: Impacts must be '+' or '-'")
        sys.exit(1)

    scores = compute_topsis(df, weight_vec, impact_vec)

    result = df.copy()
    result["Topsis Score"] = scores
    result["Rank"] = scores.argsort()[::-1].argsort() + 1

    result.to_csv(args.output_file, index=False)
    print(f"Output written to {args.output_file}")


if __name__ == "__main__":
    run()
