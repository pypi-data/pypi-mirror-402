import sys
import pandas as pd
import numpy as np

def main():
    if len(sys.argv) != 5:
        print("Usage: topsis <InputDataFile> <Weights> <Impacts> <OutputFile>")
        sys.exit(1)

    input_file = sys.argv[1]
    weights = sys.argv[2].split(",")
    impacts = sys.argv[3].split(",")
    output_file = sys.argv[4]

    try:
        df = pd.read_csv(input_file)
    except:
        print("File not found")
        sys.exit(1)

    if df.shape[1] < 3:
        print("Input file must contain three or more columns")
        sys.exit(1)

    data = df.iloc[:, 1:]

    try:
        data = data.astype(float)
    except:
        print("From 2nd to last columns must contain numeric values only")
        sys.exit(1)

    if len(weights) != data.shape[1] or len(impacts) != data.shape[1]:
        print("Number of weights, impacts and criteria columns must be same")
        sys.exit(1)

    for i in impacts:
        if i not in ["+", "-"]:
            print("Impacts must be either + or -")
            sys.exit(1)

    weights = np.array(weights, dtype=float)

    norm = np.sqrt((data ** 2).sum())
    normalized = data / norm
    weighted = normalized * weights

    best = []
    worst = []

    for i in range(len(impacts)):
        if impacts[i] == "+":
            best.append(weighted.iloc[:, i].max())
            worst.append(weighted.iloc[:, i].min())
        else:
            best.append(weighted.iloc[:, i].min())
            worst.append(weighted.iloc[:, i].max())

    best = np.array(best)
    worst = np.array(worst)

    d_pos = np.sqrt(((weighted - best) ** 2).sum(axis=1))
    d_neg = np.sqrt(((weighted - worst) ** 2).sum(axis=1))

    score = d_neg / (d_pos + d_neg)

    df["Topsis Score"] = score
    df["Rank"] = score.rank(ascending=False).astype(int)

    df.to_csv(output_file, index=False)

if __name__ == "__main__":
    main()
