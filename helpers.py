#!/usr/bin/env python
import urllib.request
import re
import os
import sys
import numpy as np
from bs4 import BeautifulSoup
from models import Morgue, BG_abbreviation, Race_abbreviation, StatRequest
from database import db_session, init_db
from os import walk, remove, listdir
from os.path import join, isfile
from flask import jsonify, json

N_TO_CACHE = 100


def download_morgues(base_url, base_folder="morgues", debug=False):
    """Downloads morgues from base_url into base_folder"""
    # get link to each user morgue's folder
    if debug:
        print("Indexing each user morgue's folder for {}".format(base_url))
    resp_base = urllib.request.urlopen(base_url)
    soup_base = BeautifulSoup(
        resp_base, "lxml",
        from_encoding=resp_base.info().get_param('charset'))

    # get links to each morgue for user
    for user in soup_base.find_all('a', href=True):
        # avoid the parent directory link and the order links
        if user["href"] != "/crawl/" and user["href"][0] != "?":
            if debug:
                print("\n\nIndexing {} morgue's folder".format(user["href"]))
                print("Link : {}".format(base_url + user["href"]))
            resp_user = urllib.request.urlopen(base_url + user["href"])
            soup_user = BeautifulSoup(
                resp_user, "lxml",
                from_encoding=resp_user.info().get_param('charset'))

            # create directory for user
            directory = base_folder + user["href"]
            if not os.path.exists(directory):
                os.makedirs(directory)
            for morgue in re.findall(re.compile(
                    "morgue.*\.txt"), soup_user.text):
                # check if we already downloaded OR if it is already in the DB
                if not os.path.isfile(directory + morgue) or \
                        not Morgue.query.filter_by(filename=directory+morgue):
                    if debug:
                        print("Downloading {}: ".format(
                              base_url + user["href"] + morgue))
                    text = urllib.request.urlopen(
                        base_url + user["href"] + morgue).read()
                    with open(directory + morgue, "wb") as f:
                        f.write(text)
                elif debug:
                    print("{} already exists".format(directory + morgue))


def load_morgues_to_db(debug=False, n=0):
    """Loads all the morgues present in directory "morgues" to DB"""
    init_db()
    i = 0
    if debug:
        print("loading morgues")
    for dirpath, dirnames, filenames in walk("morgues"):
        for filename in [f for f in filenames if f.endswith(".txt")]:
            if i >= n and n > 0:
                print("{} morgues loaded".format(i))
                db_session.commit()
                return
            if not Morgue.query.filter_by(filename=filename).first():
                run = Morgue(join(dirpath, filename))
                if run.crawl and run.time:
                    db_session.add(run)
                i += 1
            elif debug:
                print("Morgue already in db")
    print("{} morgues loaded".format(i))
    db_session.commit()


def search(q):
    results = Race_abbreviation.query.filter(
        Race_abbreviation.abbreviation.like(q + "%")
        ).all()
    results += BG_abbreviation.query.filter(
        BG_abbreviation.abbreviation.like(q + "%")
        ).all()
    return jsonify([result.as_dict() for result in results])


