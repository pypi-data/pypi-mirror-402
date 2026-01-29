import sys
import pandas as pd
import numpy as np
import os

def error(msg):
    print("Error:", msg)
    sys.exit(1)

def run():
    if len(sys.argv) != 5:
        error("Usage: topsis <inputfile> <weights> <impacts> <outputfile>")

    input_file = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    output_file = sys.argv[4]

    if not os.path.exists(input_file):
        error("Input file not found")

    df = pd.read_csv(input_file)

    if df.shape[1] < 3:
        error("File must have at least 3 columns")

    data = df.iloc[:,1:]

    try:
        data = data.astype(float)
    except:
        error("Non numeric values present")

    weights = list(map(float, weights.split(",")))
    impacts = impacts.split(",")

    if len(weights) != data.shape[1]:
        error("Weights count mismatch")

    if len(impacts) != data.shape[1]:
        error("Impacts count mismatch")

    for i in impacts:
        if i not in ['+','-']:
            error("Impacts must be + or -")

    norm = np.sqrt((data**2).sum())
    norm_data = data / norm
    weighted = norm_data * weights

    best = []
    worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            best.append(weighted.iloc[:,i].max())
            worst.append(weighted.iloc[:,i].min())
        else:
            best.append(weighted.iloc[:,i].min())
            worst.append(weighted.iloc[:,i].max())

    best = np.array(best)
    worst = np.array(worst)

    d_best = np.sqrt(((weighted - best)**2).sum(axis=1))
    d_worst = np.sqrt(((weighted - worst)**2).sum(axis=1))

    score = d_worst / (d_best + d_worst)

    df["Topsis Score"] = score
    df["Rank"] = df["Topsis Score"].rank(ascending=False).astype(int)

    df.to_csv(output_file, index=False)
    print("Output saved in", output_file)

if __name__ == "__main__":
    run()
