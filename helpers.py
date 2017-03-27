#!/usr/bin/env python
import urllib.request
import re
import os
import sys
from bs4 import BeautifulSoup
from models import Morgue, Skill, Spell
from application import db
from os import walk
from os.path import join


def download_morgues(base_url, base_folder="morgues", debug=False):
    """Downloads morgues from base_url into base_folder"""
    # get link to each user morgue's folder
    if debug:
        print("Indexing each user morgue's folder for {}".format(base_url))
    resp_base = urllib.request.urlopen(base_url)
    soup_base = BeautifulSoup(
        resp_base, "html5lib",
        from_encoding=resp_base.info().get_param('charset'))

    # get links to each morgue for user
    for user in soup_base.find_all('a', href=True):
        # avoid the parent directory link and the order links
        if user["href"] != "/crawl/" and user["href"][0] != "?":
            if debug:
                print("Indexing {} morgue's folder".format(user["href"]))
                print("Link : {}".format(base_url + user["href"]))
            resp_user = urllib.request.urlopen(base_url + user["href"])
            soup_user = BeautifulSoup(
                resp_user, "html5lib",
                from_encoding=resp_user.info().get_param('charset'))

            # create directory for user
            directory = base_folder + user["href"]
            if not os.path.exists(directory):
                os.makedirs(directory)
            for morgue in re.findall(re.compile(
                    "morgue.*\.txt"), soup_user.text):
                # check if we already downloaded OR if it is already in the DB
                if not os.path.isfile(directory + morgue) or \
                        Morgue.query.filter_by(filename=directory+morgue):
                    if debug:
                        print("Downloading {}: ".format(
                              base_url + user["href"] + morgue))
                    text = urllib.request.urlopen(
                        base_url + user["href"] + morgue).read()
                    with open(directory + morgue, "wb") as f:
                        f.write(text)
                elif debug:
                    print("{} already exists".format(directory + morgue))


def load_morgues_to_db(debug=False):
    """Loads all the morgues present in directory "morgues" to DB"""
    db.create_all()
    i = 0
    if debug:
        print("loading morgues")
    for dirpath, dirnames, filenames in walk("morgues"):
        for filename in [f for f in filenames if f.endswith(".txt")]:
            if not Morgue.query.filter_by(filename=filename).first():
                run = Morgue(join(dirpath, filename))
                db.session.add(run)
                i += 1
            elif debug:
                print("Morgue already in db")
    print("{} morgues loaded".format(i))
    db.session.commit()


def get_abbreviation():
    """From a race/background, returns its abbreviation.
    Ex: Spriggan -> Sp
          Enchanter -> En
          Hill Orc -> Ho"""
    return apology("TODO")


url = "http://crawl.xtahua.com/crawl/morgue/"
folder = "morgues/crawl-xtahua/"


if len(sys.argv) == 2:
    if sys.argv[1] == "download":
        download_morgues(url, folder, debug=True)
