import sys
import pandas as pd
import utils

def main(input_file, X_csv, y_csv, avgs, mode):
    data = pd.read_csv(input_file, low_memory=False)

    if mode == '1v1':
        X, y = utils.preprocess_dataset(data)
    elif mode == 'rank':
        X, y = utils.preprocess_dataset_v2(data)

    print(X.shape)
    print(y.shape)
    X.to_csv(X_csv, index=False)
    y.to_csv(y_csv, index=False)
    if mode == '1v1':
        pd.DataFrame([X.mean(axis=0)]).to_csv(avgs, index=False)

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0], args[1], args[2], args[3], args[4])