import sys
import os
import pandas as pd
import numpy as np

def validate_inputs():
    """
    Validates command line arguments and file content.
    Returns: DataFrame, Weights (list), Impacts (list), OutputFilename
    """
    # 1. Check for Correct number of parameters
    if len(sys.argv) != 5:
        print("Error: Incorrect number of parameters.")
        print("Usage: python topsis.py <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        print('Example: python topsis.py data.csv "1,1,1,2" "+,+,-,+" result.csv')
        sys.exit(1)

    input_file = sys.argv[1]
    weights_str = sys.argv[2]
    impacts_str = sys.argv[3]
    output_file = sys.argv[4]

    # 2. Handling of “File not Found” exception
    if not os.path.isfile(input_file):
        print(f"Error: The file '{input_file}' was not found.")
        sys.exit(1)

    # Read the file
    try:
        if input_file.endswith('.csv'):
            df = pd.read_csv(input_file)
        elif input_file.endswith('.xlsx'):
            df = pd.read_excel(input_file)
        else:
            print("Error: Input file must be .csv or .xlsx")
            sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    # 3. The input file must contain three or more columns
    if df.shape[1] < 3:
        print("Error: Input file must contain three or more columns.")
        sys.exit(1)

    # 4. From 2nd to last columns must contain numeric values only
    # (checking columns from index 1 to end)
    try:
        # Convert to numeric, coercing errors to NaN to check for non-numeric values
        data_cols = df.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')
        if data_cols.isnull().values.any():
            print("Error: From 2nd to last columns must contain numeric values only.")
            sys.exit(1)
    except Exception as e:
        print(f"Error validating numeric data: {e}")
        sys.exit(1)

    # Parse Weights and Impacts
    try:
        weights = [float(w) for w in weights_str.split(',')]
        impacts = impacts_str.split(',')
    except ValueError:
        print("Error: Weights must be numeric and separated by commas.")
        sys.exit(1)

    # 5. Impacts must be either +ve or -ve
    if not all(i in ['+', '-'] for i in impacts):
        print("Error: Impacts must be either '+' or '-'.")
        sys.exit(1)

    # 6. Check counts (Weights vs Impacts vs Columns)
    num_criteria = df.shape[1] - 1  # Excluding the first column
    if len(weights) != num_criteria or len(impacts) != num_criteria:
        print(f"Error: Number of weights ({len(weights)}), impacts ({len(impacts)}), and criteria ({num_criteria}) must be the same.")
        sys.exit(1)

    return df, weights, impacts, output_file

def topsis_calculation(df, weights, impacts):
    """
    Performs the TOPSIS calculation logic.
    """
    # Extract data part (excluding the first column which is usually Name/ID)
    data = df.iloc[:, 1:].values.astype(float)
    
    # 1. Normalize the decision matrix
    # sqrt(sum(x^2)) for each column
    root_sum_squares = np.sqrt((data**2).sum(axis=0))
    normalized_data = data / root_sum_squares

    # 2. Multiply by weights
    weighted_data = normalized_data * weights

    # 3. Calculate Ideal Best (V+) and Ideal Worst (V-)
    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(np.max(weighted_data[:, i]))
            ideal_worst.append(np.min(weighted_data[:, i]))
        else:  # impact is '-'
            ideal_best.append(np.min(weighted_data[:, i]))
            ideal_worst.append(np.max(weighted_data[:, i]))

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # 4. Euclidean distance from ideal best (S+) and ideal worst (S-)
    s_plus = np.sqrt(((weighted_data - ideal_best) ** 2).sum(axis=1))
    s_minus = np.sqrt(((weighted_data - ideal_worst) ** 2).sum(axis=1))

    # 5. Performance Score
    # P = S- / (S+ + S-)
    performance_score = s_minus / (s_plus + s_minus)

    return performance_score

def main():
    # Validation
    df, weights, impacts, output_file = validate_inputs()

    # Calculation
    try:
        scores = topsis_calculation(df, weights, impacts)
    except Exception as e:
        print(f"Error during calculation: {e}")
        sys.exit(1)

    # Append results to dataframe
    df['Topsis Score'] = scores
    
    # Calculate Rank (Higher score = Rank 1)
    df['Rank'] = df['Topsis Score'].rank(ascending=False).astype(int)

    # Save to output file
    try:
        df.to_csv(output_file, index=False)
        print(f"TOPSIS calculation completed successfully. Results saved to '{output_file}'.")
    except Exception as e:
        print(f"Error saving file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()