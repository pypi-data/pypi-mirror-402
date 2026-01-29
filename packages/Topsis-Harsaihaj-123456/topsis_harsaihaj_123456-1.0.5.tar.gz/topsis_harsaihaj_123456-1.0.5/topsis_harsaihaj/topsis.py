import sys, pandas as pd, numpy as np

def topsis(input_file, weights, impacts, output_file):
    df = pd.read_csv(input_file)
    data = df.iloc[:,1:].values.astype(float)
    w = np.array(weights)/sum(weights)
    norm = data/np.sqrt((data**2).sum(axis=0))
    weighted = norm*w
    ideal_best = np.max(weighted,axis=0)
    ideal_worst = np.min(weighted,axis=0)
    for i,imp in enumerate(impacts):
        if imp=='-':
            ideal_best[i],ideal_worst[i]=ideal_worst[i],ideal_best[i]
    d_best = np.sqrt(((weighted-ideal_best)**2).sum(axis=1))
    d_worst = np.sqrt(((weighted-ideal_worst)**2).sum(axis=1))
    score = d_worst/(d_best+d_worst)
    df['Topsis Score']=score
    df['Rank']=df['Topsis Score'].rank(ascending=False).astype(int)
    df.to_csv(output_file,index=False)

def main():
    if len(sys.argv)!=5:
        print("Usage: python topsis.py <InputDataFile> <Weights> <Impacts> <OutputFile>")
        sys.exit(1)
    weights=list(map(float,sys.argv[2].split(',')))
    impacts=sys.argv[3].split(',')
    topsis(sys.argv[1],weights,impacts,sys.argv[4])

if __name__=="__main__":
    main()
