import pandas as pd
import numpy as np
import sys
import os

def main():
    # 1. Parameter Count Check
    if len(sys.argv) != 5:
        print("ERROR: Incorrect number of parameters.")
        print("Usage: python topsis.py <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        return

    input_file = sys.argv[1]
    weights_str = sys.argv[2]
    impacts_str = sys.argv[3]
    output_file = sys.argv[4]

    # 2. File Found Check
    if not os.path.isfile(input_file):
        print(f"ERROR: File '{input_file}' not found.")
        return

    try:
        # 3. Column Count Check (Must be >= 3)
        df = pd.read_csv(input_file)
        if df.shape[1] < 3:
            print("ERROR: Input file must contain three or more columns.")
            return

        # 4. Numeric Values Check (From 2nd column onwards)
        data = df.iloc[:, 1:].values
        if not np.issubdtype(data.dtype, np.number):
            print("ERROR: Columns from 2nd to last must contain numeric values only.")
            return

        # 5. Parse and Validate Weights and Impacts
        weights = [float(w) for w in weights_str.split(',')]
        impacts = impacts_str.split(',')

        # 6. Matching Lengths Check
        if len(weights) != data.shape[1] or len(impacts) != data.shape[1]:
            print("ERROR: Number of weights, impacts, and columns must be the same.")
            return

        # 7. Impact Symbol Check
        if not all(i in ['+', '-'] for i in impacts):
            print("ERROR: Impacts must be either '+' or '-'.")
            return

        # --- TOPSIS LOGIC ---
        # Step 1: Vectorized Normalization
        norm_data = data / np.sqrt((data**2).sum(axis=0))
        
        # Step 2: Weighting
        weighted_data = norm_data * weights
        
        # Step 3: Ideal Best/Worst
        v_best = np.array([np.max(weighted_data[:, i]) if impacts[i] == '+' else np.min(weighted_data[:, i]) for i in range(len(impacts))])
        v_worst = np.array([np.min(weighted_data[:, i]) if impacts[i] == '+' else np.max(weighted_data[:, i]) for i in range(len(impacts))])

        # Step 4: Euclidean Distances
        s_best = np.sqrt(((weighted_data - v_best)**2).sum(axis=1))
        s_worst = np.sqrt(((weighted_data - v_worst)**2).sum(axis=1))

        # Step 5: Performance Score
        score = s_worst / (s_best + s_worst)

        # 8. Output Result Formatting
        df['Topsis Score'] = score
        df['Rank'] = df['Topsis Score'].rank(ascending=False).astype(int)
        
        df.to_csv(output_file, index=False)
        print(f"SUCCESS: Results saved to {output_file}")

    except Exception as e:
        print(f"AN UNEXPECTED ERROR OCCURRED: {e}")

if __name__ == "__main__":
    main()
