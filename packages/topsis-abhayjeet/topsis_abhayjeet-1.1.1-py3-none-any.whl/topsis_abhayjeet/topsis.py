import sys
import pandas as pd
import numpy as np
import os

def error(msg):
    print("Error:", msg)
    sys.exit(1)

def main():
    # ---- Argument check ----
    if len(sys.argv) != 5:
        error("Usage: python topsis.py <InputFile> <Weights> <Impacts> <OutputFile>")

    input_file = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    output_file = sys.argv[4]

    # ---- File check ----
    if not os.path.isfile(input_file):
        error("Input file not found")

    # ---- Read file ----
    if input_file.endswith(".csv"):
        data = pd.read_csv(input_file)
    elif input_file.endswith(".xlsx"):
        data = pd.read_excel(input_file)
    else:
        error("Input file must be .csv or .xlsx")

    # ---- Column count ----
    if data.shape[1] < 3:
        error("Input file must contain at least 3 columns")

    # ---- Extract criteria ----
    criteria = data.iloc[:, 1:]

    # ---- Numeric check (FIXED) ----
    if not criteria.apply(lambda col: pd.api.types.is_numeric_dtype(col)).all():
        error("Criteria columns must be numeric")

    # ---- Weights & impacts ----
    weights = list(map(float, weights.split(",")))
    impacts = impacts.split(",")

    if len(weights) != criteria.shape[1]:
        error("Number of weights must equal number of criteria")

    if len(impacts) != criteria.shape[1]:
        error("Number of impacts must equal number of criteria")

    for i in impacts:
        if i not in ['+', '-']:
            error("Impacts must be '+' or '-' only")

    weights = np.array(weights)

    # ---- TOPSIS ----
    norm = criteria / np.sqrt((criteria ** 2).sum())
    weighted = norm * weights

    ideal_best, ideal_worst = [], []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(weighted.iloc[:, i].max())
            ideal_worst.append(weighted.iloc[:, i].min())
        else:
            ideal_best.append(weighted.iloc[:, i].min())
            ideal_worst.append(weighted.iloc[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    d_pos = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    d_neg = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    score = d_neg / (d_pos + d_neg)

    data["Topsis Score"] = score
    data["Rank"] = score.rank(ascending=False, method="dense").astype(int)

    # ---- Save output ----
    data.to_csv(output_file, index=False)
    print("TOPSIS completed successfully")

if __name__ == "__main__":
    main()
