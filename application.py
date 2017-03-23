from os import walk
from os.path import join
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

import models


def load_morgues_to_db():
    db.create_all()
    i = 0
    print("loading morgues")
    for dirpath, dirnames, filenames in walk("morgues"):
        for filename in [f for f in filenames if f.endswith(".txt")]:
            if not models.Morgue.query.filter_by(filename=join(dirpath, filename)).first():
                run = models.Morgue(join(dirpath, filename))
                db.session.add(run)
                i += 1
    print("{} morgues loaded".format(i))
    db.session.commit()


def test_databases():
    db.create_all()
    from os import listdir
    files = listdir("morgues")
    for file in files:
        test_run = models.Morgue(file)
        db.session.add(test_run)
    db.session.commit()
