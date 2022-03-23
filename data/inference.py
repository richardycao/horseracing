import pandas as pd
from sklearn.metrics import confusion_matrix
import joblib

rf_model = joblib.load("./rf_model.joblib")

X_test = pd.read_csv('X_test.csv')
y_test = pd.read_csv('y_test.csv')

preds = rf_model.predict(X_test)
print(confusion_matrix(preds, y_test))
