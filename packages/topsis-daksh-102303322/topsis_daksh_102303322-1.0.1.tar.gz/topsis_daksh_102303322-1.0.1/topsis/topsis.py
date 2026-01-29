import sys
import pandas as pd
import numpy as np

def calculate_topsis(data, w, imp):
    matrix = np.array(data, dtype=float)
    
    if len(matrix) == 0:
        raise ValueError("Matrix is empty")

    row_sums = np.sqrt((matrix ** 2).sum(axis=0))
    normalized = matrix / row_sums

    weights = np.array(w, dtype=float)
    weighted_mat = normalized * weights

    best_ideal = []
    worst_ideal = []

    for i in range(len(imp)):
        col = weighted_mat[:, i]
        if imp[i] == '+':
            best_ideal.append(col.max())
            worst_ideal.append(col.min())
        else:
            best_ideal.append(col.min())
            worst_ideal.append(col.max())

    best_dist = np.sqrt(((weighted_mat - np.array(best_ideal)) ** 2).sum(axis=1))
    worst_dist = np.sqrt(((weighted_mat - np.array(worst_ideal)) ** 2).sum(axis=1))

    total_dist = best_dist + worst_dist
    performance = np.divide(worst_dist, total_dist, out=np.zeros_like(worst_dist), where=total_dist!=0)

    return performance

def run():
    if len(sys.argv) != 5:
        print("Usage: topsis <InputDataFile> <Weights> <Impacts> <ResultFileName>")
        print('Example: topsis data.csv "1,1,1,1" "+,+,-,+" result.csv')
        return

    file_path = sys.argv[1]
    weights_str = sys.argv[2]
    impacts_str = sys.argv[3]
    result_file = sys.argv[4]

    try:
        dataset = pd.read_csv(file_path)
        
        if dataset.shape[1] < 3:
            print("Error: Input file must have at least 3 columns.")
            return

        eval_matrix = dataset.iloc[:, 1:].values
        
        w_list = [float(x) for x in weights_str.split(',')]
        i_list = impacts_str.split(',')

        cols_count = eval_matrix.shape[1]
        if len(w_list) != cols_count or len(i_list) != cols_count:
            print("Error: Weights and impacts count must match the number of criteria columns.")
            return
        
        if not all(x in ['+', '-'] for x in i_list):
            print("Error: Impacts must be either '+' or '-'.")
            return

        topsis_scores = calculate_topsis(eval_matrix, w_list, i_list)

        dataset['Topsis Score'] = topsis_scores
        dataset['Rank'] = dataset['Topsis Score'].rank(ascending=False).astype(int)

        dataset.to_csv(result_file, index=False)
        print(f"File saved successfully to {result_file}")

    except FileNotFoundError:
        print("Error: The file was not found.")
    except ValueError as ve:
        print(f"Error: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    run()