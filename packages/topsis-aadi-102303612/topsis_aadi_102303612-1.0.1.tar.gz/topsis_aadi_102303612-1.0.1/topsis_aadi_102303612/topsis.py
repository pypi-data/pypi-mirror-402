import pandas as pd
import numpy as np

def topsis():
    print("\n========== TOPSIS Method ==========\n")

    
    csv_path = input("Enter CSV file path: ").strip()
    df = pd.read_csv(csv_path)

    if df.shape[1] < 3:
        raise ValueError("CSV must have at least 1 alternative and 2 criteria")

    alternatives = df.iloc[:, 0]
    decision_matrix = df.iloc[:, 1:].values.astype(float)
    criteria = df.columns[1:]

    print("Criteria detected:", list(criteria))

    weights = input(
        "Enter weights (comma or space separated): "
    ).replace(",", " ").split()

    weights = np.array(list(map(float, weights)))

    if len(weights) != decision_matrix.shape[1]:
        raise ValueError("Number of weights must match number of criteria")

    
    weights = weights / weights.sum()

    impacts = input(
        "Enter impacts (+ or -), comma or space separated: "
    ).replace(",", " ").split()

    if len(impacts) != decision_matrix.shape[1]:
        raise ValueError("Number of impacts must match number of criteria")

   
    norm_matrix = decision_matrix / np.sqrt(
        (decision_matrix ** 2).sum(axis=0)
    )

    weighted_matrix = norm_matrix * weights

    ideal_best = np.zeros(weighted_matrix.shape[1])
    ideal_worst = np.zeros(weighted_matrix.shape[1])

    for j in range(weighted_matrix.shape[1]):
        if impacts[j] == '+':
            ideal_best[j] = weighted_matrix[:, j].max()
            ideal_worst[j] = weighted_matrix[:, j].min()
        elif impacts[j] == '-':
            ideal_best[j] = weighted_matrix[:, j].min()
            ideal_worst[j] = weighted_matrix[:, j].max()
        else:
            raise ValueError("Impacts must be '+' or '-' only")

    dist_best = np.sqrt(((weighted_matrix - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted_matrix - ideal_worst) ** 2).sum(axis=1))

    topsis_score = dist_worst / (dist_best + dist_worst)

    df["TOPSIS Score"] = topsis_score
    df["Rank"] = df["TOPSIS Score"].rank(ascending=False)

   
    df.to_csv("topsis_result.csv", index=False)

    best = df.loc[df["TOPSIS Score"].idxmax()]

    print("\n🏆 BEST ALTERNATIVE:")
    print(best)

    print("\n📁 Results saved to: topsis_result.csv")


if __name__ == "__main__":
    topsis()


