import sys
import pandas as pd
import os

def main():
    # 1. CHECK PARAMETERS: You need exactly 4 arguments + the script name [cite: 6, 10]
    if len(sys.argv) != 5:
        print("Error: Wrong number of parameters. Usage: python topsis.py <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        return

    input_file = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    output_file = sys.argv[4]

    # 2. FILE HANDLING: Check if file exists [cite: 12]
    if not os.path.isfile(input_file):
        print(f"Error: File '{input_file}' not found.")
        return

    try:
        # Load the data 
        df = pd.read_csv(input_file)

        # 3. COLUMN CHECK: Must have 3+ columns [cite: 13]
        if len(df.columns) < 3:
            print("Error: Input file must contain three or more columns.")
            return

        # 4. NUMERIC CHECK: 2nd column to last must be numeric [cite: 14]
        # We try to convert them to numbers; if it fails, it means there is text there
        for col in df.columns[1:]:
            df[col] = pd.to_numeric(df[col], errors='raise')

        # 5. WEIGHTS & IMPACTS CHECK: Split by comma and check length [cite: 15, 17]
        w_list = [float(w) for w in weights.split(',')]
        i_list = impacts.split(',')

        if len(w_list) != len(i_list) or len(w_list) != (len(df.columns) - 1):
            print("Error: Number of weights, impacts, and numeric columns must be the same.")
            return

        # 6. IMPACTS SIGN CHECK: Must be + or - [cite: 16]
        if not all(i in ['+', '-'] for i in i_list):
            print("Error: Impacts must be either + or -.")
            return

        # --- MATH GOES HERE (TOPSIS Algorithm) ---
        # This is where you implement the "Normalized Matrix" and "Ideal Best/Worst" [cite: 2]
        # --- MATH SECTION ---
        import numpy as np 
        
        # Step 1: Get only the numeric data (Columns P1 to P5)
        # We skip the first column because it contains names like "M1" [cite: 13, 14]
        temp_data = df.iloc[:, 1:].values
        
        # Step 2: Vector Normalization [cite: 2]
        # Square every number, add them up for each column, then take the square root
        rss = np.sqrt(np.sum(temp_data**2, axis=0))
        normalized_data = temp_data / rss
        
        # Step 3: Multiply by Weights [cite: 2, 15]
        weighted_normalized = normalized_data * w_list
        
        # Step 4: Find Ideal Best and Ideal Worst [cite: 2, 16]
        # For '+', the Best is the Max. For '-', the Best is the Min.
        best_ideal = []
        worst_ideal = []
        
        for idx, impact in enumerate(i_list):
            if impact == '+':
                best_ideal.append(np.max(weighted_normalized[:, idx]))
                worst_ideal.append(np.min(weighted_normalized[:, idx]))
            else:
                best_ideal.append(np.min(weighted_normalized[:, idx]))
                worst_ideal.append(np.max(weighted_normalized[:, idx]))
                
        # Step 5: Calculate Distances [cite: 2]
        dist_best = np.sqrt(np.sum((weighted_normalized - best_ideal)**2, axis=1))
        dist_worst = np.sqrt(np.sum((weighted_normalized - worst_ideal)**2, axis=1))
        
        # Step 6: Calculate Performance Score 
        scores = dist_worst / (dist_best + dist_worst)
        
        # Step 7: Add scores and ranks to your table 
        df['Topsis Score'] = scores
        df['Rank'] = df['Topsis Score'].rank(ascending=False).astype(int)
        
        # Step 8: Save the result to the output file name you provided [cite: 6, 10]
        df.to_csv(output_file, index=False)
        print(f"Success! Your result is ready in {output_file}")

    except ValueError:
        print("Error: Non-numeric value found in data columns.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()