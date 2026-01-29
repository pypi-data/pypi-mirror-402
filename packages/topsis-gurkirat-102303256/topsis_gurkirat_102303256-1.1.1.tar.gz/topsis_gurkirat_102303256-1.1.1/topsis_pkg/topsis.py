# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import sys
import os

def topsis():
    # 1. Check for correct number of parameters
    if len(sys.argv) != 5:
        print("Error: Wrong number of parameters.")
        print("<InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        return

    input_file = sys.argv[1]
    weights_raw = sys.argv[2]
    impacts_raw = sys.argv[3]
    result_file = sys.argv[4]

    # 2. Handling of "File not Found" exception
    if not os.path.isfile(input_file):
        print(f"Error: File '{input_file}' not found.")
        return

    try:
        ## Support for both Excel and CSV
        if input_file.endswith('.xlsx'):
            df = pd.read_excel(input_file)
        else:
            df = pd.read_csv(input_file, encoding='latin1')
            
        # 3. Input file must contain three or more columns
        if len(df.columns) < 3:
            print("Error: Input file must contain three or more columns.")
            return
            
        # 4. From 2nd to last columns must contain numeric values only 
        data = df.iloc[:, 1:].values
        try:
            data = data.astype(float)
        except ValueError:
            print("Error: From 2nd to last columns must contain numeric values only.")
            return

        # 5. Process weights and impacts
        try:
            weights = [float(w) for w in weights_raw.split(',')]
        except ValueError:
            print("Error: Weights must be comma-separated numbers.")
            return
            
        impacts = impacts_raw.split(',')

        # 6. Check if number of weights, impacts, and columns match
        num_criteria = df.shape[1] - 1
        if len(weights) != num_criteria or len(impacts) != num_criteria:
            print("Error: Number of weights, impacts, and numeric columns must be the same.")
            return

        # 7. Impacts must be either + or -
        for i in impacts:
            if i not in ['+', '-']:
                print("Error: Impacts must be either '+' or '-'.")
                return

        # --- TOPSIS Logic ---
        # Vector Normalization
        norm_data = data / np.sqrt((data**2).sum(axis=0))

        # Weighted Normalized Matrix
        weighted_data = norm_data * weights

        # Ideal Best and Ideal Worst
        p_ideal = []
        n_ideal = []
        for i in range(len(impacts)):
            if impacts[i] == '+':
                p_ideal.append(max(weighted_data[:, i]))
                n_ideal.append(min(weighted_data[:, i]))
            else:
                p_ideal.append(min(weighted_data[:, i]))
                n_ideal.append(max(weighted_data[:, i]))

        # Distance from Ideal Best and Worst
        s_best = np.sqrt(((weighted_data - p_ideal)**2).sum(axis=1))
        s_worst = np.sqrt(((weighted_data - n_ideal)**2).sum(axis=1))

        # Performance Score
        performance_score = s_worst / (s_best + s_worst)

        # Append results to dataframe
        df['Topsis Score'] = performance_score
        df['Rank'] = df['Topsis Score'].rank(ascending=False).astype(int)
        
        # --- NEW: Print ONLY Score and Rank ---
        print("\n--- TOPSIS RESULTS (Score & Rank) ---")
        # This filters the view to show only the last two columns
        print(df[['Topsis Score', 'Rank']].to_string(index=False))
        print("-------------------------------------\n")

        # Save to CSV
        df.to_csv(result_file, index=False)
        print(f"Success: Results saved to {result_file}")
        
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    topsis()