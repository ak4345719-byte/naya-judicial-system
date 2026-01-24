import pickle
import os
from sklearn.linear_model import LinearRegression
import numpy as np


X = np.array([
    [1, 1, 0],
    [2, 1, 1],
    [3, 2, 2],
    [4, 2, 3],
    [5, 3, 4]
])

y = np.array([20, 30, 45, 60, 80])  

model = LinearRegression()
model.fit(X, y)


model_path = os.path.join(os.path.dirname(__file__), "hearing_model.pkl")
with open(model_path, "wb") as f:
    pickle.dump(model, f)

print("✅ AI Hearing Duration Model Trained & Saved")
