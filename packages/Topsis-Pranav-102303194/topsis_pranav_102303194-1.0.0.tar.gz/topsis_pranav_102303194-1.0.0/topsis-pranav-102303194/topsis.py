import sys
import pandas as pd
import numpy as np
import os

def check_numeric(df):
    """Checks if the dataframe (from 2nd column onwards) contains only numeric values."""
    try:
        data_part = df.iloc[:, 1:]
        data_part.astype(float)
        return True
    except Exception:
        return False

def topsis_logic(input_file, weights, impacts, result_file):
    try:
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Error: The file '{input_file}' was not found.")

        df = pd.read_csv(input_file)

        if df.shape[1] < 3:
            raise ValueError("Error: Input file must contain three or more columns.")

        if not check_numeric(df):
            raise ValueError("Error: From 2nd to last columns must contain numeric values only.")

        try:
            weight_list = [float(w) for w in weights.split(',')]
        except ValueError:
             raise ValueError("Error: Weights must be numeric and separated by commas.")
             
        impact_list = impacts.split(',')

        num_cols = df.shape[1] - 1

        if len(weight_list) != num_cols or len(impact_list) != num_cols:
            raise ValueError(f"Error: Number of weights ({len(weight_list)}), impacts ({len(impact_list)}), and columns ({num_cols}) must be the same.")

        if not all(i in ['+', '-'] for i in impact_list):
            raise ValueError("Error: Impacts must be either '+' or '-'.")

        # TOPSIS Calculation
        data = df.iloc[:, 1:].values.astype(float)
        rss = np.sqrt(np.sum(data**2, axis=0))
        normalized_data = data / rss
        weighted_data = normalized_data * weight_list

        ideal_best = []
        ideal_worst = []

        for i in range(num_cols):
            if impact_list[i] == '+':
                ideal_best.append(np.max(weighted_data[:, i]))
                ideal_worst.append(np.min(weighted_data[:, i]))
            else:
                ideal_best.append(np.min(weighted_data[:, i]))
                ideal_worst.append(np.max(weighted_data[:, i]))
        
        ideal_best = np.array(ideal_best)
        ideal_worst = np.array(ideal_worst)

        s_plus = np.sqrt(np.sum((weighted_data - ideal_best)**2, axis=1))
        s_minus = np.sqrt(np.sum((weighted_data - ideal_worst)**2, axis=1))

        total_dist = s_plus + s_minus
        performance_score = np.divide(s_minus, total_dist, out=np.zeros_like(s_minus), where=total_dist!=0)

        df['Topsis Score'] = performance_score
        df['Rank'] = df['Topsis Score'].rank(ascending=False).astype(int)

        df.to_csv(result_file, index=False)
        print(f"Success: TOPSIS results saved to '{result_file}'")

    except Exception as e:
        print(e)

def main():
    if len(sys.argv) != 5:
        print("Error: Wrong number of parameters.")
        print("Usage: topsis <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        print('Example: topsis data.csv "1,1,1,2" "+,+,-,+" result.csv')
    else:
        topsis_logic(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])

if __name__ == "__main__":
    main()