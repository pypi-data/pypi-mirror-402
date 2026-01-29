import sys
import os
import numpy as np
import pandas as pd


def main(argv=None):
    argv = argv if argv is not None else sys.argv

    # to tell about how to write the command in terminal
    if len(argv) != 5:
        print("Usage: python topsis.py <input> <weights> <impacts> <output>")
        return 1

    _, infile, weights_str, impacts_str, outfile = argv

    ext = os.path.splitext(infile)[1].lower()
    if ext in (".xls", ".xlsx"):
        df = pd.read_excel(infile)
    else:
        df = pd.read_csv(infile)

    criteria = df.iloc[:, 1:].apply(pd.to_numeric, errors="coerce")

    if criteria.isnull().any().any():
        print("Error: Non-numeric values found in criteria columns")
        return 1

    D = criteria.values.astype(float)

    # Weights & impacts (important to be correctly written in the terminal)
    weights = np.array([float(x) for x in weights_str.split(",")])
    impacts = np.array([x.strip() for x in impacts_str.split(",")])

    # TOPSIS calculation method and steps
    # Normalization
    norm = np.linalg.norm(D, axis=0)
    D_norm = D / norm

    # Weighted normalized matrix
    W = D_norm * weights

    # Ideal best and worst
    ideal_best = np.where(impacts == "+", W.max(axis=0), W.min(axis=0))
    ideal_worst = np.where(impacts == "+", W.min(axis=0), W.max(axis=0))

    # Separation measures
    S_plus = np.sqrt(((W - ideal_best) ** 2).sum(axis=1))
    S_minus = np.sqrt(((W - ideal_worst) ** 2).sum(axis=1))

    # Topsis score & ranking
    score = S_minus / (S_plus + S_minus)
    df["Topsis Score"] = np.round(score, 6)
    df["Rank"] = df["Topsis Score"].rank(method="dense", ascending=False).astype(int)

    # Save output
    df.to_csv(outfile, index=False)
    print("Result saved to:", outfile)
    return 0


if __name__ == "__main__":
    sys.exit(main())
