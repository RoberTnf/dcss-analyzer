from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

import models


@app.route('/')
def index():
    return render_template("test.html")


@app.route("/about")
def about():
    return apology("TODO")


@app.route("/search")
def search():
    if not request.args.get("q"):
        return apology("need to search for something")
    return apology("TODO")


def apology(text):
    return render_template("apology.html", text=text)
