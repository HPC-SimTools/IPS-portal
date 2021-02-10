from flask import Blueprint, render_template

from ipsportal.db import get_db

bp = Blueprint('index', __name__)


@bp.route("/")
def index():
    """Show all the posts, most recent first."""
    db = get_db()
    runs = db.execute("SELECT * FROM run").fetchall()
    return render_template("index.html", runs=runs)
