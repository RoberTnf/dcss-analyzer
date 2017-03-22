from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

import models


def test_databases():
    db.create_all()
    test_run = models.Morgue("0.19", "kr4n3x", 178, False)
    test_rune = models.Rune(test_run, "serpentine")
    test_rune2 = models.Rune(test_run, "serpentine")
    db.session.add(test_run)
    db.session.add(test_rune)
    db.session.add(test_rune2)
    db.session.commit()
