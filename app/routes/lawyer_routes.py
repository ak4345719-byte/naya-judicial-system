from flask import Blueprint, render_template

lawyer_bp = Blueprint('lawyer_bp', __name__)

@lawyer_bp.route("/case-status")
def case_status_page():
    return render_template("case-status.html")



