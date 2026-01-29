import sys
import pandas as pd
import numpy as np

def topsis(input_file, weights, impacts, output_file):

    df = pd.read_csv(input_file)

    if df.shape[1] < 3:
        raise Exception("Input file must contain at least 3 columns")

    data = df.iloc[:, 1:]

    if not all(data.dtypes.apply(lambda x: np.issubdtype(x, np.number))):
        raise Exception("Columns from 2nd to last must be numeric")

    weights = np.array(weights)
    impacts = np.array(impacts)

    if len(weights) != data.shape[1]:
        raise Exception("Number of weights must match number of criteria")

    if len(impacts) != data.shape[1]:
        raise Exception("Number of impacts must match number of criteria")

    if not all(i in ['+', '-'] for i in impacts):
        raise Exception("Impacts must be + or -")

    norm = data / np.sqrt((data ** 2).sum())
    weighted = norm * weights

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
    df['Topsis Score'] = score
    df['Rank'] = df['Topsis Score'].rank(ascending=False)

    df.to_csv(output_file, index=False)
    print("TOPSIS calculation completed successfully.")


# =========================
# CLI ENTRY POINT
# =========================
def main():
    if len(sys.argv) != 5:
        print("Usage: topsis <input_file> <weights> <impacts> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    weights = list(map(float, sys.argv[2].split(",")))
    impacts = sys.argv[3].split(",")
    output_file = sys.argv[4]

    try:
        topsis(input_file, weights, impacts, output_file)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

