import sys
import pandas as pd


def main():
    if len(sys.argv) != 5:
        print("Error: Incorrect number of arguments.")
        print("Usage: python topsis.py <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        sys.exit(1)

    input_file = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    output_file = sys.argv[4]

    # ---------- File Reading ----------
    try:
        data = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print("Error while reading the file:", e)
        sys.exit(1)

    # ---------- Column Count Validation ----------
    if data.shape[1] < 3:
        print("Error: Input file must contain at least three columns.")
        sys.exit(1)

    print("File loaded successfully.")
    print("Number of rows:", data.shape[0])
    print("Number of columns:", data.shape[1])
    
    # ---------- Numeric Value Validation ----------
    numeric_data = data.iloc[:, 1:]

    try:
        numeric_data = numeric_data.apply(pd.to_numeric)
    except ValueError:
        print("Error: From 2nd to last columns must contain numeric values only.")
        sys.exit(1)
        
        # ---------- Weights and Impacts Validation ----------
    num_criteria = data.shape[1] - 1

    try:
        weight_list = [float(w) for w in weights.split(',')]
    except ValueError:
        print("Error: Weights must be numeric and separated by commas.")
        sys.exit(1)

    impact_list = impacts.split(',')

    if len(weight_list) != num_criteria:
        print("Error: Number of weights must be equal to number of criteria.")
        sys.exit(1)

    if len(impact_list) != num_criteria:
        print("Error: Number of impacts must be equal to number of criteria.")
        sys.exit(1)

    for impact in impact_list:
        if impact not in ['+', '-']:
            print("Error: Impacts must be either '+' or '-'.")
            sys.exit(1)
    
    # Decision matrix
    decision_matrix = numeric_data.values

    # Normalize matrix
    norm = (decision_matrix ** 2).sum(axis=0) ** 0.5
    normalized_matrix = decision_matrix / norm

    # Apply weights
    weighted_matrix = normalized_matrix * weight_list

    # Ideal best and ideal worst
    ideal_best = []
    ideal_worst = []

    for j in range(num_criteria):
        if impact_list[j] == '+':
            ideal_best.append(weighted_matrix[:, j].max())
            ideal_worst.append(weighted_matrix[:, j].min())
        else:
            ideal_best.append(weighted_matrix[:, j].min())
            ideal_worst.append(weighted_matrix[:, j].max())

    # Distance calculation
    ideal_best = pd.Series(ideal_best)
    ideal_worst = pd.Series(ideal_worst)

    dist_best = ((weighted_matrix - ideal_best.values) ** 2).sum(axis=1) ** 0.5
    dist_worst = ((weighted_matrix - ideal_worst.values) ** 2).sum(axis=1) ** 0.5

    # TOPSIS score
    topsis_score = dist_worst / (dist_best + dist_worst)

  
    # STEP 7: Ranking and output file
   
    data['Topsis Score'] = topsis_score
    data['Rank'] = data['Topsis Score'].rank(ascending=False, method='dense').astype(int)

    try:
        data.to_csv(output_file, index=False)
        print("TOPSIS analysis completed successfully.")
        print(f"Result saved to '{output_file}'")
    except Exception as e:
        print("Error while saving output file:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
