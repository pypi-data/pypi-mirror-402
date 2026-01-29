import sys
import pandas as pd
import numpy as np
import os

def check_inputs(input_file, weights, impacts):
    # 2. File existence
    if not os.path.exists(input_file):
        raise FileNotFoundError("Input file not found")

    # 3. Read file (csv or xlsx)
    try:
        if input_file.endswith(".csv"):
            data = pd.read_csv(input_file)
        elif input_file.endswith(".xlsx"):
            data = pd.read_excel(input_file)
        else:
             raise ValueError("Only .csv or .xlsx files allowed")
    except Exception as e:
        raise ValueError(f"Cannot read input file: {e}")

    # 4. Column check
    if data.shape[1] < 3:
        raise ValueError("Input file must have at least 3 columns")

    # 5. Numeric check
    criteria = data.iloc[:, 1:]
    try:
        criteria = criteria.astype(float)
    except:
        raise ValueError("From 2nd to last columns must be numeric")

    # 6. Weights and impacts
    if "," not in weights or "," not in impacts:
        raise ValueError("Weights and impacts must be comma-separated")

    weight_list = weights.split(",")
    impact_list = impacts.split(",")

    if len(weight_list) != criteria.shape[1] or len(impact_list) != criteria.shape[1]:
        raise ValueError("Number of weights and impacts must match number of criteria columns")

    try:
        weight_list = np.array(weight_list, dtype=float)
    except:
        raise ValueError("Weights must be numeric")

    for i in impact_list:
        if i not in ["+", "-"]:
            raise ValueError("Impacts must be '+' or '-'")
            
    return data, criteria, weight_list, impact_list

def topsis(input_file, weights, impacts, output_file=None):
    """
    Topsis implementation.
    Returns the dataframe with Topsis Score and Rank.
    """
    data, criteria, weight_arr, impact_list = check_inputs(input_file, weights, impacts)
    
    # 7. TOPSIS Calculation
    matrix = criteria.values
    
    # Avoid division by zero
    norm = np.sqrt((matrix**2).sum(axis=0))
    # Handle cases where norm is 0 to avoid nan
    norm = np.where(norm == 0, 1, norm) 
    
    normalized = matrix / norm

    weighted = normalized * weight_arr

    ideal_best = []
    ideal_worst = []

    for i in range(len(impact_list)):
        if impact_list[i] == "+":
            ideal_best.append(max(weighted[:, i]))
            ideal_worst.append(min(weighted[:, i]))
        else:
            ideal_best.append(min(weighted[:, i]))
            ideal_worst.append(max(weighted[:, i]))

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    d_plus = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    d_minus = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    # Handle division by zero if d_plus + d_minus is 0
    denominator = d_plus + d_minus
    score = np.divide(d_minus, denominator, out=np.zeros_like(d_minus), where=denominator!=0)

    data["Topsis Score"] = score
    data["Rank"] = data["Topsis Score"].rank(ascending=False)
    
    if output_file:
        if output_file.endswith(".xlsx"):
            data.to_excel(output_file, index=False)
        else:
            data.to_csv(output_file, index=False)
        print(f"Success! Result saved to {output_file}")
         
    return data

if __name__ == "__main__":
    # 1. Check arguments
    if len(sys.argv) != 5:
        print("Usage: python topsis.py <InputFile> <Weights> <Impacts> <OutputFile>")
        sys.exit(1)
    
    in_file = sys.argv[1]
    w = sys.argv[2]
    im = sys.argv[3]
    out_file = sys.argv[4]
    
    try:
        topsis(in_file, w, im, out_file)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
