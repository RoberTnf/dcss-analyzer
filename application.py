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
    return flask.render_template("index.html")


@app.route("/about")
def about():
    return flask.render_template("about.html")


@app.route("/statistics")
def statistics():
    return apology("TODO")


@app.route("/morgue_analyzer")
def morgue_analyzer():
    return apology("TODO")


@app.route("/search")
def search():
    q = flask.request.args.get("q")
    return helpers.search(q)

@app.route("/searchGods")
def searchGods():
    q = flask.request.args.get("q")
    return helpers.searchGods(q)

@app.route("/searchPlayers")
def searchPlayers():
    q = flask.request.args.get("q")
    return helpers.searchPlayers(q)


def apology(text):
    return flask.render_template("apology.html", text=text)


@app.route("/stats")
def stats():
    """Gets stats to be represented from string"""
    return helpers.stats(**flask.request.args)


@app.teardown_appcontext
def shutdown_session(Exception=None):
    db_session.remove()
