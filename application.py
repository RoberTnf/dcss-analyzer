import flask
import helpers
from flask_sqlalchemy import SQLAlchemy
from flask_jsglue import JSGlue
from database import db_session

app = flask.Flask(__name__)

JSGlue(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


@app.route('/')
def index():
    return flask.render_template("test.html")


@app.route("/about")
def about():
    return apology("TODO")


@app.route("/search")
def search():
    q = flask.request.args.get("q")
    return helpers.search(q)


def apology(text):
    return flask.render_template("apology.html", text=text)


@app.route("/stats")
def stats():
    """Gets stats to be represented from string"""
    q = flask.request.args.get("q")
    return helpers.stats(q)


@app.teardown_appcontext
def shutdown_session(Exception=None):
    db_session.remove()
