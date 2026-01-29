import sys
import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder

def validateInputs():
    # 1. Incorrect number of parameters
    if len(sys.argv) != 5:
        print("Error: Number of parameters are incorrect.")
        print("Correct Order: python <ProgramFile>.py <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        sys.exit(1)
    inputFile = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    outputFile = sys.argv[4]

    # 2. File not Found exception
    if not os.path.exists(inputFile):
        print(f"Error: '{inputFile}' was not found.")
        sys.exit(1)
    try:
        df = pd.read_csv(inputFile)
    except Exception as e:
        print(f"Error: Could not read {e}")
        sys.exit(1)

    # 3. Number of Columns must be >= 3
    if df.shape[1] < 3:
        print("Error: Input file must contain 3 or more columns.")
        sys.exit(1)

    # 4. Weights Format
    try:
        weights = [float(w) for w in weights.split(',')]
    except ValueError:
        print("Error: Incorrect Weight Format.")
        print("Error: Correct Weight Format: '1,2,3' ")
        sys.exit(1)

    # 5. Impacts Format
    impacts = impacts.split(',')
    if not all(i in ['+', '-'] for i in impacts):
        print("Error: Incorrect Impact Format.")
        print("Error: Correct Impact Format: '+,-,+' ")
        sys.exit(1)

    # 6. Non Numeric Values
    for col in df.columns[1:]:
        if not pd.api.types.is_numeric_dtype(df[col]):
            print(f"ALERT: Non-numeric values are present in '{col}'.")

            try:
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col])
                mapp = dict(zip(le.classes_,le.transform(le.classes_)))
                print(f"{col} encoded.")
                print(f"Mapping: {mapp}")

            except Exception as e:
                print(f"Error: '{col} cannot be encoded'.")
                sys.exit(1)
    data = df.iloc[:,1:].values.astype(float)

    # 4. Equal Number of weights, impacts & columns in data
    num = data.shape[1]
    if len(weights) != num:
        print(f"Error: Weights: {len(weights)} != Columns {num}.")
        sys.exit(1)
    if len(impacts) != num:
        print(f"Error: Impacts: {len(impacts)} != Columns {num}.")
        sys.exit(1)

    return df, data, weights, impacts, outputFile



def computeScore(data, weights, impacts):
    # Step 1: Normalization
    result = np.sqrt(np.sum(data**2, axis=0))
    if (result == 0).any():
        print("Error: One of the columns contains only 0's, Normalization cannot be performed.")
        sys.exit(1)   
    normMatrix = (data / result)

    # Step 2: Weighted Normalized Matrix
    weightedMat = normMatrix * weights

    # Step 3: Ideal Best and Ideal Worst
    idealBest = []
    idealWorst = []
    for i in range(len(impacts)):
        if impacts[i] == '+':
            idealBest.append(np.max(weightedMat[:, i]))
            idealWorst.append(np.min(weightedMat[:, i]))
        else:
            idealBest.append(np.min(weightedMat[:, i]))
            idealWorst.append(np.max(weightedMat[:, i]))
    idealBest = np.array(idealBest)
    idealWorst = np.array(idealWorst)

    # Step 4: Euclidean Distance
    best = np.sqrt(np.sum((weightedMat - idealBest)**2, axis=1))
    worst = np.sqrt(np.sum((weightedMat - idealWorst)**2, axis=1))

    # Step 5: Topsis Score
    score = np.divide(worst, (best+worst), out=np.zeros_like(worst), where=(best+worst)!=0)
    score = np.round(score,5)
    return score



def main():
    # Validation and Encoding
    df, data, weights, impacts, outputFile = validateInputs()

    # Calculation
    score = computeScore(data, weights, impacts)

    # Rank
    df['Topsis Score'] = score
    df['Rank'] = df['Topsis Score'].rank(ascending=False).astype(int)

    # Save file
    try:
        df.to_csv(outputFile, index=False)
        print(f"Success! Result saved as '{outputFile}'\n")
    except Exception as e:
        print(f"Error: Output could not be saved.")

    # Display Output
    print(pd.read_csv(outputFile))



if __name__ == "__main__":
    main()