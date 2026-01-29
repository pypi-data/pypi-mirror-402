import sys
import pandas as pd
import numpy as np

def main():
    # Check number of arguments
    if len(sys.argv) != 5:
        print("Usage: python topsis.py <InputFile> <Weights> <Impacts> <OutputFile>")
        sys.exit(1)

    input_file = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    output_file = sys.argv[4]

    # Read CSV file
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print("Error: Input file not found")
        sys.exit(1)

    # Check minimum columns
    if df.shape[1] < 3:
        print("Error: Input file must contain at least 3 columns")
        sys.exit(1)

    data = df.iloc[:, 1:]

    # Check numeric data
    if not np.all(data.applymap(np.isreal)):
        print("Error: All columns except first must be numeric")
        sys.exit(1)

    # Parse weights and impacts
    weights = list(map(float, weights.split(',')))
    impacts = impacts.split(',')

    if len(weights) != data.shape[1] or len(impacts) != data.shape[1]:
        print("Error: Number of weights, impacts and columns must match")
        sys.exit(1)

    for i in impacts:
        if i not in ['+', '-']:
            print("Error: Impacts must be + or -")
            sys.exit(1)

    # 🔹 STEP 5: Normalize the matrix
    norm_data = data / np.sqrt((data ** 2).sum())

    # 🔹 STEP 6: Apply weights
    weighted_data = norm_data * weights

    # 🔹 STEP 7: Ideal best and worst
    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(weighted_data.iloc[:, i].max())
            ideal_worst.append(weighted_data.iloc[:, i].min())
        else:
            ideal_best.append(weighted_data.iloc[:, i].min())
            ideal_worst.append(weighted_data.iloc[:, i].max())

    # 🔹 STEP 8: Distance calculation
    dist_best = np.sqrt(((weighted_data - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted_data - ideal_worst) ** 2).sum(axis=1))

    # 🔹 STEP 9: TOPSIS score
    scores = dist_worst / (dist_best + dist_worst)

    # 🔹 STEP 10: Rank
    df['Topsis Score'] = scores
    df['Rank'] = df['Topsis Score'].rank(ascending=False).astype(int)

    # Save output
    df.to_csv(output_file, index=False)
    print("TOPSIS analysis completed successfully")

if __name__ == "__main__":
    main()