from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

import models


def test_databases():
    db.create_all()
    from os import listdir
    files = listdir("morgues")
    for file in files:
        test_run = models.Morgue(file)
        db.session.add(test_run)
    db.session.commit()
