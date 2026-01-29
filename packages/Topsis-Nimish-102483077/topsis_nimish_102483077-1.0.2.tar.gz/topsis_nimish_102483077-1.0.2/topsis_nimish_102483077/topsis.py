import pandas as pd
import numpy as np
import sys

def topsis(input_file, weights, impacts):
    # Read CSV
    data = pd.read_csv(input_file)

    # Extract decision matrix (ignore first column)
    matrix = data.iloc[:, 1:].values.astype(float)

    # Convert inputs
    weights = np.array(weights, dtype=float)
    impacts = impacts.split(",")

    # Validation checks
    if matrix.shape[1] != len(weights):
        raise ValueError(
            f"Number of weights ({len(weights)}) does not match "
            f"number of criteria ({matrix.shape[1]})"
        )

    if matrix.shape[1] != len(impacts):
        raise ValueError(
            f"Number of impacts ({len(impacts)}) does not match "
            f"number of criteria ({matrix.shape[1]})"
        )

    for impact in impacts:
        if impact not in ['+', '-']:
            raise ValueError("Impacts must be either '+' or '-'")

    # Step 1: Normalize the matrix
    norm = np.sqrt((matrix ** 2).sum(axis=0))
    norm_matrix = matrix / norm

    # Step 2: Apply weights
    weighted = norm_matrix * weights

    # Step 3: Determine ideal best and worst
    ideal_best = np.zeros(weighted.shape[1])
    ideal_worst = np.zeros(weighted.shape[1])

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best[i] = weighted[:, i].max()
            ideal_worst[i] = weighted[:, i].min()
        else:
            ideal_best[i] = weighted[:, i].min()
            ideal_worst[i] = weighted[:, i].max()

    # Step 4: Calculate distances
    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    # Step 5: Calculate TOPSIS score
    scores = dist_worst / (dist_best + dist_worst)

    # Convert to pandas Series for ranking
    data["Topsis Score"] = scores
    data["Rank"] = pd.Series(scores).rank(ascending=False, method="dense").astype(int)

    # Save output
    data.to_csv("output.csv", index=False)
    print("TOPSIS results saved to output.csv")

def main():
    if len(sys.argv) != 4:
        print("Usage:")
        print("topsis <input_file.csv> <weights> <impacts>")
        sys.exit(1)

    input_file = sys.argv[1]
    weights = sys.argv[2].replace(" ", "").split(",")
    impacts = sys.argv[3].replace(" ", "")

    topsis(input_file, weights, impacts)

if __name__ == "__main__":
    main()
