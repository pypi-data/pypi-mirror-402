import sys
import pandas as pd
import numpy as np
import os

def topsis(input_file, weights, impacts, output_file):
    # ---------- File existence check ----------
    if not os.path.exists(input_file):
        print("Error: Input file not found")
        sys.exit(1)

    # ---------- Read CSV ----------
    try:
        data = pd.read_csv(input_file)
    except Exception as e:
        print("Error reading file:", e)
        sys.exit(1)

    # ---------- Column count check ----------
    if data.shape[1] < 3:
        print("Error: Input file must contain three or more columns")
        sys.exit(1)

    # ---------- Extract numeric data ----------
    try:
        matrix = data.iloc[:, 1:].astype(float).values
    except ValueError:
        print("Error: From 2nd to last columns must contain numeric values only")
        sys.exit(1)

    # ---------- Parse weights & impacts ----------
    weights = list(map(float, weights.split(",")))
    impacts = impacts.split(",")

    if len(weights) != matrix.shape[1] or len(impacts) != matrix.shape[1]:
        print("Error: Number of weights and impacts must match number of columns")
        sys.exit(1)

    for impact in impacts:
        if impact not in ["+", "-"]:
            print("Error: Impacts must be either '+' or '-'")
            sys.exit(1)

    # ---------- Step 1: Normalize ----------
    norm_matrix = matrix / np.sqrt((matrix ** 2).sum(axis=0))

    # ---------- Step 2: Weighted normalization ----------
    weighted_matrix = norm_matrix * weights

    # ---------- Step 3: Ideal best & worst ----------
    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == "+":
            ideal_best.append(weighted_matrix[:, i].max())
            ideal_worst.append(weighted_matrix[:, i].min())
        else:
            ideal_best.append(weighted_matrix[:, i].min())
            ideal_worst.append(weighted_matrix[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # ---------- Step 4: Distance calculation ----------
    dist_best = np.sqrt(((weighted_matrix - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted_matrix - ideal_worst) ** 2).sum(axis=1))

    # ---------- Step 5: TOPSIS score ----------
    scores = dist_worst / (dist_best + dist_worst)

    # ---------- Ranking ----------
    ranks = (-scores).argsort().argsort() + 1

    # ---------- Output ----------
    data["Topsis Score"] = scores
    data["Rank"] = ranks

    data.to_csv(output_file, index=False)
    print("TOPSIS calculation completed successfully")
    print("Output file saved as:", output_file)


# ===================== MAIN =====================
if __name__ == "__main__":

    if len(sys.argv) != 5:
        print("Usage:")
        print("python topsis.py <InputDataFile> <Weights> <Impacts> <OutputFileName>")
        sys.exit(1)

    _, input_file, weights, impacts, output_file = sys.argv
    topsis(input_file, weights, impacts, output_file)



def main():
    import sys

    if len(sys.argv) != 5:
        print("Usage: topsis <inputfile> <weights> <impacts> <outputfile>")
        sys.exit(1)

    topsis(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
        sys.argv[4]
    )


if __name__ == "__main__":
    main()
