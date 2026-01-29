import sys
import pandas as pd
import numpy as np

def topsis(input_file, weights, impacts, output_file):
    # Read input file (CSV or Excel)
    try:
        data = pd.read_csv(input_file)
    except Exception:
        try:
            data = pd.read_excel(input_file)
        except Exception:
            print("Error: Input file must be a valid CSV or Excel file.")
            sys.exit(1)

    # Check minimum number of columns
    if data.shape[1] < 3:
        print("Error: Input file must contain at least three columns.")
        sys.exit(1)

    # Extract criteria columns and ensure numeric values
    criteria = data.iloc[:, 1:]
    try:
        criteria = criteria.astype(float)
    except ValueError:
        print("Error: All criteria values must be numeric.")
        sys.exit(1)

    # Parse weights and impacts
    weights = weights.split(',')
    impacts = impacts.split(',')

    if len(weights) != criteria.shape[1]:
        print("Error: Number of weights must match number of criteria.")
        sys.exit(1)

    if len(impacts) != criteria.shape[1]:
        print("Error: Number of impacts must match number of criteria.")
        sys.exit(1)

    if not all(i in ['+', '-'] for i in impacts):
        print("Error: Impacts must be either '+' or '-'.")
        sys.exit(1)

    weights = np.array(weights, dtype=float)

    # Normalize weights
    weights = weights / weights.sum()

    # Step 1: Normalize the decision matrix
    norm = criteria / np.sqrt((criteria ** 2).sum())

    # Step 2: Weighted normalized matrix
    weighted = norm * weights

    # Step 3: Determine ideal best and worst
    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(weighted.iloc[:, i].max())
            ideal_worst.append(weighted.iloc[:, i].min())
        else:
            ideal_best.append(weighted.iloc[:, i].min())
            ideal_worst.append(weighted.iloc[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # Step 4: Calculate distances
    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    # Step 5: Calculate TOPSIS score
    score = dist_worst / (dist_best + dist_worst + 1e-9)

    # Add results to dataframe
    data['Topsis Score'] = score
    data['Rank'] = data['Topsis Score'].rank(ascending=False).astype(int)

    # Save output file (CSV or Excel)
    try:
        data.to_csv(output_file, index=False)
    except Exception:
        try:
            data.to_excel(output_file, index=False)
        except Exception:
            print("Error: Output file must be a valid CSV or Excel file.")
            sys.exit(1)

    print("Result saved to", output_file)


def main():
    if len(sys.argv) != 5:
        print("Error: Incorrect number of parameters.")
        print("Usage: topsis <inputFile> <weights> <impacts> <outputFile>")
        sys.exit(1)

    topsis(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])


if __name__ == "__main__":
    main()