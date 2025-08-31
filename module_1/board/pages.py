from flask import Blueprint, render_template

bp = Blueprint("pages", __name__)

@bp.route("/")
def home():
    # return "Hello, Home!"
    return render_template("pages/home.html")

@bp.route("/about")
def about():
    # return "Hello, About!"
    return render_template("pages/about.html")