
import sys
import pandas as pd
import numpy as np


def topsis(input_file, weights, impacts, output_file):
    try:

        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print("Error: Input file not found")
        sys.exit(1)


    if df.shape[1] < 3:
        print("Error: Input file must contain three or more columns")
        sys.exit(1)

    data = df.iloc[:, 1:]


    if not np.all(data.applymap(np.isreal)):
        print("Error: From 2nd to last columns must contain numeric values only")
        sys.exit(1)

    weights = weights.split(",")
    impacts = impacts.split(",")


    if len(weights) != data.shape[1] or len(impacts) != data.shape[1]:
        print("Error: Number of weights, impacts, and columns must be the same")
        sys.exit(1)


    for i in impacts:
        if i not in ["+", "-"]:
            print("Error: Impacts must be either + or -")
            sys.exit(1)

    weights = np.array(weights, dtype=float)


    norm_data = data / np.sqrt((data ** 2).sum())


    weighted_data = norm_data * weights


    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == "+":
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
    df["Rank"] = df["Topsis Score"].rank(ascending=False).astype(int)


    df.to_csv(output_file, index=False)
    print("TOPSIS analysis completed successfully!")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage:")
        print("python topsis.py <InputDataFile> <Weights> <Impacts> <OutputFile>")
        sys.exit(1)

    topsis(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])