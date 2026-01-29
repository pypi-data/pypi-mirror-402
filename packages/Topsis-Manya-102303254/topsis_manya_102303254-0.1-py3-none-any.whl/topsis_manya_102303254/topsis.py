
import sys
import pandas as pd
import numpy as np

def topsis(input_file, weights, impacts, output_file):

    if input_file.endswith(".csv"):
        data = pd.read_csv(input_file)
    elif input_file.endswith(".xlsx"):
        data = pd.read_excel(input_file)
    else:
        print("Error: Input file must be CSV or Excel")
        sys.exit(1)

    if data.shape[1] < 3:
        print("Error: Input file must contain three or more columns")
        sys.exit(1)

    values = data.iloc[:, 1:].values.astype(float)

    weights = np.array([float(w) for w in weights.split(",")])
    impacts = impacts.split(",")

    if len(weights) != values.shape[1]:
        print("Error: Number of weights must match number of criteria")
        sys.exit(1)

    if len(impacts) != values.shape[1]:
        print("Error: Number of impacts must match number of criteria")
        sys.exit(1)

    for i in impacts:
        if i not in ['+', '-']:
            print("Error: Impacts must be + or -")
            sys.exit(1)

    norm = values / np.sqrt((values ** 2).sum(axis=0))
    weighted = norm * weights

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

    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    score = dist_worst / (dist_best + dist_worst)

    data["Topsis Score"] = score
    data["Rank"] = data["Topsis Score"].rank(ascending=False).astype(int)

    data.to_csv(output_file, index=False)
    print(f"Output saved to {output_file}")


def main():
    if len(sys.argv) != 5:
        print("Usage: topsis <InputDataFile> <Weights> <Impacts> <OutputResultFile>")
        sys.exit(1)

    _, input_file, weights, impacts, output_file = sys.argv
    topsis(input_file, weights, impacts, output_file)


if __name__ == "__main__":
    main()
