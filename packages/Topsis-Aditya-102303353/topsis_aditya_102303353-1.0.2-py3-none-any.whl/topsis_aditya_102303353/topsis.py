import pandas as pd
import numpy as np
import sys
import os

def topsis():
    # 1. Check for correct number of parameters
    if len(sys.argv) != 5:
        print("Error: Wrong number of parameters.")
        print("Usage: python Topsis-Aditya-102303353.py <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        return

    input_file = sys.argv[1]
    weights_str = sys.argv[2]
    impacts_str = sys.argv[3]
    output_file = sys.argv[4]

    # 2. Handling File Not Found exception
    if not os.path.isfile(input_file):
        print(f"Error: File '{input_file}' not found.")
        return

    try:
        # Load the dataset
        df = pd.read_csv(input_file)

        # 3. Input file must contain three or more columns
        if len(df.columns) < 3:
            print("Error: Input file must contain three or more columns.")
            return

        # 4. From 2nd to last columns must contain numeric values only
        data = df.iloc[:, 1:].values
        if not np.issubdtype(data.dtype, np.number):
            print("Error: From 2nd to last columns must contain numeric values only.")
            return

        # 5. Parse weights and impacts and validate count
        try:
            weights = [float(w) for w in weights_str.split(',')]
        except ValueError:
            print("Error: Weights must be numeric and separated by commas.")
            return
            
        impacts = impacts_str.split(',')

        if len(weights) != data.shape[1] or len(impacts) != data.shape[1]:
            print("Error: Number of weights, impacts, and numeric columns must be the same.")
            return

        # 6. Impacts must be either + or -
        for impact in impacts:
            if impact not in ['+', '-']:
                print("Error: Impacts must be either '+' or '-'.")
                return

        # Working of TOPSIS

        # Step 1: Vector Normalization
        # Denominator = sqrt(sum(x^2)) for each column
        norm_data = data / np.sqrt((data**2).sum(axis=0))

        # Step 2: Weight the Normalized Matrix
        # Multiply normalized values by weights
        weighted_data = norm_data * weights

        # Step 3: Identify Ideal Best (V+) and Ideal Worst (V-)
        # Ideal Best depends on impact (+ is max, - is min)
        v_plus = []
        v_minus = []
        for i in range(len(impacts)):
            if impacts[i] == '+':
                v_plus.append(np.max(weighted_data[:, i]))
                v_minus.append(np.min(weighted_data[:, i]))
            else:
                v_plus.append(np.min(weighted_data[:, i]))
                v_minus.append(np.max(weighted_data[:, i]))

        # Step 4: Calculate Euclidean Distances
        # Measures distance from best (S+) and worst (S-)
        s_plus = np.sqrt(((weighted_data - v_plus)**2).sum(axis=1))
        s_minus = np.sqrt(((weighted_data - v_minus)**2).sum(axis=1))

        # Step 5: Calculate TOPSIS Score
        # Formula: Pi = S- / (S+ + S-)
        topsis_score = s_minus / (s_plus + s_minus)

        # Step 6: Rank the alternatives
        # Higher score results in a better rank
        df['Topsis Score'] = topsis_score
        df['Rank'] = df['Topsis Score'].rank(ascending=False).astype(int)

        # Save to result file
        df.to_csv(output_file, index=False)
        print(f"Success: Results saved to {output_file}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    topsis()