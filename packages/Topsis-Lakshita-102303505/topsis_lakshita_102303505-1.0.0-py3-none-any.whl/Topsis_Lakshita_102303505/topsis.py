import sys
import os
import pandas as pd
import numpy as np


def topsis_analysis(input_file, weights, impacts, output_file):
    """
    Perform TOPSIS analysis on the given dataset.
    
    Parameters:
    -----------
    input_file : str
        Path to input CSV or Excel file
    weights : str
        Comma-separated weights for each criterion (e.g., "1,1,1,2")
    impacts : str
        Comma-separated impacts (+/-) for each criterion (e.g., "+,+,-,+")
    output_file : str
        Path for output CSV file
    
    Returns:
    --------
    pandas.DataFrame
        DataFrame with TOPSIS scores and rankings
    
    Raises:
    -------
    FileNotFoundError
        If input file doesn't exist
    ValueError
        If validation fails for parameters
    """
    
    # File Check
    if not os.path.exists(input_file):
        raise FileNotFoundError("Input file not found.")

    try:
        if input_file.endswith('.xlsx'):
            df = pd.read_excel(input_file)
        else:
            df = pd.read_csv(input_file)
    except Exception as e:
        raise ValueError(f"Unable to read the input file: {e}")

    # Column Check
    if df.shape[1] < 3:
        raise ValueError("Input file must contain at least three columns.")

    # Criteria Data
    data = df.iloc[:, 1:]

    # Numeric Check
    if not data.apply(lambda col: np.issubdtype(col.dtype, np.number)).all():
        raise ValueError("From 2nd to last columns must contain numeric values only.")

    # Weights & Impacts Processing
    try:
        weights_list = list(map(float, weights.split(",")))
        impacts_list = impacts.split(",")
    except Exception:
        raise ValueError("Weights and impacts must be comma-separated.")

    if len(weights_list) != data.shape[1]:
        raise ValueError("Number of weights must match number of criteria.")

    if len(impacts_list) != data.shape[1]:
        raise ValueError("Number of impacts must match number of criteria.")

    for impact in impacts_list:
        if impact not in ['+', '-']:
            raise ValueError("Impacts must be either '+' or '-'.")

    # Decision Matrix Normalization
    norm = np.sqrt((data ** 2).sum())
    normalized_data = data / norm

    # Apply Weights
    weighted_data = normalized_data * weights_list

    # Ideal Best and Worst
    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts_list)):
        if impacts_list[i] == '+':
            ideal_best.append(weighted_data.iloc[:, i].max())
            ideal_worst.append(weighted_data.iloc[:, i].min())
        else:
            ideal_best.append(weighted_data.iloc[:, i].min())
            ideal_worst.append(weighted_data.iloc[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # Distance
    distance_best = np.sqrt(((weighted_data - ideal_best) ** 2).sum(axis=1))
    distance_worst = np.sqrt(((weighted_data - ideal_worst) ** 2).sum(axis=1))

    # TOPSIS Score
    score = distance_worst / (distance_best + distance_worst)

    # Rank
    df['Topsis Score'] = score
    df['Rank'] = score.rank(ascending=False, method='dense').astype(int)

    # Save output
    df.to_csv(output_file, index=False)

    return df


def main():
    """Command-line interface for TOPSIS analysis."""
    
    if len(sys.argv) != 5:
        print("Error: Incorrect number of parameters.")
        print("Usage:")
        print("python -m Topsis_YourName_RollNumber <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        print("\nExample:")
        print('python -m Topsis_YourName_RollNumber data.csv "1,1,1,2" "+,+,-,+" output-result.csv')
        sys.exit(1)

    try:
        result_df = topsis_analysis(
            sys.argv[1],
            sys.argv[2],
            sys.argv[3],
            sys.argv[4]
        )
        
        print("\n" + "="*80)
        print("TOPSIS ANALYSIS COMPLETED SUCCESSFULLY")
        print("="*80)
        print(f"\nInput File: {sys.argv[1]}")
        print(f"Weights: {sys.argv[2]}")
        print(f"Impacts: {sys.argv[3]}")
        print(f"Output File: {sys.argv[4]}")
        print("\n" + "-"*80)
        print("RESULTS:")
        print("-"*80)
        print(result_df.to_string(index=False))
        print("="*80 + "\n")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
