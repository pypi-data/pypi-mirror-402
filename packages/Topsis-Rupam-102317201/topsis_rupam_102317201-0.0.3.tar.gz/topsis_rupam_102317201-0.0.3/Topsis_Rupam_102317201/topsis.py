import numpy as np
import pandas as pd
import sys
import os

def main():
    if len(sys.argv) !=5:
        print("Wrong no. of Parameters")
        return
  
    input = sys.argv[1]
    weight_inp = sys.argv[2]
    impact_inp = sys.argv[3]
    output_file = sys.argv[4]
  

    if not os.path.exists(input):
        print("File not found")

    try:
        df = pd.read_csv(input)
    except:
        print("Error")
        return

    if df.shape[1] < 3:
        print("Atleast 3 features!")
        return
    try:
        data = df.iloc[:, 1:].values.astype(float)
    except ValueError:
            print("Only numeric values")
            return

    try:
        weight = [float(w) for w in weight_inp.split(',')] #.split() so seperate value, no single string
        impact = impact_inp.split(',') #<---
    except ValueError:
        print("Seperate the weight by commas")
        return

    num_col = data.shape[1] #<---
    if len(weight) != num_col or len(impact)!= num_col:
        print("Both weight and impact must be of same lenght")
        return

    for i in impact:
        if i not in ['+', '-']:
            print("Wrong Impact")
            return

     #topsis algo  
    col_sum = np.sqrt((data**2).sum(axis=0))
    col_sum[col_sum==0] = 1
    normalized = data / col_sum
    weighted_normalized = normalized * weight
    ideal_best_Vpos = []
    ideal_worst_Vneg = []

    for i in range(num_col):
        if impact[i] == '+':
            ideal_best_Vpos.append(weighted_normalized[:,i].max())
            ideal_worst_Vneg.append(weighted_normalized[:,i].min())
        else:
            ideal_best_Vpos.append(weighted_normalized[:,i].min())
            ideal_worst_Vneg.append(weighted_normalized[:,i].max())
    
    ideal_best_Vpos = np.array(ideal_best_Vpos)
    ideal_worst_Vneg = np.array(ideal_worst_Vneg)

    S_plus = np.sqrt(((weighted_normalized - ideal_best_Vpos)**2).sum(axis=1))
    S_minus = np.sqrt(((weighted_normalized - ideal_worst_Vneg)**2).sum(axis=1))
    S_Total = S_plus + S_minus #<---

    Performance_index = [] #<---
    for i in range(len(S_Total)):
        if S_Total[i] == 0:
            Performance_index.append(0.0)
        else:
            Performance_index.append(S_minus[i] / S_Total[i])

    df['Topsis Score'] = Performance_index
    df['Rank'] = df['Topsis Score'].rank(ascending=False).astype(int)
    
    df.to_csv(output_file, index=False)
    print("Success")

if __name__ == "__main__":
    main()

