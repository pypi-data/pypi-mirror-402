import sys
import pandas as pd
import numpy as np

def main():
    if len(sys.argv) != 5:
        print("Usage: topsis input.csv weights impacts output.csv")
        return
    topsis(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])


def topsis(input_file, weights, impacts, output_file):

    # read file
    try:
        df = pd.read_csv(input_file)
    except:
        print("File not found")
        return

    # column check
    if df.shape[1] < 3:
        print("Minimum 3 columns required")
        return

    # numeric check
    try:
        data = df.iloc[:, 1:].astype(float).values
    except:
        print("Non-numeric data found")
        return

    # weights impacts
    try:
        weights = [float(i) for i in weights.split(",")]
    except:
        print("Invalid weights")
        return

    impacts = impacts.split(",")

    if len(weights) != data.shape[1] or len(impacts) != data.shape[1]:
        print("Mismatch in weights/impacts")
        return

    for i in impacts:
        if i not in ["+", "-"]:
            print("Invalid impact")
            return

    # normalization
    norm = np.sqrt((data ** 2).sum(axis=0))
    norm_data = data / norm

    # weighted matrix
    w_data = norm_data * weights

    # best worst
    best = []
    worst = []

    for i in range(len(impacts)):
        if impacts[i] == "+":
            best.append(max(w_data[:, i]))
            worst.append(min(w_data[:, i]))
        else:
            best.append(min(w_data[:, i]))
            worst.append(max(w_data[:, i]))

    # distance
    d_plus = np.sqrt(((w_data - best) ** 2).sum(axis=1))
    d_minus = np.sqrt(((w_data - worst) ** 2).sum(axis=1))

    # score
    score = d_minus / (d_plus + d_minus)

    # rank
    df["Topsis Score"] = score
    df["Rank"] = df["Topsis Score"].rank(ascending=False)

    # save
    df.to_csv(output_file, index=False)

    print("TOPSIS done")

