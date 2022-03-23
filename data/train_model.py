import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix
import joblib

X = pd.read_csv('X.csv')
y = pd.read_csv('y.csv')

rf = RandomForestClassifier()
rf.fit(X, y.ravel())
joblib.dump(rf, "./rf_model.joblib")
