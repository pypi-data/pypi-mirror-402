import pandas as pd
import sys
import os

def topsis(input_file, weights, impacts, result_file):
    # Check if input file exists
    try:
        df = pd.read_excel(input_file)
    except FileNotFoundError:
        print("Error: File not found.")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # Check Input Data validity
    if df.shape[1] < 3:
        print("Error: Input file must contain at least 3 columns.")
        return

    # Separate non-numeric columns (assuming first column is ID/Name)
    # The assignment usually expects only the first column to be non-numeric.
    dataset = df.iloc[:, 1:].copy()
    
    # Check if columns are numeric
    try:
        dataset = dataset.astype(float)
    except ValueError:
        print("Error: Columns from 2nd to last must contain numeric values only.")
        return

    # Process Weights and Impacts
    try:
        weights = [float(w) for w in weights.split(',')]
        impacts = impacts.split(',')
    except ValueError:
        print("Error: Weights must be numeric and separated by commas.")
        return

    # Input Validation
    if len(weights) != dataset.shape[1] or len(impacts) != dataset.shape[1]:
        print("Error: Number of weights, impacts, and criteria columns must be the same.")
        return

    if not all(i in ['+', '-'] for i in impacts):
        print("Error: Impacts must be either '+' or '-'.")
        return

    # TOPSIS Algorithm
    # Vector Normalization
    dataset_norm = dataset / ((dataset**2).sum())**0.5

    dataset_weighted = dataset_norm * weights

    ideal_best = []
    ideal_worst = []

    for i in range(dataset.shape[1]):
        if impacts[i] == '-':
            ideal_best.append(dataset_weighted.iloc[:, i].min())
            ideal_worst.append(dataset_weighted.iloc[:, i].max())
        else:
            ideal_best.append(dataset_weighted.iloc[:, i].max())
            ideal_worst.append(dataset_weighted.iloc[:, i].min())

    # Euclidean Distances
    dist_best = ((dataset_weighted - ideal_best)**2).sum(axis=1)**0.5
    dist_worst = ((dataset_weighted - ideal_worst)**2).sum(axis=1)**0.5

    # Performance Score
    # Handle potential division by zero
    performance = dist_worst/(dist_best + dist_worst)
    df['Topsis Score'] = performance
    
    # Rank (Descending order)
    df['Rank'] = df['Topsis Score'].rank(ascending=False)

    try:
        df.to_csv(result_file, index=False)
        print(f"TOPSIS analysis completed successfully. Results saved to {result_file}")
    except Exception as e:
        print(f"Error saving file: {e}")

def main():
    # Check arguments
    if len(sys.argv) != 5:
        print("Error: Wrong number of arguments.")
        print("Usage: topsis <InputDataFile> <Weights> <Impacts> <ResultFileName>")
        print('Example: topsis data.xlsx "1,1,1,1" "+,+,-,+" result.csv')
        sys.exit()
    
    # Call the function
    topsis(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])

if __name__ == "__main__":
    main()