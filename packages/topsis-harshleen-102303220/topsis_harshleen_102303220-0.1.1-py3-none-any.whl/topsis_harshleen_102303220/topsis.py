#IMPLEMENT TOPSIS METHOD FOR MULTI-CRITERIA DECISION MAKING

import sys
import os
import pandas as pd
import numpy as np


def topsis():
    """
    Execute TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution)
    Multi-criteria decision making algorithm.
    
    Reads command line arguments:
    - InputDataFile: CSV file with decision matrix (first column is alternatives)
    - Weights: Comma-separated numeric weights for criteria
    - Impacts: Comma-separated '+' or '-' indicating benefit/cost criteria
    - OutputFile: Output CSV file with TOPSIS scores and ranks
    """
    
    # -------------------- Command Line Arguments --------------------
    if len(sys.argv) != 5:
        print("Usage: python topsis.py <InputDataFile> <Weights> <Impacts> <OutputFile>")
        sys.exit(1)

    input_file = sys.argv[1]
    weights_input = sys.argv[2]
    impacts_input = sys.argv[3]
    output_file = sys.argv[4]

    # -------------------- File Not Found Check --------------------
    if not os.path.isfile(input_file):
        print("Error: Input file not found")
        sys.exit(1)

    # -------------------- Read CSV --------------------
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        print("Error while reading the input file")
        sys.exit(1)

    # -------------------- Column Count Check --------------------
    if df.shape[1] < 3:
        print("Error: Input file must contain three or more columns")
        sys.exit(1)

    # -------------------- Numeric Values Check --------------------
    data = df.iloc[:, 1:]  # from 2nd column to last

    if not np.all(data.applymap(lambda x: isinstance(x, (int, float)))):
        print("Error: From 2nd to last columns must contain numeric values only")
        sys.exit(1)

    # -------------------- Weights & Impacts Parsing --------------------
    try:
        weights = [float(w) for w in weights_input.split(",")]
    except:
        print("Error: Weights must be numeric and separated by commas")
        sys.exit(1)

    impacts = impacts_input.split(",")

    # -------------------- Length Matching Check --------------------
    if len(weights) != data.shape[1] or len(impacts) != data.shape[1]:
        print("Error: Number of weights, impacts, and criteria columns must be the same")
        sys.exit(1)

    # -------------------- Impacts Validation --------------------
    for imp in impacts:
        if imp not in ["+", "-"]:
            print("Error: Impacts must be either '+' or '-'")
            sys.exit(1)

    # -------------------- If all checks pass --------------------
    print("Input validation successful. Proceeding to TOPSIS calculation...")

    # -------------------- TOPSIS Calculation --------------------
    # 1. Normalisation
    # Convert data to numpy array
    matrix = data.values.astype(float)
    norm_denominator = np.sqrt(np.sum(matrix ** 2, axis=0))
    normalized_matrix = matrix / norm_denominator

    # 2. Weight assign
    weights = np.array(weights)
    weighted_normalized_matrix = normalized_matrix * weights

    # 3. Ideal best and ideal worst
    ideal_best = []
    ideal_worst = []

    for j in range(weighted_normalized_matrix.shape[1]):
        column = weighted_normalized_matrix[:, j]
        
        if impacts[j] == "+":
            ideal_best.append(np.max(column))
            ideal_worst.append(np.min(column))
        else:  # impact is "-"
            ideal_best.append(np.min(column))
            ideal_worst.append(np.max(column))

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # 4. Euclidean distance from ideal best and ideal worst
    distance_best = np.sqrt(np.sum((weighted_normalized_matrix - ideal_best) ** 2, axis=1))
    distance_worst = np.sqrt(np.sum((weighted_normalized_matrix - ideal_worst) ** 2, axis=1))

    # -------------------- Step 5: Performance Score --------------------
    performance_score = distance_worst / (distance_best + distance_worst)

    # 6. Add results to dataframe ranking
    # Add TOPSIS Score
    df["Topsis Score"] = performance_score

    # Assign Rank (higher score = better rank)
    df["Rank"] = df["Topsis Score"].rank(method="max", ascending=False).astype(int)

    # Save output file
    df.to_csv(output_file, index=False)

    print("TOPSIS analysis completed successfully.")
    print(f"Result saved to {output_file}")


def main():
    """Main entry point for TOPSIS analysis."""
    try:
        topsis()
    except Exception as e:
        print("Error:", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
