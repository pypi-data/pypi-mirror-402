import sys
import pandas as pd
import numpy as np
import os

def check_numeric(df):
    try:
        # Check from 2nd column (index 1) to the end
        df.iloc[:, 1:].astype(float)
        return True
    except ValueError:
        return False

def topsis(input_file, weights, impacts, result_file):
    try:
        # 1. Load Data
        try:
            df = pd.read_csv(input_file)
        except FileNotFoundError:
            print(f"Error: File '{input_file}' not found.")
            return

        # 2. Validation
        if len(df.columns) < 3:
            print("Error: Input file must contain three or more columns.")
            return

        if not check_numeric(df):
            print("Error: From 2nd to last columns must contain numeric values only.")
            return

        cols = len(df.columns) - 1 # excluding the first column
        
        weights = [float(w) for w in weights.split(',')]
        impacts = impacts.split(',')

        if len(weights) != cols or len(impacts) != cols:
            print("Error: The number of weights, number of impacts and number of columns (from 2nd to last columns) must be the same.")
            return

        if not all(i in ['+', '-'] for i in impacts):
            print("Error: Impacts must be either +ve or -ve.")
            return

        # 3. Algorithm
        # Vector Normalization
        df_calc = df.iloc[:, 1:].copy().astype(float) # Use a copy for calculation to preserve original data for output
        rss = np.sqrt((df_calc**2).sum())
        df_norm = df_calc / rss

        # Weighted Normalization
        df_weighted = df_norm * weights

        # Ideal Best and Worst
        ideal_best = []
        ideal_worst = []

        for i in range(cols):
            if impacts[i] == '+':
                ideal_best.append(df_weighted.iloc[:, i].max())
                ideal_worst.append(df_weighted.iloc[:, i].min())
            else:
                ideal_best.append(df_weighted.iloc[:, i].min())
                ideal_worst.append(df_weighted.iloc[:, i].max())

        # Euclidean Distance
        s_plus = np.sqrt(((df_weighted - ideal_best) ** 2).sum(axis=1))
        s_minus = np.sqrt(((df_weighted - ideal_worst) ** 2).sum(axis=1))

        # Performance Score
        total_dist = s_plus + s_minus
        performance_score = s_minus / total_dist
        
        # 4. Output
        df['Topsis Score'] = performance_score
        df['Rank'] = df['Topsis Score'].rank(ascending=False).astype(int)

        df.to_csv(result_file, index=False)
        print(f"Result file '{result_file}' created successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    if len(sys.argv) != 5:
        print("Usage: python <program.py> <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        print('Example: python topsis.py data.csv "1,1,1,2" "+,+,+,-" result.csv')
        return

    input_file = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    result_file = sys.argv[4]

    if not os.path.exists(input_file):
         print(f"Error: File '{input_file}' not found.")
         return

    topsis(input_file, weights, impacts, result_file)

if __name__ == "__main__":
    main()
