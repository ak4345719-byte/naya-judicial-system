import pandas as pd
import os
from sklearn.linear_model import LinearRegression
import pickle


data = {
    "witnesses": [1, 2, 3, 4, 5],
    "advocates": [1, 1, 2, 2, 3],
    "previous_hearings": [0, 1, 2, 3, 4],
    "duration": [20, 30, 45, 60, 80]
}

df = pd.DataFrame(data)

X = df[["witnesses", "advocates", "previous_hearings"]]
y = df["duration"]

model = LinearRegression()
model.fit(X, y)


model_path = os.path.join(os.path.dirname(__file__), "hearing_model.pkl")
with open(model_path, "wb") as f:
    pickle.dump(model, f)

print("✅ Model trained & saved")
