import sys
import pandas as pd
import numpy as np

def validate_inputs(df, weights, impacts):
    # validating input file
    if df.shape[1] < 3:
        raise ValueError("Input file must contain at least 3 columns (Alternatives, and at least 2 Criteria)")

    # validating weights and impacts
    if len(weights) != len(impacts):
        raise ValueError("Number of weights and impacts must be same")
    if df.shape[1] - 1 != len(weights):
        raise ValueError("Weights/impacts count must match the number of criteria/feature columns")

    # validating impacts
    if not all(i in ['+', '-'] for i in impacts):
        raise ValueError("Impacts must be either '+' or '-'")

def preprocess_data(df):
    criteria = df.iloc[:, 1:]

    categorical_cols = criteria.select_dtypes(include=['object']).columns
    if len(categorical_cols) > 0:
        raise ValueError(
            f"Categorical data detected in columns {list(categorical_cols)}."
            "Categorical Data is not handled. Please convert them to numeric ranks first."
        )

    criteria = criteria.astype(float)

    # missing value (mean imputation)
    criteria = criteria.fillna(criteria.mean())

    if criteria.isnull().sum().sum() != 0:
        raise ValueError("Null values remain after preprocessing")
    
    return criteria

def topsis_score(data, weights, impacts):
    # step 1: Normalize
    norm = np.sqrt((data**2).sum())
    norm[norm == 0] = 1 #handling division by 0
    normalized = data / norm

    # step 2: Apply weights
    weighted = normalized * weights

    # step 3: Ideal best & worst
    ideal_best = []
    ideal_worst = []

    for i in range(len(weights)):
        if impacts[i] == '+':
            ideal_best.append(weighted.iloc[:, i].max())
            ideal_worst.append(weighted.iloc[:, i].min())
        else:
            ideal_best.append(weighted.iloc[:, i].min())
            ideal_worst.append(weighted.iloc[:, i].max())
    
    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # step 4: Euclidean Distances
    dist_best = np.sqrt(((weighted - ideal_best)**2).sum(axis = 1))
    dist_worst = np.sqrt(((weighted - ideal_worst)**2).sum(axis = 1))
            
    # step 5: Score
    score = dist_worst / (dist_best + dist_worst)

    return score

def main():
    if len(sys.argv) != 5:
        print("Usage: python topsis.py <InputDataFile> <Weights> <Impacts> <ResultFileName>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    weights = np.array(list(map(float, sys.argv[2].split(','))))
    weights = weights / weights.sum() # normalizing weights
    impacts = sys.argv[3].split(',')
    output_file = sys.argv[4]

    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)

    validate_inputs(df, weights, impacts)

    preprocessed_data = preprocess_data(df)
    
    scores = topsis_score(preprocessed_data, weights, impacts)

    df['Topsis Score'] = scores
    df['Rank'] = df['Topsis Score'].rank(ascending=False, method='dense').astype(int)

    df.to_csv(output_file, index=False)
    print("TOPSIS analysis completed successfully.")

if __name__ == "__main__":
    main()