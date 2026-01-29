import sys
import pandas as pd
import numpy as np

def validate_inputs(input_file, weights, impacts, output_file):
    """Validate command line arguments"""
    
    # Check if input file exists
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    # Check if file has at least 3 columns
    if len(df.columns) < 3:
        print("Error: Input file must contain at least three columns")
        sys.exit(1)
    
    # Check if numeric columns (2nd to last) contain only numeric values
    numeric_cols = df.iloc[:, 1:]
    for col in numeric_cols.columns:
        if not pd.api.types.is_numeric_dtype(numeric_cols[col]):
            try:
                pd.to_numeric(numeric_cols[col])
            except:
                print(f"Error: Column '{col}' contains non-numeric values")
                sys.exit(1)
    
    # Parse weights and impacts
    try:
        weights_list = [float(w.strip()) for w in weights.split(',')]
    except ValueError:
        print("Error: Weights must be numeric values separated by commas")
        sys.exit(1)
    
    impacts_list = [i.strip() for i in impacts.split(',')]
    
    # Check if impacts are either +ve or -ve
    for impact in impacts_list:
        if impact not in ['+', '-']:
            print("Error: Impacts must be either '+' or '-'")
            sys.exit(1)
    
    # Check if number of weights, impacts and columns match
    num_numeric_cols = len(df.columns) - 1
    if len(weights_list) != num_numeric_cols:
        print(f"Error: Number of weights ({len(weights_list)}) must equal number of criteria ({num_numeric_cols})")
        sys.exit(1)
    
    if len(impacts_list) != num_numeric_cols:
        print(f"Error: Number of impacts ({len(impacts_list)}) must equal number of criteria ({num_numeric_cols})")
        sys.exit(1)
    
    return df, weights_list, impacts_list

def normalize_matrix(df):
    """Normalize the decision matrix"""
    numeric_data = df.iloc[:, 1:].values
    
    # Calculate the root of sum of squares for each column
    root_sum_squares = np.sqrt(np.sum(numeric_data**2, axis=0))
    
    # Normalize
    normalized = numeric_data / root_sum_squares
    
    return normalized

def calculate_weighted_matrix(normalized, weights):
    """Calculate weighted normalized decision matrix"""
    return normalized * weights

def find_ideal_solutions(weighted, impacts):
    """Find ideal best and ideal worst solutions"""
    ideal_best = []
    ideal_worst = []
    
    for i, impact in enumerate(impacts):
        if impact == '+':
            ideal_best.append(np.max(weighted[:, i]))
            ideal_worst.append(np.min(weighted[:, i]))
        else:
            ideal_best.append(np.min(weighted[:, i]))
            ideal_worst.append(np.max(weighted[:, i]))
    
    return np.array(ideal_best), np.array(ideal_worst)

def calculate_distances(weighted, ideal_best, ideal_worst):
    """Calculate Euclidean distances from ideal best and worst"""
    distance_best = np.sqrt(np.sum((weighted - ideal_best)**2, axis=1))
    distance_worst = np.sqrt(np.sum((weighted - ideal_worst)**2, axis=1))
    
    return distance_best, distance_worst

def calculate_topsis_score(distance_best, distance_worst):
    """Calculate TOPSIS score"""
    return distance_worst / (distance_best + distance_worst)

def calculate_rank(scores):
    """Calculate rank based on TOPSIS scores"""
    return pd.Series(scores).rank(ascending=False, method='min').astype(int)

def topsis(input_file, weights, impacts, output_file):
    """Main TOPSIS function"""
    
    # Validate inputs
    df, weights_list, impacts_list = validate_inputs(input_file, weights, impacts, output_file)
    
    # Step 1: Normalize the decision matrix
    normalized = normalize_matrix(df)
    
    # Step 2: Calculate weighted normalized decision matrix
    weighted = calculate_weighted_matrix(normalized, weights_list)
    
    # Step 3: Find ideal best and ideal worst solutions
    ideal_best, ideal_worst = find_ideal_solutions(weighted, impacts_list)
    
    # Step 4: Calculate distances from ideal solutions
    distance_best, distance_worst = calculate_distances(weighted, ideal_best, ideal_worst)
    
    # Step 5: Calculate TOPSIS score
    topsis_scores = calculate_topsis_score(distance_best, distance_worst)
    
    # Step 6: Calculate rank
    ranks = calculate_rank(topsis_scores)
    
    # Create output dataframe
    result_df = df.copy()
    result_df['Topsis Score'] = topsis_scores.round(2)
    result_df['Rank'] = ranks
    
    # Save to output file
    result_df.to_csv(output_file, index=False)
    print(f"Results saved to '{output_file}'")

def main():
    """Command line entry point"""
    if len(sys.argv) != 5:
        print("Error: Incorrect number of parameters")
        print("Usage: topsis <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        print('Example: topsis data.csv "1,1,1,2" "+,+,-,+" output-result.csv')
        sys.exit(1)
    
    input_file = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    output_file = sys.argv[4]
    
    topsis(input_file, weights, impacts, output_file)

if __name__ == "__main__":
    main()