import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib
import sys

def main(X_csv, y_csv, model_file):
    X = pd.read_csv(X_csv)
    y = pd.read_csv(y_csv)

    rf = RandomForestClassifier()
    rf.fit(X, y)
    joblib.dump(rf, model_file)

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0], args[1], args[2])