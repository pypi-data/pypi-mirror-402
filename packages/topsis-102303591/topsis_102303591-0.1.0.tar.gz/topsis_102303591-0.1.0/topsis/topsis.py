import numpy as np
import pandas as pd
import re
import sys

class topsis:
 
    """
    TOPSIS : Technique for Order of Preference by Similarity to Ideal Solution
    Steps to be followed :
    1. Construct the decision matrix from the given data.
    2. Normalize the decision matrix.
    3. Construct the weighted normalized decision matrix.
    4. Determine the ideal and negative-ideal solutions.
    5. Calculate the separation measures for each alternative.
    6. Calculate the relative closeness to the ideal solution.
    7. Rank the alternatives based on the relative closeness.
    8. Display the results.
    """
    def __init__(self, file, weights, impacts):
       
        # check for proper csv file
        assert "csv" in f"{file}", "Could not recognize csv file, try checking your input file"
        self.df = pd.read_csv(file).iloc[:, 1:]
        self.df_copy_id = pd.read_csv(file).iloc[:, 0]

        # Data Preprocessing
        
        # Using regular expressions to extract only numeric values along with floating values
        for i in self.df:
            self.df[i] = [re.findall("[0-9]*\.[0-9]+|[0-9]+", str(x))[0] for x in self.df[i]]
        self.matrix = np.array(self.df, dtype = np.float64)

        # Check for correct format of matrix
        assert len(self.matrix.shape) == 2, "Decision matrix a must be 2D"

        self.rows = len(self.matrix)
        self.columns = len(self.matrix[0])
        self.n_matrix = np.array([[0]*self.columns for _ in range(self.rows)], dtype = np.float64)
        self.w_matrix = np.array([[0]*self.columns for _ in range(self.rows)], dtype = np.float64)
        self.weights = np.array(weights, dtype = np.float64)

        # Check for correct format of weights
        assert len(self.weights.shape) == 1, "Weights array must be 1D"
        assert self.weights.size == self.columns, f"Weights array should be of length {self.columns}"

        self.impacts = np.array(impacts)
        # Check for correct format of impacts
        assert len(self.impacts.shape) == 1, "Impact array must be 1D"
        assert self.impacts.size == self.columns, f"Impacts array should be of length {self.columns}"

        self.best = np.array([0]*self.columns, dtype = np.float64)
        self.worst = np.array([0]*self.columns, dtype = np.float64)
        self.s_best = np.array([0]*self.rows, dtype = np.float64)
        self.s_worst = np.array([0]*self.rows, dtype = np.float64)
        self.p_scores = np.array([0]*self.rows, dtype = np.float64)

    def normalized_matrix(self):
        for i in range(self.columns):
            temp = np.sum(self.matrix[:, i]**2)**0.5
            self.n_matrix[:, i] = self.matrix[:, i] / temp

    def weighted_matrix(self):
        for i in range(self.columns):
            self.w_matrix[:, i] = self.n_matrix[:, i] * self.weights[i]

    def ideal_calculate(self):
        for i in range(self.columns):
            if self.impacts[i] == '+':
                self.best[i] = np.max(self.w_matrix[:, i])
                self.worst[i] = np.min(self.w_matrix[:, i])
            else:
                self.best[i] = np.min(self.w_matrix[:, i])
                self.worst[i] = np.max(self.w_matrix[:, i])

    # Step for calculating p_scores 
    
    def rank_calculate(self):
        for i in range(self.rows):
            self.s_best[i] = np.sum((self.w_matrix[i, :] - self.best)**2)**0.5
            self.s_worst[i] = np.sum((self.w_matrix[i, :] - self.worst)**2)**0.5
        self.p_scores = self.s_worst/(self.s_best + self.s_worst)

        final_scores_sorted = np.argsort(self.p_scores) # gives indices of sorted array
        max_index = len(final_scores_sorted)

        rank = []
        for i in range(len(final_scores_sorted)):
            rank.append(max_index - np.where(final_scores_sorted==i)[0][0])
            
        print(pd.DataFrame({"Models/id" : self.df_copy_id, "Ranks": np.array(rank)}))
        print(f"Result : Model/Alternative {np.argsort(self.p_scores)[-1] + 1} is best")

    def display(self):
        print('Original Matrix :')
        print(self.matrix)
        print('Nomralized Matrix : ')
        print(self.n_matrix)
        print('Weighted Matrix : ')
        print(self.w_matrix)
        print('Best values : ')
        print(self.best)
        print('Worst Values : ')
        print(self.worst)
        print('S_best Values : ')
        print(self.s_best)
        print('S_worst Values : ')
        print(self.s_worst)
        print('Performace Scores : ')
        print(self.p_scores)

    # main topsis functions 
    def topsis_main(self, debug = False):
        self.normalized_matrix()
        self.weighted_matrix()
        self.ideal_calculate()
        print()
        self.rank_calculate()
        if debug:
            print()
            self.display()

# main driver function
if __name__ == '__main__':
    print('TOPSIS RANKING ALGORITHM')
    print('Arguments to be entered in this order : python -m topsis.topsis <InputDataFile> <Weights> <Impacts> <Verbose(optional)>')
    if len(sys.argv) >= 4:
        file = sys.argv[1]
        weights = list(map(float, sys.argv[2].strip().split(',')))
        impacts = list(sys.argv[3].strip().split(','))
        print(f"Given csv file : {file} ")
        print(f"Given weights : {weights}")
        print(f"Given impacts : {impacts}")
        t = topsis(file, weights, impacts)
        if len(sys.argv) == 5:
            print()
            t.topsis_main(debug = True)
        else:
            t.topsis_main()
    else:
        print("Put Arguments in Correct order : python -m topsis.topsis <InputDataFile> <Weights> <Impacts> <Verbose>(optional)>")

