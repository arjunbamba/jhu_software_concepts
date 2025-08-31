from flask import Blueprint, render_template

bp = Blueprint("pages", __name__)

@bp.route("/")
def home():
    # return "Hello, Home!"
    return render_template("pages/home.html")

@bp.route("/projects")
def projects():
    # return "Hello, Projects!"
    return render_template("pages/projects.html")

@bp.route("/contact")
def contact():
    # return "Hello, Contact!"
    return render_template("pages/contact.html")