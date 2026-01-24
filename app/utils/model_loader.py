import os
try:
    import pickle
except ImportError:
    pickle = None

from ..config import MODEL_PATH

_model = None

class MockModel:
    def predict(self, features):
        
        
        return [15]

def get_model():
    global _model
    
    
    
    if _model is None:
        try:
            
            import sklearn
            with open(MODEL_PATH, "rb") as f:
                _model = pickle.load(f)
        except (ImportError, FileNotFoundError, Exception) as e:
            print(f"⚠️ ML Model/Deps not found ({e}). Using Mock Model.")
            _model = MockModel()

    return _model
