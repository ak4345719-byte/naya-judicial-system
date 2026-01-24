from flask import Blueprint, render_template, request, jsonify
from app.utils.prediction_engine import predictor_engine

decision_bp = Blueprint('decision_bp', __name__)

@decision_bp.route("/outcome-predictor")
def outcome_predictor_page():
    return render_template("outcome-predictor.html")

@decision_bp.route("/judicial-map")
def judicial_map_page():
    return render_template("judicial_map.html")

@decision_bp.route("/api/ai/simulate-outcome", methods=["POST"])
def simulate_outcome():
    data = request.json
    query = data.get("statute", "")
    bench = data.get("bench", "Gujarat High Court")
    
    # Use the engine to get stats from High Court Metadata
    stats = predictor_engine.get_outcome_stats(query)
    
    return jsonify(stats)
