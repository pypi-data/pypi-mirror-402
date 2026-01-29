import sys
import os
import pandas as pd
import numpy as np


def topsis(input_file, weights, impacts, output_file):
    if not os.path.isfile(input_file):
        raise FileNotFoundError("File not Found")

    df = pd.read_csv(input_file)

    if df.shape[1] < 3:
        raise ValueError("Input file must contain three or more columns")

    weights_list = weights.split(",")
    impacts_list = impacts.split(",")

    try:
        matrix = df.iloc[:, 1:].values.astype(float)
    except ValueError:
        raise ValueError("From 2nd to last columns must contain numeric values only")

    criteria_count = df.shape[1] - 1

    if len(weights_list) != criteria_count or len(impacts_list) != criteria_count:
        raise ValueError("Number of weights, impacts and columns must be the same")

    for sign in impacts_list:
        if sign not in ["+", "-"]:
            raise ValueError("Impacts must be either + or -")

    try:
        weights_list = [float(w) for w in weights_list]
    except ValueError:
        raise ValueError("Weights must be numeric")

    normalised = matrix / np.sqrt((matrix ** 2).sum(axis=0))
    weighted_matrix = normalised * weights_list

    best = []
    worst = []

    for i in range(criteria_count):
        column = weighted_matrix[:, i]
        if impacts_list[i] == "+":
            best.append(column.max())
            worst.append(column.min())
        else:
            best.append(column.min())
            worst.append(column.max())

    best = np.array(best)
    worst = np.array(worst)

    distance_best = np.sqrt(((weighted_matrix - best) ** 2).sum(axis=1))
    distance_worst = np.sqrt(((weighted_matrix - worst) ** 2).sum(axis=1))

    topsis_score = distance_worst / (distance_best + distance_worst)

    df["Topsis Score"] = topsis_score
    df["Rank"] = df["Topsis Score"].rank(ascending=False).astype(int)

    df.to_csv(output_file, index=False)
    return df


def main():
    if len(sys.argv) != 5:
        print("Usage: topsis <inputFileName> <weights> <impacts> <resultFileName>")
        sys.exit(1)

    input_file = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    output_file = sys.argv[4]

    try:
        topsis(input_file, weights, impacts, output_file)
        print(f"Result saved to {output_file}")
    except FileNotFoundError as e:
        print(str(e))
        sys.exit(1)
    except ValueError as e:
        print(str(e))
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
