import sys
import pandas as pd
import utils

def main(input_file, X_csv, y_csv):
    data = pd.read_csv(input_file)

    X, y = utils.preprocess_dataset(data)

    print(X.shape)
    print(y.shape)
    X.to_csv(X_csv, index=False)
    y.to_csv(y_csv, index=False)

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0], args[1], args[2])