import sys
import pandas as pd
import numpy as np
import os

def error(msg):
    print("Error:", msg)
    sys.exit(1)

def main():
    if len(sys.argv) != 5:
        error("Usage: topsis <inputFile> <weights> <impacts> <outputFile>")

    input_file = sys.argv[1]
    weights = sys.argv[2].split(',')
    impacts = sys.argv[3].split(',')
    output_file = sys.argv[4]

    if not os.path.isfile(input_file):
        error("Input file not found")

    df = pd.read_csv(input_file)

    if df.shape[1] < 3:
        error("Input file must contain at least 3 columns")

    data = df.iloc[:, 1:].values

    try:
        data = data.astype(float)
    except:
        error("Criteria columns must contain numeric values only")

    weights = list(map(float, weights))

    if len(weights) != data.shape[1] or len(impacts) != data.shape[1]:
        error("Weights, impacts and criteria count must match")

    if not all(i in ['+', '-'] for i in impacts):
        error("Impacts must be '+' or '-' only")

    # Step 1: Normalize
    norm = np.sqrt((data ** 2).sum(axis=0))
    normalized = data / norm

    # Step 2: Weighted normalized
    weighted = normalized * weights

    # Step 3: Ideal best & worst
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

    # Step 4: Distance measures
    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    # Step 5: TOPSIS score
    score = dist_worst / (dist_best + dist_worst)

    df["Topsis Score"] = score
    df["Rank"] = df["Topsis Score"].rank(ascending=False).astype(int)

    df.to_csv(output_file, index=False)
    print("TOPSIS analysis completed successfully")

if __name__ == "__main__":
    main()
