import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib
import sys
import lightgbm as lgbm
from sklearn.model_selection import train_test_split
from sklearn.metrics import log_loss

def main(X_csv, y_csv, model_file):
    X = pd.read_csv(X_csv)
    y = pd.read_csv(y_csv)

    # model = lgbm.LGBMClassifier(n_estimators=10000)
    # model.fit(
    #     X, y,
    #     eval_metric="binary_logloss",
    # )

    model = RandomForestClassifier()
    model.fit(X, y)

    joblib.dump(model, model_file)

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0], args[1], args[2])