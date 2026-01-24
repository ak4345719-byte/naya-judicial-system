import pandas as pd
import pickle
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

from feature_engineering import preprocess_data

DATASET_PATH = "../dataset/court_cases.csv"
MODEL_PATH = "../app/hearing_model.pkl"

def train():
    print("📥 Loading dataset...")
    df = pd.read_csv(DATASET_PATH)

    X, y = preprocess_data(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print("🧠 Training Random Forest model...")
    model = RandomForestRegressor(
        n_estimators=100,
        random_state=42
    )
    model.fit(X_train, y_train)

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    print("✅ Model trained & saved as hearing_model.pkl")

if __name__ == "__main__":
    train()
