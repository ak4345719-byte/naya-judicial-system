from flask import Blueprint, request, jsonify
from ..utils.model_loader import get_model

prediction_bp = Blueprint("prediction", __name__)

@prediction_bp.route("/api/predict-duration", methods=["POST"])
def predict_duration():
    data = request.json

    model = get_model()
    features = [[
        data["complexity"],
        data["judge_experience"]
    ]]

    prediction = model.predict(features)[0]

    return jsonify({
        "predicted_days": int(prediction)
    })
