import sys
import pandas as pd
import numpy as np
import os

def error(msg):
    print("Error:", msg)
    sys.exit(1)

def main():
    if len(sys.argv) != 5:
        error("Usage: python topsis.py <InputDataFile> <Weights> <Impacts> <OutputFile>")

    input_file = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    output_file = sys.argv[4]

    if not os.path.exists(input_file):
        error("Input file not found!")

    try:
        if input_file.endswith(".csv"):
            df = pd.read_csv(input_file)
        elif input_file.endswith(".xlsx"):
            df = pd.read_excel(input_file)
        else:
            error("Input file must be .csv or .xlsx")
    except:
        error("Unable to read input file!")

    if df.shape[1] < 3:
        error("Input file must contain at least 3 columns!")

    data = df.iloc[:, 1:]

    for col in data.columns:
        if not pd.api.types.is_numeric_dtype(data[col]):
            error("From 2nd to last column, all values must be numeric!")

    weights = weights.split(",")
    impacts = impacts.split(",")

    if len(weights) != data.shape[1]:
        error("Number of weights must match number of criteria columns!")

    if len(impacts) != data.shape[1]:
        error("Number of impacts must match number of criteria columns!")

    try:
        weights = np.array([float(w) for w in weights])
    except:
        error("Weights must be numeric!")

    for imp in impacts:
        if imp not in ['+', '-']:
            error("Impacts must be either + or - only!")

    impacts = np.array(impacts)

    norm = np.sqrt((data ** 2).sum())
    norm_data = data / norm

    weighted_data = norm_data * weights

    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(weighted_data.iloc[:, i].max())
            ideal_worst.append(weighted_data.iloc[:, i].min())
        else:
            ideal_best.append(weighted_data.iloc[:, i].min())
            ideal_worst.append(weighted_data.iloc[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    dist_best = np.sqrt(((weighted_data - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted_data - ideal_worst) ** 2).sum(axis=1))

    topsis_score = dist_worst / (dist_best + dist_worst)

    df["Topsis Score"] = topsis_score
    df["Rank"] = df["Topsis Score"].rank(ascending=False, method="dense").astype(int)

    df.to_csv(output_file, index=False)

    print(" TOPSIS analysis completed successfully!")
    print(" Output saved to:", output_file)

if __name__ == "__main__":
    main()
