"""
TOPSIS Implementation - Command Line Tool
Author: Sanyam Wadhwa
Roll No: 102303059
Class: 3C12

Description: This program implements the TOPSIS (Technique for Order of Preference 
by Similarity to Ideal Solution) method for multi-criteria decision making.
"""

import sys
import pandas as pd
import numpy as np

def validate_inputs(file_path, weights, impacts):
    """
    Validate all input parameters according to assignment requirements
    Created by: Sanyam Wadhwa (102303059)
    """
    
    # Check if file exists - handling FileNotFoundError as per requirements
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found!")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    # Validation: Input file must contain three or more columns
    # Sanyam Wadhwa - 102303059
    if df.shape[1] < 3:
        print("Error: Input file must contain at least 3 columns!")
        sys.exit(1)
    
    # Validation: From 2nd to last columns must contain numeric values only
    # Handling of non-numeric values - Sanyam Wadhwa
    numeric_columns = df.columns[1:]
    for col in numeric_columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            try:
                df[col] = pd.to_numeric(df[col])
            except:
                print(f"Error: Column '{col}' contains non-numeric values!")
                sys.exit(1)
    
    # Parse weights and impacts
    try:
        weight_list = [float(w.strip()) for w in weights.split(',')]
    except:
        print("Error: Weights must be numeric values separated by commas!")
        sys.exit(1)
    
    try:
        impact_list = [i.strip() for i in impacts.split(',')]
    except:
        print("Error: Impacts must be separated by commas!")
        sys.exit(1)
    
    # Validation: Impacts must be either +ve or -ve
    # Sanyam Wadhwa - Roll No: 102303059
    for impact in impact_list:
        if impact not in ['+', '-']:
            print("Error: Impacts must be either '+' or '-'!")
            sys.exit(1)
    
    # Validation: Number of weights, impacts and columns must be same
    # Sanyam Wadhwa (102303059) - 3C12
    num_criteria = df.shape[1] - 1  # Exclude first column
    if len(weight_list) != num_criteria:
        print(f"Error: Number of weights ({len(weight_list)}) must equal number of criteria columns ({num_criteria})!")
        sys.exit(1)
    
    if len(impact_list) != num_criteria:
        print(f"Error: Number of impacts ({len(impact_list)}) must equal number of criteria columns ({num_criteria})!")
        sys.exit(1)
    
    return df, weight_list, impact_list


def topsis(df, weights, impacts):
    """
    Implement TOPSIS algorithm for multi-criteria decision making
    
    Implementation by: Sanyam Wadhwa
    Roll Number: 102303059
    Class: 3C12
    
    TOPSIS Steps:
    1. Normalize the decision matrix
    2. Calculate weighted normalized decision matrix
    3. Find ideal best and ideal worst solutions
    4. Calculate separation measures (Euclidean distance)
    5. Calculate performance score (closeness to ideal)
    6. Rank alternatives based on performance score
    """
    
    # Extract the decision matrix (exclude first column which contains names/IDs)
    # Sanyam Wadhwa - 102303059
    matrix = df.iloc[:, 1:].values
    
    # Step 1: Normalize the decision matrix using vector normalization
    # Formula: x_ij / sqrt(sum(x_ij^2))
    # Implemented by Sanyam Wadhwa (102303059)
    normalized = matrix / np.sqrt((matrix ** 2).sum(axis=0))
    
    # Step 2: Calculate weighted normalized decision matrix
    # Multiply each column by its corresponding weight
    # Sanyam Wadhwa - 102303059
    weights_array = np.array(weights)
    weighted_normalized = normalized * weights_array
    
    # Step 3: Determine ideal best and ideal worst solutions
    # For beneficial criteria (+): ideal best = max, ideal worst = min
    # For non-beneficial criteria (-): ideal best = min, ideal worst = max
    # Sanyam Wadhwa (102303059) - 3C12
    ideal_best = np.zeros(len(weights))
    ideal_worst = np.zeros(len(weights))
    
    for i, impact in enumerate(impacts):
        if impact == '+':
            ideal_best[i] = weighted_normalized[:, i].max()
            ideal_worst[i] = weighted_normalized[:, i].min()
        else:  # impact == '-'
            ideal_best[i] = weighted_normalized[:, i].min()
            ideal_worst[i] = weighted_normalized[:, i].max()
    
    # Step 4: Calculate Euclidean separation measures
    # S+ = Distance from ideal best solution
    # S- = Distance from ideal worst solution
    # Sanyam Wadhwa - Roll No: 102303059
    
    # Calculate Euclidean distance from ideal best
    separation_best = np.sqrt(((weighted_normalized - ideal_best) ** 2).sum(axis=1))
    
    # Calculate Euclidean distance from ideal worst
    separation_worst = np.sqrt(((weighted_normalized - ideal_worst) ** 2).sum(axis=1))
    
    # Step 5: Calculate TOPSIS performance score (closeness coefficient)
    # Formula: Performance Score = S- / (S+ + S-)
    # Range: 0 to 1, where 1 is best
    # Implemented by Sanyam Wadhwa (102303059)
    topsis_score = separation_worst / (separation_best + separation_worst)
    
    # Step 6: Rank alternatives based on performance score
    # Higher TOPSIS score indicates better alternative
    # Rank 1 is the best alternative
    # Sanyam Wadhwa - 102303059 - 3C12
    rank = np.argsort(-topsis_score) + 1  # Descending order, 1-indexed
    final_rank = np.empty_like(rank)
    final_rank[np.argsort(-topsis_score)] = np.arange(1, len(rank) + 1)
    
    return topsis_score, final_rank


def main():
    """
    Main function to execute TOPSIS command line program
    Created by: Sanyam Wadhwa
    Roll No: 102303059
    Group: 3C12
    """
    
    # Validation: Check for correct number of parameters
    # Program requires exactly 4 arguments
    # Sanyam Wadhwa (102303059)
    if len(sys.argv) != 5:
        print("Usage: python topsis.py <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        print("Example: python topsis.py data.csv \"1,1,1,2\" \"+,+,-,+\" output-result.csv")
        sys.exit(1)
    
    # Extract command line arguments
    # Sanyam Wadhwa - 102303059
    input_file = sys.argv[1]
    weights_str = sys.argv[2]
    impacts_str = sys.argv[3]
    output_file = sys.argv[4]
    
    # Validate all inputs according to assignment requirements
    # Sanyam Wadhwa (102303059) - Group 3C12
    df, weights, impacts = validate_inputs(input_file, weights_str, impacts_str)
    
    # Apply TOPSIS algorithm to the validated data
    # Sanyam Wadhwa - Roll No: 102303059
    scores, ranks = topsis(df, weights, impacts)
    
    # Prepare output: Add TOPSIS Score and Rank columns to original dataframe
    # Sanyam Wadhwa (102303059)
    result_df = df.copy()
    result_df['Topsis Score'] = scores
    result_df['Rank'] = ranks.astype(int)
    
    # Save results to output CSV file
    # Sanyam Wadhwa - 102303059 - 3C12
    try:
        result_df.to_csv(output_file, index=False)
        print(f"Success! Results saved to '{output_file}'")
    except Exception as e:
        print(f"Error saving output file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Entry point of the program
    # Sanyam Wadhwa (102303059)
    main()