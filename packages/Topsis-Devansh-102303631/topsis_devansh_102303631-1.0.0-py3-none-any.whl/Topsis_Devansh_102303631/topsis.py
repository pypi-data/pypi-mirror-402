import pandas as pd
import numpy as np
import sys
import os

def check_inputs():
    if len(sys.argv) != 5:
        print("Usage: python <script_name> <InputDataFile> <Weights> <Impacts> <ResultFileName>")
        sys.exit(1)

    input_file = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    result_file = sys.argv[4]

    try:
        if not os.path.exists(input_file):
            raise FileNotFoundError("Input file not found.")
        
        # Read file based on extension
        if input_file.endswith('.csv'):
            df = pd.read_csv(input_file)
        elif input_file.endswith(('.xls', '.xlsx')):
            try:
                df = pd.read_excel(input_file)
            except ImportError:
                 # fallback if openpyxl is missing, strictly speaking not needed if environment is good but good for safety
                 print("Error: Library to read excel file might be missing or file is corrupted.")
                 sys.exit(1)
        else:
            print("Error: Input file must be .csv or .xlsx")
            sys.exit(1)

        if df.shape[1] < 3:
            print("Error: Input file must have at least 3 columns.")
            sys.exit(1)

        # Check for non-numeric values in criteria columns (from 2nd column onwards)
        try:
            df.iloc[:, 1:] = df.iloc[:, 1:].apply(pd.to_numeric)
        except ValueError:
            print("Error: From 2nd to last columns must contain numeric values only.")
            sys.exit(1)

        weights_list = [float(w) for w in weights.split(',')]
        impacts_list = impacts.split(',')

        if len(weights_list) != len(impacts_list) or len(weights_list) != (df.shape[1] - 1):
             print("Error: Number of weights, impacts and criteria columns must be same.")
             sys.exit(1)

        if not all(i in ['+', '-'] for i in impacts_list):
            print("Error: Impacts must be either '+' or '-'.")
            sys.exit(1)

        return df, weights_list, impacts_list, result_file

    except FileNotFoundError as fnf_error:
        print(f"Error: {fnf_error}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def topsis(df, weights, impacts):
    # Normalize the matrix
    df_norm = df.iloc[:, 1:].copy()
    data = df_norm.values.astype(float)
    
    # Root sum of squares
    rss = np.sqrt(np.sum(data**2, axis=0))
    
    # Avoid division by zero
    if (rss == 0).any():
        print("Error: Columns with all zero values found, cannot normalize.")
        sys.exit(1)

    normalized_data = data / rss

    # Multiply by weights
    weighted_data = normalized_data * weights

    # Ideal Best and Ideal Worst
    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(np.max(weighted_data[:, i]))
            ideal_worst.append(np.min(weighted_data[:, i]))
        else:
            ideal_best.append(np.min(weighted_data[:, i]))
            ideal_worst.append(np.max(weighted_data[:, i]))
            
    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # Euclidean distance
    dist_best = np.sqrt(np.sum((weighted_data - ideal_best)**2, axis=1))
    dist_worst = np.sqrt(np.sum((weighted_data - ideal_worst)**2, axis=1))

    # Topsis Score
    # Handle division by zero if dist_best + dist_worst is 0 (unlikely but possible)
    with np.errstate(divide='ignore', invalid='ignore'):
         score = dist_worst / (dist_best + dist_worst)
    
    score = np.nan_to_num(score) # fail-safe

    return score

def main():
    df, weights, impacts, result_file = check_inputs()
    
    scores = topsis(df, weights, impacts)
    
    df['Topsis Score'] = scores
    df['Rank'] = df['Topsis Score'].rank(ascending=False).astype(int)
    
    df.to_csv(result_file, index=False)
    print(f"Result file '{result_file}' generated successfully.")

if __name__ == "__main__":
    main()
