import sys
import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder

def validate_and_process_inputs():
    # Check for correct number of parameters
    if len(sys.argv) != 5:
        print("Error: Wrong number of parameters.")
        print("Format: python topsis.py <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        print("Example: python topsis.py data.csv '1,1,1,2' '+,+,-,+' result.csv")
        sys.exit(1)

    input_file = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    output_file = sys.argv[4]

    # “File not Found” exception
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)

    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        print(f"Error: Could not read file. {e}")
        sys.exit(1)

    # Handling the input file must contain three or more columns.
    if df.shape[1] < 3:
        print("Error: Input file must contain three or more columns.")
        sys.exit(1)

    # Handling Impacts and weights must be separated by ‘,’ (comma) and valid.
    try:
        final_weights = [float(w) for w in weights.split(',')]
    except ValueError:
        print("Error: Weights should be comma-separated numeric values (e.g., '1,2,3').")
        sys.exit(1)

    final_impacts = impacts.split(',')
    
    if not all(i in ['+', '-'] for i in final_impacts):
        print("Error: Impacts should be either '+' or '-' separated by commas (e.g., '+,-,+').")
        sys.exit(1)

    # Converting non numeric values to numeric - Encoding
    # Iterate from the 2nd column (index 1) to the last
    for col in df.columns[1:]:
        if not pd.api.types.is_numeric_dtype(df[col]):
            print(f"Column '{col}' has non numeric values.")
            
            try:
                le = LabelEncoder()
                # Fit and transform the column
                df[col] = le.fit_transform(df[col])
                
                # Mapping : create pairs of (OriginalLabel, EncodedNumber)
                mapping = dict(zip(le.classes_, le.transform(le.classes_)))
                print(f"Mapping: {mapping}")
                
            except Exception as e:
                print(f"Error: Could not encode '{col}' column. {e}")
                sys.exit(1)

    # Final matrix after encoding
    data_matrix = df.iloc[:, 1:].values.astype(float)

    # The number of weights, number of impacts and number of columns (from 2nd to last columns) must be the same.
    columns = data_matrix.shape[1]
    
    if len(final_weights) != columns:
        print(f"Error: Number of weights ({len(final_weights)}) is not equal to number of columns ({columns}).")
        sys.exit(1) 

    if len(final_impacts) != columns:
        print(f"Error: Number of impacts ({len(final_impacts)}) is not to equal to number of columns ({columns}).")
        sys.exit(1)

    return df, data_matrix, final_weights, final_impacts, output_file


def calculate_topsis(data_matrix, weights, impacts):
    """
    Performs the TOPSIS calculation on the numeric data matrix.
    """
    # Step 1: Vector Normalization
    rss = np.sqrt(np.sum(data_matrix**2, axis=0))
    
    if (rss == 0).any():
        print("Error: One of the columns contains all zeros, cannot normalize.")
        sys.exit(1)
        
    normalized_matrix = data_matrix / rss

    # Step 2: Weight Assignment (Normalized Matrix)
    weighted_matrix = normalized_matrix * weights

    # Step 3: Find Ideal Best and Ideal Worst
    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(np.max(weighted_matrix[:, i]))
            ideal_worst.append(np.min(weighted_matrix[:, i]))
        else: # Impact is '-'
            ideal_best.append(np.min(weighted_matrix[:, i]))
            ideal_worst.append(np.max(weighted_matrix[:, i]))

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # Step 4: Calculate Euclidean Distance
    s_best = np.sqrt(np.sum((weighted_matrix - ideal_best)**2, axis=1))
    s_worst = np.sqrt(np.sum((weighted_matrix - ideal_worst)**2, axis=1))

    # Step 5: Topsis Score
    denom = s_best + s_worst
    topsis_score = np.divide(s_worst, denom, out=np.zeros_like(s_worst), where=denom!=0)
    topsis_score = np.round(topsis_score, 5)
    
    return topsis_score

def main():
    # Validation and Encoding
    df, data_matrix, weights, impacts, output_file = validate_and_process_inputs()

    # Calculation
    topsis_score = calculate_topsis(data_matrix, weights, impacts)

    # Step 6: Assign rank according to TOPSIS score
    # higher score- higher rank
    df['Topsis Score'] = topsis_score
    df['Rank'] = df['Topsis Score'].rank(ascending=False).astype(int)

    # Save to output file
    try:
        df.to_csv(output_file, index=False)
        print(f"Success! Result saved in file : '{output_file}'")
    except Exception as e:
        print(f"Error in saving output to file. {e}")
    
    print(df)

if __name__ == "__main__":
    main()