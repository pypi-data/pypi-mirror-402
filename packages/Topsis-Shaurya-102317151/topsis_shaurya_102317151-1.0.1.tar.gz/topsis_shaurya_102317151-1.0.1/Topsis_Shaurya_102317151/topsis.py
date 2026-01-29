import pandas as pd
import numpy as np
import sys
import os

def main():
    # Check if number of parameters is correct
    if len(sys.argv) != 5:
        print("Usage: python topsis.py <InputDataFile> <Weights> <Impacts> <ResultFileName>")
        return

    # Getting arguments from command line
    file_name = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    result_file = sys.argv[4]

    # File not found handling
    if not os.path.exists(file_name):
        print("Error: File not found.")
        return

    try:
        df = pd.read_csv(file_name)
    except:
        print("Error: Could not read file.")
        return

    # Check for 3 or more columns
    if df.shape[1] < 3:
        print("Error: Input file must contain three or more columns.")
        return

    # Handling non-numeric values
    # We take a copy of data to work on, starting from 2nd column
    data = df.iloc[:, 1:].values
    rows, cols = data.shape

    # Check if all values are numeric
    try:
        data = data.astype(float)
    except ValueError:
        print("Error: Columns from 2nd to last must contain numeric values only.")
        return

    # Handling weights and impacts
    try:
        w = [float(i) for i in weights.split(',')]
        im = impacts.split(',')
    except:
        print("Error: Weights and Impacts must be separated by ','")
        return

    # Checking lengths
    if len(w) != cols or len(im) != cols:
        print("Error: Number of weights, impacts and columns must be same.")
        return

    # Checking impacts signs
    for i in im:
        if i not in ['+', '-']:
            print("Error: Impacts must be either +ve or -ve.")
            return

    # --- TOPSIS Logic Starts ---
    
    # 1. Normalize
    # Calculate square root of sum of squares
    rss = []
    for j in range(cols):
        s = 0
        for i in range(rows):
            s += data[i][j]**2
        rss.append(np.sqrt(s))

    # Divide by rss to get normalized matrix
    for i in range(rows):
        for j in range(cols):
            data[i][j] = data[i][j] / rss[j]

    # 2. Multiply by weights
    for i in range(rows):
        for j in range(cols):
            data[i][j] = data[i][j] * w[j]

    # 3. Find Ideal Best and Worst
    best = []
    worst = []

    for j in range(cols):
        col_vals = data[:, j]
        if im[j] == '+':
            best.append(max(col_vals))
            worst.append(min(col_vals))
        else:
            best.append(min(col_vals))
            worst.append(max(col_vals))

    # 4. Euclidean Distance and Score
    score = []

    for i in range(rows):
        sum_p = 0
        sum_m = 0
        for j in range(cols):
            sum_p += (data[i][j] - best[j])**2
            sum_m += (data[i][j] - worst[j])**2
        
        sp = np.sqrt(sum_p)
        sm = np.sqrt(sum_m)
        
        # Calculate performance score
        if (sp + sm) == 0:
            score.append(0.0)
        else:
            score.append(sm / (sp + sm))

    # Output to CSV
    df['Topsis Score'] = score
    df['Rank'] = df['Topsis Score'].rank(ascending=False)
    
    df.to_csv(result_file, index=False)
    print(f"Result saved to {result_file}")

if __name__ == "__main__":
    main()