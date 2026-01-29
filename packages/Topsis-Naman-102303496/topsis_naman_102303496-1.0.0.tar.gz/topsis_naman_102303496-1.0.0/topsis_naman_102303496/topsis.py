import pandas as pd
import numpy as np

def topsis(input_file, weights, impacts, result_file):
    df = pd.read_csv(input_file)
    
    weights = [float(w) for w in weights.split(',')]
    impacts = impacts.split(',')
    
    data = df.iloc[:, 1:].values.astype(float)
    
    norm = data / np.sqrt((data ** 2).sum(axis=0))
    weighted = norm * weights
    
    ideal_best = np.where([i == '+' for i in impacts], weighted.max(axis=0), weighted.min(axis=0))
    ideal_worst = np.where([i == '+' for i in impacts], weighted.min(axis=0), weighted.max(axis=0))
    
    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))
    
    score = dist_worst / (dist_best + dist_worst)
    df['Topsis Score'] = score
    df['Rank'] = df['Topsis Score'].rank(ascending=False).astype(int)
    
    df.to_csv(result_file, index=False)
