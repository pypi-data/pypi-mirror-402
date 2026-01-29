import sys
import pandas as pd
import numpy as np
import os

def main():
    if len(sys.argv) != 5:
        print("Usage: topsis <InputFile> <Weights> <Impacts> <OutputFile>")
        return

    input_file = sys.argv[1]
    weights_str = sys.argv[2]
    impacts_str = sys.argv[3]
    output_file = sys.argv[4]

    if not os.path.isfile(input_file):
        print("Error: Input file not found")
        return

    try:
        df = pd.read_csv(input_file)
    except:
        print("Error: Unable to read CSV file")
        return

    if df.shape[1] < 3:
        print("Error: Input file must contain at least 3 columns")
        return

    try:
        data = df.iloc[:, 1:].values.astype(float)
    except:
        print("Error: Criteria columns must be numeric")
        return

    weights = list(map(float, weights_str.split(',')))
    impacts = impacts_str.split(',')

    if len(weights) != data.shape[1] or len(impacts) != data.shape[1]:
        print("Error: Number of weights and impacts must match number of criteria")
        return

    if not all(i in ['+', '-'] for i in impacts):
        print("Error: Impacts must be + or -")
        return

    # Step 1: Normalize
    norm_data = data / np.sqrt((data ** 2).sum(axis=0))

    # Step 2: Apply weights
    weighted_data = norm_data * weights

    # Step 3: Ideal best and worst
    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(weighted_data[:, i].max())
            ideal_worst.append(weighted_data[:, i].min())
        else:
            ideal_best.append(weighted_data[:, i].min())
            ideal_worst.append(weighted_data[:, i].max())

    # Step 4: Distance measures
    s_best = np.sqrt(((weighted_data - ideal_best) ** 2).sum(axis=1))
    s_worst = np.sqrt(((weighted_data - ideal_worst) ** 2).sum(axis=1))

    # Step 5: TOPSIS score
    scores = s_worst / (s_best + s_worst)

    df['Topsis Score'] = scores
    df['Rank'] = df['Topsis Score'].rank(ascending=False)

    df.to_csv(output_file, index=False)
    print("Result saved to", output_file)
