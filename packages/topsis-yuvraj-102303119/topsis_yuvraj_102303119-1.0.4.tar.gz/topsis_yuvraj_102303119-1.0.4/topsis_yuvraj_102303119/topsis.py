import pandas as pd
import numpy as np
import sys
import os

def run():

    default_input = "data.csv"
    default_weights = "1,1,1"
    default_impacts = "+,+,+"
    default_output = "result.csv"

    if len(sys.argv) == 5:
        input_file = sys.argv[1]
        weights_str = sys.argv[2]
        impacts_str = sys.argv[3]
        result_file = sys.argv[4]
    elif len(sys.argv) == 1:
        print("No command-line arguments provided. Using default values.")
        input_file = default_input
        weights_str = default_weights
        impacts_str = default_impacts
        result_file = default_output
    else:
        print("Error: Invalid number of arguments.")
        print("Usage: python program.py <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        return

    if not os.path.isfile(input_file):
        print(f"Error: File '{input_file}' not found.")
        return

    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        print(f"Error: Could not read file. {e}")
        return

    if df.shape[1] < 3:
        print("Error: Input file must contain three or more columns.")
        return

    try:
        data = df.iloc[:, 1:].values.astype(float)
    except ValueError:
        print("Error: From 2nd to last columns must contain numeric values only.")
        return

    try:
        weights = np.array([float(w) for w in weights_str.split(',')])
    except ValueError:
        print("Error: Weights must be numeric and separated by commas.")
        return

    impacts = impacts_str.split(',')

    if len(weights) != data.shape[1] or len(impacts) != data.shape[1]:
        print("Error: Number of weights, impacts, and criteria columns must be the same.")
        return

    for impact in impacts:
        if impact not in ['+', '-']:
            print("Error: Impacts must be either '+' or '-'.")
            return

    norm_data = data / np.sqrt((data ** 2).sum(axis=0))
    weights = weights / weights.sum()
    weighted_norm = norm_data * weights

    ideal_best = np.zeros(data.shape[1])
    ideal_worst = np.zeros(data.shape[1])

    for i in range(data.shape[1]):
        if impacts[i] == '+':
            ideal_best[i] = np.max(weighted_norm[:, i])
            ideal_worst[i] = np.min(weighted_norm[:, i])
        else:
            ideal_best[i] = np.min(weighted_norm[:, i])
            ideal_worst[i] = np.max(weighted_norm[:, i])

    dist_best = np.sqrt(((weighted_norm - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted_norm - ideal_worst) ** 2).sum(axis=1))

    scores = dist_worst / (dist_best + dist_worst)

    df['Topsis Score'] = scores
    df['Rank'] = df['Topsis Score'].rank(method='dense', ascending=False).astype(int)

    df.to_csv(result_file, index=False)
    print(f"TOPSIS result saved to '{result_file}'")

if __name__ == "__main__":
    run()