import sys
import os
import pandas as pd
import numpy as np

def error(msg):
    print("Error:", msg)
    sys.exit(1)

def main():
    if len(sys.argv) != 5:
        error("Usage: topsis <InputDataFile> <Weights> <Impacts> <OutputFile>")

    input_file = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    output_file = sys.argv[4]

    if not os.path.isfile(input_file):
        error("Input file does not exist")

    df = pd.read_csv(input_file)

    if df.shape[1] < 3:
        error("Input file must contain at least 3 columns")

    data = df.iloc[:, 1:]

    if not all(data.map(np.isreal).all()):
        error("Columns from 2nd to last must be numeric")

    weights = list(map(float, weights.split(',')))
    impacts = impacts.split(',')

    if len(weights) != data.shape[1]:
        error("Number of weights must match number of criteria")

    if len(impacts) != data.shape[1]:
        error("Number of impacts must match number of criteria")

    for i in impacts:
        if i not in ['+', '-']:
            error("Impacts must be either + or -")

    norm = np.sqrt((data ** 2).sum())
    normalized = data / norm
    weighted = normalized * weights

    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(weighted.iloc[:, i].max())
            ideal_worst.append(weighted.iloc[:, i].min())
        else:
            ideal_best.append(weighted.iloc[:, i].min())
            ideal_worst.append(weighted.iloc[:, i].max())

    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    score = dist_worst / (dist_best + dist_worst)

    df["Topsis Score"] = score
    df["Rank"] = score.rank(ascending=False).astype(int)

    df.to_csv(output_file, index=False)
    print("TOPSIS analysis completed successfully")