def stats(**kwargs):
    keys = list(kwargs.keys())
    keys.sort()
    request = "?"
    for key in keys:
        request += "{}={}&".format(key, kwargs[key][0])

    # if it has been searched
    stat = StatRequest.query.filter(StatRequest.request == request).first()
    if stat:
        # if cached, just load it
        if cached(stat):
            json_data = json.load(open("cached/{}.json".format(request)))
            stat.times += 1
            db_session.commit()
            return jsonify(json_data)
        else:
            stat.times += 1
            db_session.commit()
    else:
        stat = StatRequest(request=request)
        db_session.add(stat)
        db_session.commit()

    results = {}
    morgues = Morgue.query
    case = None
    if "abbreviation" in kwargs:
        abv = kwargs["abbreviation"][0]
        # check if q is an abbreviation
        if len(abv) == 2:
            # check if abv is a race
            if morgues.filter(Race_abbreviation.abbreviation == abv).first():
                id = Race_abbreviation.query.filter(
                    Race_abbreviation.abbreviation == abv).first().id
                morgues = morgues.filter(
                    Morgue.race_id == id)
                case = "race"
            # check if abv is a background
            elif morgues.filter(BG_abbreviation.abbreviation == abv).first():
                id = BG_abbreviation.query.filter(
                    BG_abbreviation.abbreviation == abv).first().id
                morgues = morgues.filter(
                    Morgue.background_id == id)
                case = "bg"
        elif len(abv) == 4:
            bg_id = BG_abbreviation.query.filter(
                BG_abbreviation.abbreviation == abv[2:]).first().id
            race_id = Race_abbreviation.query.filter(
                Race_abbreviation.abbreviation == abv[:2]).first().id
            morgues = morgues.filter(
                (Morgue.race_id == race_id) &
                (Morgue.background_id == bg_id))
            case = "combo"

    # apply filters provided in kwargs
    if "god" in kwargs:
        morgues = morgues.filter(Morgue.god == kwargs["god"][0])
    if "name" in kwargs:
        morgues = morgues.filter(Morgue.name == kwargs["name"][0])
    if "success" in kwargs:
        morgues = morgues.filter(Morgue.success == kwargs["success"][0])
    if "runes" in kwargs:
        morgues = morgues.filter(Morgue.runes == kwargs["runes"][0])
    if "version" in kwargs:
        # version = 0.15.4645 -> 0.15
        version = kwargs["version"][0][:4] + "%"
        morgues = morgues.filter(Morgue.version.like(version))

    if not morgues.first():
        results["ERROR"] = "No results for your query"
        return jsonify(results)

    # fill results with information about the runs
    if case == "bg":
        # makes a dictionary with every race with its number of appearences
        races = {}
        for race in Race_abbreviation.query.all():
            races[Race_abbreviation.query.filter(
                Race_abbreviation.id == race.id).first().string] =\
                morgues.filter(Morgue.race_id == race.id).count()
        results["races"] = races

    if case == "race":
        bgs = {}
        for bg in BG_abbreviation.query.all():
            bgs[BG_abbreviation.query.filter(
                BG_abbreviation.id == bg.id).first().string] =\
                morgues.filter(Morgue.background_id == bg.id).count()
        results["bgs"] = bgs

    # most common branch_order
    results["branch_order"] = get_medium_branch_order(
        [morgue.branch_order for morgue in morgues.all()])

    results["mean_time"] = np.array([m.time for m in morgues.all()]).mean()

    results["mean_turns"] = np.array([m.turns for m in morgues.all()]).mean()

    results["wins"] = morgues.filter(Morgue.success).count()
    results["games"] = morgues.count()
    results["winrate"] = str(results["wins"] * 100 / results["games"]) + "%"

    results["mean_XL"] = np.array([m.XL for m in morgues.all()]).mean()
    results["mean_Str"] = np.array([m.Str for m in morgues.all()]).mean()
    results["mean_AC"] = np.array([m.AC for m in morgues.all()]).mean()
    results["mean_Int"] = np.array([m.Int for m in morgues.all()]).mean()
    results["mean_EV"] = np.array([m.EV for m in morgues.all()]).mean()
    results["mean_Dex"] = np.array([m.Dex for m in morgues.all()]).mean()
    results["mean_SH"] = np.array([m.SH for m in morgues.all()]).mean()

    if "name" not in kwargs:
        players = {}
        for player in morgues.distinct(Morgue.name).all():
            players[player.name] = morgues.filter(Morgue.name == player.name).count()
        results["players"] = players

    if "god" not in kwargs:
        gods = {}
        for god in morgues.distinct(Morgue.god).all():
            if god.god:
                gods[god.god] = morgues.filter(Morgue.god == god.god).count()
            else:
                gods["none"] = morgues.filter(Morgue.god == None).count()
        results["gods"] = gods

    if not kwargs.get("success"):
        killers = {}
        for killer in morgues.distinct(Morgue.killer).all():
            if killer.killer:
                killers[killer.killer] = morgues.filter(Morgue.killer == killer.killer).count()
            else:
                killers["none"] = morgues.filter(Morgue.killer == None).count()
        results["killers"] = killers
    update_cached(stat, results)

    return jsonify(results)


def update_cached(stat, results):
    """Checks if stat, (from StatRequest), needs to be cached"""
    # get and sort stats
    stats = StatRequest.query.all()
    stats.sort(key=lambda x: x.times, reverse=True)

    if stat in stats[:N_TO_CACHE]:
        json.dump(results, open("cached/{}.json".format(stat.request), "w"))
    return True


def cached(stat):
    return isfile("cached/{}.json".format(stat.request))


def rm_cached():
    for file in listdir("cached"):
        remove("cached/{}".format(file))


def most_common(lst):
    """Returns the most common element on lst"""
    return max(set(lst), key=lst.count)


def max_len(lst):
    """Returns the longitude of the largest element on the list"""
    return len(max(set(lst), key=len))


def get_medium_branch_order(branch_orders):
    """Returns the most common branch order, only takes into account the order
    of first entrance
    """

    # reduced_branch_orders is a list with just the letter of each branch
    reduced_branch_orders = []
    for branch_order in branch_orders:
        reduced_branch_orders.append("")
        for branch in branch_order.split(" ")[:-1]:
            reduced_branch_orders[-1] += branch[0]

    # calculate the most common order of branches, up untill zot
    most_common_branch = ""
    for i in range(max_len(reduced_branch_orders)):
        branchs = ""
        for branch_order in reduced_branch_orders:
            if len(branch_order) > i:
                branchs += branch_order[i]
        if most_common(branchs) not in most_common_branch:
            most_common_branch += most_common(branchs)
    # only up until Zot, but add zot if not found
    if most_common_branch.find("Z") != -1:
        return(most_common_branch[:most_common_branch.find("Z") + 1])
    else:
        return(most_common_branch + "Z")


if len(sys.argv) == 2:
    if sys.argv[1] == "download":
        url = "http://crawl.xtahua.com/crawl/morgue/"
        folder = "morgues/crawl-xtahua/"
        download_morgues(url, folder, debug=True)
