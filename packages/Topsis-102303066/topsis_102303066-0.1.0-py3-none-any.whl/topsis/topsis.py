import numpy as np
import pandas as pd
import re
import sys


class TopsisMethod:
    """
    TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)

    Workflow:
    1. Read decision matrix
    2. Normalize values
    3. Apply weights
    4. Identify ideal best & worst
    5. Compute separation distances
    6. Calculate performance score
    7. Rank alternatives
    """

    def __init__(self, filename, wts, signs):

        # CSV validation
        if "csv" not in filename:
            raise AssertionError("Input file must be a CSV")

        raw_data = pd.read_csv(filename)
        self.identifiers = raw_data.iloc[:, 0]
        self.data = raw_data.iloc[:, 1:]

        # Extract numeric values using regex
        for col in self.data.columns:
            self.data[col] = [
                re.findall(r"[0-9]*\.[0-9]+|[0-9]+", str(val))[0]
                for val in self.data[col]
            ]

        self.decision_matrix = np.array(self.data, dtype=float)

        if len(self.decision_matrix.shape) != 2:
            raise AssertionError("Decision matrix must be 2-dimensional")

        self.m, self.n = self.decision_matrix.shape

        self.norm_matrix = np.zeros((self.m, self.n))
        self.weighted_matrix = np.zeros((self.m, self.n))

        self.weights = np.array(wts, dtype=float)
        self.impacts = np.array(signs)

        if self.weights.ndim != 1 or self.weights.size != self.n:
            raise AssertionError("Weights must be 1D and match number of criteria")

        if self.impacts.ndim != 1 or self.impacts.size != self.n:
            raise AssertionError("Impacts must be 1D and match number of criteria")

        self.ideal_best = np.zeros(self.n)
        self.ideal_worst = np.zeros(self.n)

        self.dist_best = np.zeros(self.m)
        self.dist_worst = np.zeros(self.m)
        self.scores = np.zeros(self.m)

    def normalize(self):
        for j in range(self.n):
            denom = np.sqrt(np.sum(self.decision_matrix[:, j] ** 2))
            self.norm_matrix[:, j] = self.decision_matrix[:, j] / denom

    def apply_weights(self):
        for j in range(self.n):
            self.weighted_matrix[:, j] = self.norm_matrix[:, j] * self.weights[j]

    def calculate_ideal_solutions(self):
        for j in range(self.n):
            if self.impacts[j] == '+':
                self.ideal_best[j] = np.max(self.weighted_matrix[:, j])
                self.ideal_worst[j] = np.min(self.weighted_matrix[:, j])
            else:
                self.ideal_best[j] = np.min(self.weighted_matrix[:, j])
                self.ideal_worst[j] = np.max(self.weighted_matrix[:, j])

    def compute_scores(self):
        for i in range(self.m):
            self.dist_best[i] = np.sqrt(
                np.sum((self.weighted_matrix[i] - self.ideal_best) ** 2)
            )
            self.dist_worst[i] = np.sqrt(
                np.sum((self.weighted_matrix[i] - self.ideal_worst) ** 2)
            )

        self.scores = self.dist_worst / (self.dist_best + self.dist_worst)

        order = np.argsort(self.scores)
        total = len(order)

        ranks = []
        for idx in range(len(order)):
            ranks.append(total - np.where(order == idx)[0][0])

        result = pd.DataFrame({
            "Models/id": self.identifiers,
            "Ranks": np.array(ranks)
        })

        print(result)
        print(f"Result : Model/Alternative {np.argmax(self.scores) + 1} is best")

    def show_debug(self):
        print("\nOriginal Matrix:\n", self.decision_matrix)
        print("\nNormalized Matrix:\n", self.norm_matrix)
        print("\nWeighted Matrix:\n", self.weighted_matrix)
        print("\nIdeal Best:\n", self.ideal_best)
        print("\nIdeal Worst:\n", self.ideal_worst)
        print("\nDistance from Best:\n", self.dist_best)
        print("\nDistance from Worst:\n", self.dist_worst)
        print("\nPerformance Scores:\n", self.scores)

    def run(self, verbose=False):
        self.normalize()
        self.apply_weights()
        self.calculate_ideal_solutions()
        self.compute_scores()

        if verbose:
            self.show_debug()


# Driver code
if __name__ == "__main__":

    print("TOPSIS RANKING ALGORITHM")
    print("Usage:")
    print("python -m topsis.topsis <InputFile.csv> <Weights> <Impacts> <Verbose(optional)>")

    if len(sys.argv) >= 4:
        input_file = sys.argv[1]
        weight_list = list(map(float, sys.argv[2].split(',')))
        impact_list = sys.argv[3].split(',')

        print(f"Input file : {input_file}")
        print(f"Weights    : {weight_list}")
        print(f"Impacts    : {impact_list}")

        model = TopsisMethod(input_file, weight_list, impact_list)

        if len(sys.argv) == 5:
            model.run(verbose=True)
        else:
            model.run()
    else:
        print("Error: Incorrect number of arguments.")
