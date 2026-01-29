import sys
import os
import pandas as pd
import numpy as np

def error(msg):
    print(f"Error: {msg}")
    sys.exit(1)

def topsis_main():
    # 1. Check number of arguments
    if len(sys.argv) != 5:
        error("Usage: python topsis.py <InputFile> <Weights> <Impacts> <OutputFile>")

    input_file = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    output_file = sys.argv[4]

    # 2. File existence
    if not os.path.exists(input_file):
        error("Input file not found")

    # 3. Read CSV
    try:
        df = pd.read_csv(input_file)
    except:
        error("Unable to read input file")

    if df.shape[1] < 3:
        error("Input file must contain at least 3 columns")

    data = df.iloc[:, 1:]

    # 4. Numeric check
    try:
        data = data.astype(float)
    except:
        error("Columns from 2nd to last must be numeric")

    # 5. Weights & impacts
    weights = weights.split(",")
    impacts = impacts.split(",")

    if len(weights) != data.shape[1]:
        error("Number of weights must match number of criteria")

    if len(impacts) != data.shape[1]:
        error("Number of impacts must match number of criteria")

    try:
        weights = np.array(weights, dtype=float)
    except:
        error("Weights must be numeric")

    for i in impacts:
        if i not in ['+', '-']:
            error("Impacts must be either + or -")

    # 6. Normalize
    matrix = data.values
    norm = np.sqrt((matrix ** 2).sum(axis=0))
    normalized = matrix / norm

    # 7. Weighted matrix
    weighted = normalized * weights

    # 8. Ideal best & worst
    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(weighted[:, i].max())
            ideal_worst.append(weighted[:, i].min())
        else:
            ideal_best.append(weighted[:, i].min())
            ideal_worst.append(weighted[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # 9. Distances
    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    # 10. Topsis score
    score = dist_worst / (dist_best + dist_worst)

    df["Topsis Score"] = score
    df["Rank"] = df["Topsis Score"].rank(ascending=False).astype(int)

    df.to_csv(output_file, index=False)
    print("TOPSIS completed successfully")


