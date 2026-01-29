import sys
import pandas as pd
import numpy as np
import os

def error(msg):
    print(f"Error: {msg}")
    sys.exit(1)

def main():
    if len(sys.argv) != 5:
        error("Usage: topsis <InputDataFile> <Weights> <Impacts> <OutputFile>")

    input_file = sys.argv[1]
    weights = sys.argv[2].split(",")
    impacts = sys.argv[3].split(",")
    output_file = sys.argv[4]

    if not os.path.exists(input_file):
        error("Input file not found")

    try:
        if input_file.endswith(".xlsx"):
            df = pd.read_excel(input_file)
        else:
            df = pd.read_csv(input_file)
    except:
        error("Unable to read input file")

    if df.shape[1] < 3:
        error("Input file must contain at least 3 columns")

    data = df.iloc[:, 1:]

    try:
        data = data.astype(float)
    except:
        error("Columns from 2nd to last must be numeric")

    n = data.shape[1]

    if len(weights) != n or len(impacts) != n:
        error("Number of weights, impacts and criteria must be same")

    weights = np.array(weights, dtype=float)

    for i in impacts:
        if i not in ['+', '-']:
            error("Impacts must be either '+' or '-'")

    norm = np.sqrt((data ** 2).sum())
    normalized = data / norm
    weighted = normalized * weights

    ideal_best, ideal_worst = [], []

    for i in range(n):
        if impacts[i] == '+':
            ideal_best.append(weighted.iloc[:, i].max())
            ideal_worst.append(weighted.iloc[:, i].min())
        else:
            ideal_best.append(weighted.iloc[:, i].min())
            ideal_worst.append(weighted.iloc[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    score = dist_worst / (dist_best + dist_worst)

    df["Topsis Score"] = score
    df["Rank"] = score.rank(ascending=False).astype(int)

    if output_file.endswith(".xlsx"):
        df.to_excel(output_file, index=False)
    else:
        df.to_csv(output_file, index=False)

    print("TOPSIS result generated successfully")

if __name__ == "__main__":
    main()
