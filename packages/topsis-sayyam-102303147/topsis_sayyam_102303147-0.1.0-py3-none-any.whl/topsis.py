
import pandas as pd
import numpy as np
import sys

def topsis(data, weights, impacts):
    # Exclude the first column (e.g., Fund Name) which is not a criterion
    numeric_data = data.iloc[:, 1:]

    # Step 1: Normalize the decision matrix
    norm = np.sqrt((numeric_data ** 2).sum())
    normalized_data = numeric_data / norm

    # Step 2: Calculate the weighted normalized decision matrix
    weighted_data = normalized_data * weights

    # Step 3: Determine the ideal best and ideal worst solutions
    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(weighted_data.iloc[:, i].max())
            ideal_worst.append(weighted_data.iloc[:, i].min())
        else:  # impacts[i] == '-'
            ideal_best.append(weighted_data.iloc[:, i].min())
            ideal_worst.append(weighted_data.iloc[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # Step 4: Calculate the separation measure for each alternative
    dist_best = np.sqrt(((weighted_data - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted_data - ideal_worst) ** 2).sum(axis=1))

    # Step 5: Calculate the relative closeness to the ideal solution
    # Handle potential division by zero if dist_best + dist_worst is 0
    # (This usually means the alternative is identical to both ideal_best and ideal_worst, which is rare)
    score = dist_worst / (dist_best + dist_worst)
    return score

def main():
    if len(sys.argv) != 5:
        print("Usage: python topsis.py <input_csv_file> <weights> <impacts> <output_csv_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    weights_str = sys.argv[2]
    impacts_str = sys.argv[3]
    output_file = sys.argv[4]

    try:
        data = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading input CSV: {e}")
        sys.exit(1)

    try:
        weights = [int(w) for w in weights_str.split(',')]
    except ValueError:
        print("Error: Weights must be a comma-separated list of integers.")
        sys.exit(1)

    impacts = [i.strip() for i in impacts_str.split(',')]
    if not all(i in ['+', '-'] for i in impacts):
        print("Error: Impacts must be a comma-separated list of '+' or '-'.")
        sys.exit(1)

    # Check if number of weights/impacts matches number of criteria (data columns - 1 for ID)
    num_criteria = data.shape[1] - 1
    if len(weights) != num_criteria or len(impacts) != num_criteria:
        print(f"Error: Number of weights ({len(weights)}) and impacts ({len(impacts)}) must match the number of criteria ({num_criteria}) in the data.")
        sys.exit(1)

    # Calculate TOPSIS scores
    topsis_scores = topsis(data, weights, impacts)

    # Add Topsis Score and Rank to the DataFrame
    data["Topsis Score"] = topsis_scores
    data["Rank"] = data["Topsis Score"].rank(ascending=False).astype(int)

    try:
        data.to_csv(output_file, index=False)
        print(f"Results successfully saved to '{output_file}'")
    except Exception as e:
        print(f"Error saving output CSV to '{output_file}': {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
