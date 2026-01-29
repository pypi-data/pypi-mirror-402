import sys
import pandas as pd
import numpy as np

def validate_inputs(input_file, weights, impacts, output_file):
    """Validate all input parameters"""
    errors = []
    
    # Check if correct number of parameters
    if len(sys.argv) != 5:
        errors.append("Error: Incorrect number of parameters!")
        errors.append("Usage: python <program.py> <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        return errors
    
    # Check if input file exists
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        errors.append(f"Error: File '{input_file}' not found!")
        return errors
    except Exception as e:
        errors.append(f"Error: Unable to read file '{input_file}'. {str(e)}")
        return errors
    
    # Check if file has at least 3 columns
    if len(df.columns) < 3:
        errors.append("Error: Input file must contain three or more columns!")
        return errors
    
    # Check if columns 2 onwards contain only numeric values
    for col in df.columns[1:]:
        if not pd.api.types.is_numeric_dtype(df[col]):
            errors.append(f"Error: Column '{col}' contains non-numeric values!")
            return errors
    
    # Parse weights
    try:
        weight_list = [float(w.strip()) for w in weights.split(',')]
    except ValueError:
        errors.append("Error: Weights must be numeric values separated by commas!")
        return errors
    
    # Parse impacts
    impact_list = [i.strip() for i in impacts.split(',')]
    
    # Check if number of weights, impacts, and columns match
    num_criteria = len(df.columns) - 1
    if len(weight_list) != num_criteria:
        errors.append(f"Error: Number of weights ({len(weight_list)}) must equal number of criteria columns ({num_criteria})!")
        return errors
    
    if len(impact_list) != num_criteria:
        errors.append(f"Error: Number of impacts ({len(impact_list)}) must equal number of criteria columns ({num_criteria})!")
        return errors
    
    # Check if impacts are either +ve or -ve
    for impact in impact_list:
        if impact not in ['+', '-']:
            errors.append("Error: Impacts must be either '+' or '-'!")
            return errors
    
    return errors

def topsis(input_file, weights, impacts, output_file):
    """Perform TOPSIS analysis"""
    
    # Read the CSV file
    df = pd.read_csv(input_file)
    
    # Parse weights and impacts
    weight_list = np.array([float(w.strip()) for w in weights.split(',')])
    impact_list = [i.strip() for i in impacts.split(',')]
    
    # Extract the decision matrix (all columns except the first one)
    decision_matrix = df.iloc[:, 1:].values
    
    # Step 1: Normalize the decision matrix
    # Using vector normalization: each element divided by square root of sum of squares
    norms = np.sqrt((decision_matrix ** 2).sum(axis=0))
    normalized_matrix = decision_matrix / norms
    
    # Step 2: Calculate weighted normalized decision matrix
    weighted_matrix = normalized_matrix * weight_list
    
    # Step 3: Determine ideal best and ideal worst
    ideal_best = np.zeros(len(weight_list))
    ideal_worst = np.zeros(len(weight_list))
    
    for i, impact in enumerate(impact_list):
        if impact == '+':
            ideal_best[i] = weighted_matrix[:, i].max()
            ideal_worst[i] = weighted_matrix[:, i].min()
        else:  # impact == '-'
            ideal_best[i] = weighted_matrix[:, i].min()
            ideal_worst[i] = weighted_matrix[:, i].max()
    
    # Step 4: Calculate Euclidean distance from ideal best and ideal worst
    distance_best = np.sqrt(((weighted_matrix - ideal_best) ** 2).sum(axis=1))
    distance_worst = np.sqrt(((weighted_matrix - ideal_worst) ** 2).sum(axis=1))
    
    # Step 5: Calculate Topsis score (relative closeness to ideal solution)
    topsis_score = distance_worst / (distance_best + distance_worst)
    
    # Step 6: Rank the alternatives
    rank = np.argsort(-topsis_score) + 1  # Higher score = better rank
    final_rank = np.empty_like(rank)
    final_rank[np.argsort(-topsis_score)] = np.arange(1, len(rank) + 1)
    
    # Add Topsis Score and Rank to the dataframe
    df['Topsis Score'] = topsis_score
    df['Rank'] = final_rank.astype(int)
    
    # Save to output file
    df.to_csv(output_file, index=False)
    
    print(f"TOPSIS analysis completed successfully!")
    print(f"Results saved to '{output_file}'")

def main():
    # Check if correct number of arguments
    if len(sys.argv) != 5:
        print("Error: Incorrect number of parameters!")
        print("Usage: python <program.py> <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        print("Example: python topsis.py data.csv \"1,1,1,2\" \"+,+,-,+\" output-result.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    output_file = sys.argv[4]
    
    # Validate inputs
    errors = validate_inputs(input_file, weights, impacts, output_file)
    
    if errors:
        for error in errors:
            print(error)
        sys.exit(1)
    
    # Perform TOPSIS
    try:
        topsis(input_file, weights, impacts, output_file)
    except Exception as e:
        print(f"Error: An unexpected error occurred - {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
