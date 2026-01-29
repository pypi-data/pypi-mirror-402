import sys
import os
import pandas as pd
import numpy as np

def error(msg):
    print("Error:", msg)
    sys.exit(1)

def topsis(input_file, weights, impacts, output_file):

    # ---------- File existence ----------
    if not os.path.exists(input_file):
        error("Input file not found")

    # ---------- Read CSV ----------
    try:
        df = pd.read_csv(input_file)
    except:
        error("Invalid CSV file")

    # ---------- Minimum columns ----------
    if df.shape[1] < 3:
        error("Input file must contain three or more columns")

    data = df.iloc[:, 1:]

    # ---------- Numeric check ----------
    try:
      data = data.astype(float)
    except ValueError:
      error("From 2nd to last columns must contain numeric values only")

    data = data.astype(float)

    # ---------- Weights & Impacts ----------
    weights = weights.split(",")
    impacts = impacts.split(",")

    if len(weights) != data.shape[1]:
        error("Number of weights must be equal to number of criteria")

    if len(impacts) != data.shape[1]:
        error("Number of impacts must be equal to number of criteria")

    for i in impacts:
        if i not in ['+', '-']:
            error("Impacts must be either '+' or '-'")

    weights = np.array(weights, dtype=float)

    # ---------- Normalization ----------
    norm = data / np.sqrt((data ** 2).sum())

    # ---------- Weighted normalization ----------
    weighted = norm * weights

    # ---------- Ideal best & worst ----------
    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(weighted.iloc[:, i].max())
            ideal_worst.append(weighted.iloc[:, i].min())
        else:
            ideal_best.append(weighted.iloc[:, i].min())
            ideal_worst.append(weighted.iloc[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # ---------- Distance ----------
    s_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    s_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    # ---------- Score & Rank ----------
    score = s_worst / (s_best + s_worst)
    df["Topsis Score"] = score
    df["Rank"] = score.rank(ascending=False, method="dense").astype(int)

    # ---------- Output ----------
    df.to_csv(output_file, index=False)
    print("TOPSIS completed successfully")
    print("Output saved to:", output_file)

def main():
    if len(sys.argv) != 5:
       error("Usage: topsis <InputDataFile> <Weights> <Impacts> <OutputFile>")
    else:
        topsis(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4])
