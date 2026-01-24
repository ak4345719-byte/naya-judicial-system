import pandas as pd

def preprocess_data(df: pd.DataFrame):
    """
    Converts raw court case data into ML-ready format
    """

    
    case_type_map = {
        "Civil": 0,
        "Criminal": 1,
        "Family": 2,
        "Commercial": 3
    }
    df["case_type"] = df["case_type"].map(case_type_map)

    
    complexity_map = {
        "Low": 0,
        "Medium": 1,
        "High": 2
    }
    df["case_complexity"] = df["case_complexity"].map(complexity_map)

    
    X = df[
        [
            "case_type",
            "number_of_witnesses",
            "advocate_count",
            "previous_hearings",
            "case_complexity"
        ]
    ]

    y = df["hearing_duration_minutes"]

    return X, y
