import sys
import pandas as pd
import numpy as np
from pathlib import Path


def topsis(input_file, weights, impacts, output_file):
    """
    TOPSIS Implementation
    """
    
    # Validate file exists
    if not Path(input_file).exists():
        print(f"Error: File '{input_file}' not found!")
        sys.exit(1)
    
    # Read file (supports both CSV and Excel)
    try:
        if input_file.endswith('.csv'):
            df = pd.read_csv(input_file)
        elif input_file.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(input_file)
        else:
            print("Error: File must be CSV or Excel format")
            sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    # Check minimum columns
    if df.shape[1] < 3:
        print("Error: File must have at least 3 columns")
        sys.exit(1)
    
    # Parse weights and impacts
    try:
        weight_list = [float(w.strip()) for w in weights.split(',')]
    except:
        print("Error: Weights must be comma-separated numbers")
        sys.exit(1)
    
    try:
        impact_list = [i.strip() for i in impacts.split(',')]
    except:
        print("Error: Impacts must be comma-separated")
        sys.exit(1)
    
    # Validate impacts
    for impact in impact_list:
        if impact not in ['+', '-']:
            print(f"Error: Impacts must be '+' or '-', found '{impact}'")
            sys.exit(1)
    
    # Check counts match
    num_criteria = df.shape[1] - 1
    if len(weight_list) != num_criteria:
        print(f"Error: Number of weights ({len(weight_list)}) must equal criteria ({num_criteria})")
        sys.exit(1)
    
    if len(impact_list) != num_criteria:
        print(f"Error: Number of impacts ({len(impact_list)}) must equal criteria ({num_criteria})")
        sys.exit(1)
    
    # Check numeric columns
    for col in df.columns[1:]:
        if not pd.api.types.is_numeric_dtype(df[col]):
            print(f"Error: Column '{col}' must be numeric")
            sys.exit(1)
    
    # STEP 1: Normalize
    normalized_df = df.copy()
    for col in df.columns[1:]:
        sum_of_squares = np.sqrt((df[col] ** 2).sum())
        if sum_of_squares != 0:
            normalized_df[col] = df[col] / sum_of_squares
        else:
            normalized_df[col] = 0
    
    # STEP 2: Apply weights
    weighted_df = normalized_df.copy()
    for idx, col in enumerate(normalized_df.columns[1:]):
        weighted_df[col] = normalized_df[col] * weight_list[idx]
    
    # STEP 3: Find ideal best and worst
    ideal_best = []
    ideal_worst = []
    for idx, col in enumerate(weighted_df.columns[1:]):
        if impact_list[idx] == '+':
            ideal_best.append(weighted_df[col].max())
            ideal_worst.append(weighted_df[col].min())
        else:
            ideal_best.append(weighted_df[col].min())
            ideal_worst.append(weighted_df[col].max())
    
    # STEP 4: Calculate distances
    distance_best = []
    distance_worst = []
    
    for idx in range(len(weighted_df)):
        dist_best = 0
        dist_worst = 0
        
        for col_idx, col in enumerate(weighted_df.columns[1:]):
            dist_best += (weighted_df.iloc[idx][col] - ideal_best[col_idx]) ** 2
            dist_worst += (weighted_df.iloc[idx][col] - ideal_worst[col_idx]) ** 2
        
        distance_best.append(np.sqrt(dist_best))
        distance_worst.append(np.sqrt(dist_worst))
    
    # STEP 5: Calculate TOPSIS Score
    topsis_scores = []
    for i in range(len(distance_best)):
        denominator = distance_best[i] + distance_worst[i]
        if denominator == 0:
            topsis_scores.append(0)
        else:
            topsis_scores.append(distance_worst[i] / denominator)
    
    # STEP 6: Rank
    result_df = df.copy()
    result_df['Topsis Score'] = topsis_scores
    result_df['Rank'] = result_df['Topsis Score'].rank(ascending=False).astype(int)
    
    # Save result
    result_df.to_csv(output_file, index=False)
    
    print(f"✓ TOPSIS completed successfully!")
    print(f"✓ Results saved to: {output_file}")
    print(f"\nAll Rankings:")
    print(result_df.sort_values('Rank')[[df.columns[0], 'Topsis Score', 'Rank']].to_string(index=False))


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Error: Wrong number of arguments!")
        print("\nUsage:")
        print('  python topsis.py <InputFile> <Weights> <Impacts> <OutputFile>')
        print("\nExample:")
        print('  python topsis.py data.xlsx "1,1,1,2" "+,+,-,+" result.csv')
        sys.exit(1)
    
    input_file = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    output_file = sys.argv[4]
    
    topsis(input_file, weights, impacts, output_file)