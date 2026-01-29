import sys 
import numpy as np
import pandas as pd
import math 

def error_exit(message):
    print("Error:", message)
    sys.exit(1)
    
def main():
    if len(sys.argv) != 5:
        print("the input is wrong \n please provide the correct number of arguments")
        print("Usage: python topsis.py <input_data_file> <weights> <impacts> <output_file>")
        sys.exit(1)
        
    input_file = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    output_file = sys.argv[4]
    
    try:
        data = pd.read_csv(input_file)
    except Exception as e:
        error_exit(f"input file not found or Unable to read input file: {e}")
        
    if data.shape[1] < 3:
        error_exit("Input file must contain at least three columns.")
        
    df_2 = data.iloc[:, 1:].copy()
    
    if not np.all(df_2.applymap(np.isreal)):
        error_exit("All  values should be  be numeric")
        
    df_2_matrix  = df_2.values.astype(float)
    
    try :
        weights = list(map(float, weights.split(',')))
    except:
        error_exit("Weights must be  numeric values separated by commas.")
        
    impacts = impacts.split(',')
    if len(weights) != df_2.shape[1]:
        error_exit("weight should be given for eahc columns ( crteria column)")
    if len(impacts) != df_2.shape[1]:
        error_exit("impacts  should be given for eahc columns ( crteria column)")
        
    for impact in impacts:
        if impact not in ['+', '-']:
            error_exit("Impacts must be either '+' or '-'.")
            
            
    # applying topsis method
    
    # Step 1: Normalize the decision matrix
    norm_denominator = np.sqrt((df_2_matrix**2).sum(axis=0))
    normalized_matrix = df_2_matrix / norm_denominator
    
    # Step 2: Multiply by weights
    weights = np.array(weights)
    normalised_weght = weights / weights.sum()
    weighted_normalized_matrix = normalized_matrix * normalised_weght
    
    # Step 3: Determine ideal and negative-ideal solutions
    ideal_best = []
    ideal_worst = []
    
    for j in range(weighted_normalized_matrix.shape[1]):
        if impacts[j] == '+':
            ideal_best.append(np.max(weighted_normalized_matrix[:, j]))
            ideal_worst.append(np.min(weighted_normalized_matrix[:, j]))
        else:
            ideal_best.append(np.min(weighted_normalized_matrix[:, j]))
            ideal_worst.append(np.max(weighted_normalized_matrix[:, j]))
            
    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)
    
    # Step 4: Calculate distances to ideal and negative-ideal solutions
    distance_best = np.sqrt(((weighted_normalized_matrix - ideal_best) ** 2).sum(axis=1))
    distance_worst = np.sqrt(((weighted_normalized_matrix - ideal_worst) ** 2).sum(axis=1))
    
    # Step 5: Calculate performance score
    
    performance_score = distance_worst / (distance_best + distance_worst)
    
    data['Topsis Score'] = performance_score
    data['Rank'] = data['Topsis Score'].rank(ascending=False).astype(int)
    
    data.to_csv(output_file, index=False)
    print("Topsis analysis completed successfulyy \n . Resulted_output  saved to", output_file)
    
if __name__ == "__main__":
    main()