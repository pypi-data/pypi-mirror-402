import sys
import pandas as pd
import numpy as np


def topsis(input_file, weights, impacts, output_file):
    """
    Perform TOPSIS analysis and save result to output CSV
    """

    # Read input file
    data = pd.read_csv(input_file)

    if data.shape[1] < 3:
        raise ValueError("Input file must contain at least three columns")

    matrix = data.iloc[:, 1:].values.astype(float)

    if len(weights) != matrix.shape[1]:
        raise ValueError("Number of weights must match number of criteria")

    if len(impacts) != matrix.shape[1]:
        raise ValueError("Number of impacts must match number of criteria")

    for impact in impacts:
        if impact not in ['+', '-']:
            raise ValueError("Impacts must be either '+' or '-'")

    # Normalize the decision matrix
    norm = np.sqrt((matrix ** 2).sum(axis=0))
    normalized_matrix = matrix / norm

    # Apply weights
    weighted_matrix = normalized_matrix * weights

    # Determine ideal best and worst
    ideal_best = np.zeros(matrix.shape[1])
    ideal_worst = np.zeros(matrix.shape[1])

    for i in range(matrix.shape[1]):
        if impacts[i] == '+':
            ideal_best[i] = weighted_matrix[:, i].max()
            ideal_worst[i] = weighted_matrix[:, i].min()
        else:
            ideal_best[i] = weighted_matrix[:, i].min()
            ideal_worst[i] = weighted_matrix[:, i].max()

    # Calculate distances
    distance_best = np.sqrt(((weighted_matrix - ideal_best) ** 2).sum(axis=1))
    distance_worst = np.sqrt(((weighted_matrix - ideal_worst) ** 2).sum(axis=1))

    # Calculate TOPSIS score
    topsis_score = distance_worst / (distance_best + distance_worst)

    # Add scores and rank
    data['Topsis Score'] = topsis_score
    data['Rank'] = data['Topsis Score'].rank(ascending=False, method='dense')

    # Save output
    data.to_csv(output_file, index=False)


def main():
    if len(sys.argv) != 5:
        print("Usage:")
        print("topsis <input_file> <weights> <impacts> <output_file>")
        print("Example:")
        print('topsis data.csv "1,1,1,1" "+,+,-,+" result.csv')
        sys.exit(1)

    input_file = sys.argv[1]
    weights = list(map(float, sys.argv[2].split(',')))
    impacts = sys.argv[3].split(',')
    output_file = sys.argv[4]

    topsis(input_file, weights, impacts, output_file)


if __name__ == "__main__":
    main()
