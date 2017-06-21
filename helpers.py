#!/usr/bin/env python

import os
import re
import sys
import urllib.request
from os import listdir, remove, walk
from os.path import isfile, join
from time import time

from bs4 import BeautifulSoup
from database import db_session, init_db
from flask import json, jsonify
from models import BG_abbreviation, Morgue, Race_abbreviation, StatRequest
from sqlalchemy import text
from sqlalchemy.sql import func

# import numpy as np

# global variables
DEBUG = True
N_TO_CACHE = 10000


def download_morgues(base_url, base_folder):
    """Downloads morgues from base_url into base_folder"""

    # get links to each user morgue's folder
    base_folder = "morgues/" + base_folder
    if DEBUG:
        print("Indexing each user morgue's folder for {}".format(base_url))
    resp_base = urllib.request.urlopen(base_url)
    soup_base = BeautifulSoup(
        resp_base, "lxml", from_encoding=resp_base.info().get_param('charset'))

    # get links to each morgue for user
    for user in soup_base.find_all('a', href=True):
        # avoid the parent directory link and the order links
        if user["href"] != "/crawl/" and user["href"][0] != "?" and\
                user["href"] != "../" or "morgue" in user["href"]:
            if DEBUG:
                print("\n\nIndexing {} morgue's folder".format(user["href"]))
                print("Link : {}".format(base_url + user["href"]))
            resp_user = urllib.request.urlopen(base_url + user["href"])
            soup_user = BeautifulSoup(
                resp_user,
                "lxml",
                from_encoding=resp_user.info().get_param('charset'))

            # create directory for user
            directory = base_folder + user["href"]
            if not os.path.exists(directory):
                os.makedirs(directory)

            # download each morgue
            for morgue in re.findall(
                    re.compile("morgue.*\.txt"), soup_user.text):
                # check if we already downloaded OR if it is already in the DB
                if not os.path.isfile(directory + morgue) or \
                        not Morgue.query.filter_by(filename=directory+morgue):
                    if DEBUG:
                        print("Downloading {}: ".format(
                            base_url + user["href"] + morgue))
                    text = urllib.request.urlopen(base_url + user["href"] +
                                                  morgue).read()
                    with open(directory + morgue, "wb") as f:
                        f.write(text)
                elif DEBUG:
                    print("{} already exists".format(directory + morgue))


def load_morgues_to_db(n=0):
    """Loads all the morgues present in directory "morgues" to DB.
    n: max number of morgues to parse, if 0 -> infinite."""

    # create tables if needed
    init_db()
    # counter of morgues parsed
    i = 0
    # counter of morgues already in db
    j = 0

    if DEBUG:
        print("loading morgues")
        t = time()

    # all the filenames of morgues in db
    db_morgues = db_session.query(Morgue.filename).all()

    # do for every *.txt in morgues/
    for dirpath, dirnames, filenames in walk("morgues"):
        for filename in [f for f in filenames if f.endswith(".txt")]:

            # if n morgues added, end
            if i >= n and n > 0:
                print("{} morgues loaded".format(i))
                db_session.commit()
                return

            # add only if not already in db
            if not (filename, ) in db_morgues:
                run = Morgue(join(dirpath, filename), dirpath.split("/")[1])
                if run.crawl and run.time:
                    db_session.add(run)
                i += 1
            else:
                j += 1

            # commit changes to DB every 1000 processed morgues
            if i % 1000 == 0 and i != 0 and DEBUG:
                db_session.commit()
                if DEBUG:
                    print("{} s to load 1000 morgues, total {} morgues".format(
                        time() - t, i))
                    print("{} morgues already in db".format(j))
                    j = 0
                    t = time()

    print("{} morgues loaded".format(i))
    db_session.commit()


def search(q):
    """Returns json object ready for typeahead with search results from DB for
    omnisearch.

    q: string to be searched for."""

    # add results from abbreviations and full strings
    results = Race_abbreviation.query.filter(
        Race_abbreviation.abbreviation.ilike(q + "%")).all()
    results += BG_abbreviation.query.filter(
        BG_abbreviation.abbreviation.ilike(q + "%")).all()
    if len(q) > 2:
        results += BG_abbreviation.query.filter(
            BG_abbreviation.string.ilike(q + "%")).all()
        results += Race_abbreviation.query.filter(
            Race_abbreviation.string.ilike(q + "%")).all()

    # eliminate duplicates and convert to list of dicts
    results = [r.as_dict() for r in set(results)]

    # check for combos
    if len(q) <= 4:
        race = Race_abbreviation.query.filter(
            Race_abbreviation.abbreviation.ilike(q[:2])).first()

        bg = BG_abbreviation.query.filter(
            BG_abbreviation.abbreviation.ilike(q[2:] + "%")).all()

        # as there is not a bg+race table we create an .as_dict object
        if race and bg:
            for i in bg:
                r = {
                    "abbreviation":
                    "{}{}".format(race.abbreviation, i.abbreviation),
                    "string":
                    "{} {}".format(race.string, i.string)
                }
                results.append(r)

    return jsonify(results)


def searchGods(q):
    """Returns json object ready for typeahead with search results from DB for
    god filter.

    q: string to be searched for."""
    results = Morgue.query.filter(Morgue.god.ilike(q + "%")).distinct(
        Morgue.god).all()
    # eliminate duplicates and convert to list of dicts
    results = [{"suggestion": r.god} for r in set(results)]

    return jsonify(results)


def searchPlayers(q):
    """Returns json object ready for typeahead with search results from DB for
    player filter.

    q: string to be searched for."""
    results = Morgue.query.filter(Morgue.name.ilike(q + "%")).distinct(
        Morgue.name).all()
    # eliminate duplicates and convert to list of dicts
    results = [{"suggestion": r.name} for r in set(results)]

    return jsonify(results)


def stats(**kwargs):
    """Returns json object with stats.

    kwargs: filters to be applied, valid values are:
        abbreviation, god, name, success, runes, version"""

    # ~~~~~~~~~~~~~~~~~~~~~~~~~ CACHE MANAGEMENT
    # create string with all kwargs
    keys = list(kwargs.keys())
    keys.sort()
    request = "?"
    for key in keys:
        if key != "caching":
            request += "{}={}&".format(key, kwargs[key][0])

    # if it has been searched
    stat = StatRequest.query.filter(StatRequest.request == request).first()
    if stat:
        # if cached, just load it
        if cached(stat):
            json_data = json.load(open("cached/{}.json".format(request)))
            stat.times += 1
            db_session.commit()
            if "caching" not in kwargs:
                return jsonify(json_data)
            else:
                return()
        else:
            stat.times += 1
            db_session.commit()
    else:
        stat = StatRequest(request=request)
        db_session.add(stat)
        db_session.commit()
    # ~~~~~~~~~~~~~~~~~~~~~~~~~ END OF CACHE MANAGEMENT

    results = {}  # dictionary in which the stats will be appended

    # we will be using Morgue.query for some cases and db_session.query()
    # in other cases, as even though Morgue.query is more legible, you can't
    # use sqlalchemy.func
    morgues = Morgue.query
    case = None  # will be used to know which type of abbreviation was passed
    db_filter = ""  # will be appended to form a SQL filter

    if DEBUG:
        t = time()
        t_tot = time()

    if "abbreviation" in kwargs:
        abv = kwargs["abbreviation"][0]
        if len(abv) == 2:
            # check if abv is a race
            if morgues.filter(Race_abbreviation.abbreviation == abv).first():
                id = Race_abbreviation.query.filter(
                    Race_abbreviation.abbreviation == abv).first()
                if id:
                    id = id.id

                    morgues = morgues.filter(Morgue.race_id == id)

                    if db_filter:
                        db_filter += " AND morgues.race_id = {}".format(id)
                    else:
                        db_filter += "morgues.race_id = {}".format(id)
                    case = "race"

            # check if abv is a background
            elif morgues.filter(BG_abbreviation.abbreviation == abv).first():
                id = BG_abbreviation.query.filter(
                    BG_abbreviation.abbreviation == abv).first()
                if id:
                    id = id.id

                    morgues = morgues.filter(Morgue.background_id == id)

                    if db_filter:
                        db_filter += " AND morgues.background_id = {}"\
                            .format(id)
                    else:
                        db_filter += "morgues.background_id = {}".format(id)
                    case = "bg"

        elif len(abv) == 4:
            # check if abv is a combo
            bg_id = BG_abbreviation.query.filter(
                BG_abbreviation.abbreviation == abv[2:]).first()
            race_id = Race_abbreviation.query.filter(
                Race_abbreviation.abbreviation == abv[:2]).first()

            if race_id and bg_id:
                race_id = race_id.id
                bg_id = bg_id.id
                morgues = morgues.filter((Morgue.race_id == race_id) & (
                    Morgue.background_id == bg_id))

                if db_filter:
                    db_filter += " AND morgues.race_id = {}\
                        AND morgues.background_id = {}"\
                        .format(race_id, bg_id)
                else:
                    db_filter += "morgues.race_id = {}\
                         AND morgues.background_id = {}"\
                        .format(race_id, bg_id)
                case = "combo"

        if not case:
            # if abv was passed, but it wasnt a race, bg or combo
            results["ERROR"] = "No results for your query"
            if "caching" not in kwargs:
                return jsonify(results)
            else:
                return()

    # apply filters provided in kwargs
    if "god" in kwargs:
        morgues = morgues.filter(Morgue.god == kwargs["god"][0])

        if db_filter:
            db_filter += " AND morgues.god = '{}'".format(kwargs["god"][0])
        else:
            db_filter += "morgues.god = '{}'".format(kwargs["god"][0])
    if "name" in kwargs:
        morgues = morgues.filter(Morgue.name == kwargs["name"][0])

        if db_filter:
            db_filter += " AND morgues.name = '{}'".format(kwargs["name"][0])
        else:
            db_filter += "morgues.name = '{}'".format(kwargs["name"][0])
    if "success" in kwargs:
        morgues = morgues.filter(Morgue.success == kwargs["success"][0])

        if db_filter:
            db_filter += " AND morgues.success = '{}'"\
                .format(kwargs["success"][0])
        else:
            db_filter += "morgues.success = '{}'".format(kwargs["success"][0])
    if "runes" in kwargs:
        morgues = morgues.filter(Morgue.runes == kwargs["runes"][0])

        if db_filter:
            db_filter += " AND morgues.runes = '{}'".format(kwargs["runes"][0])
        else:
            db_filter += "morgues.runes = '{}'".format(kwargs["runes"][0])

    if "version" in kwargs:
        # version = 0.15.4645 -> 0.15
        version = kwargs["version"][0][:4] + "%"
        morgues = morgues.filter(Morgue.version.ilike(version))

        if db_filter:
            db_filter += " AND morgues.version LIKE '{}%'"\
                .format(kwargs["version"][0])
        else:
            db_filter += "morgues.version LIKE '{}%'"\
                .format(kwargs["version"][0])

    # if after applying filters there's no result
    if not morgues.first():
        results["ERROR"] = "No results for your query"
        if "caching" not in kwargs:
            return jsonify(results)
        else:
            return()

    if DEBUG:
        print("{} s to filter.".format(time() - t))
        t = time()

    # most common branch_order

    # get the most traveserd branch order
    # results["branch_order"] = get_medium_branch_order(
    #     [morgue.branch_order for morgue in morgues.all()])

    # calculate a lot of means
    results["mean_time"] = round(
        custom_float(
            db_session.query(func.avg(Morgue.time)).filter(text(db_filter))
            .first()[0]) / 3600, 2)
    results["mean_turns"] = round(
        custom_float(
            db_session.query(func.avg(Morgue.turns)).filter(text(db_filter))
            .first()[0]), 2)
    results["mean_XL"] = round(
        custom_float(
            db_session.query(func.avg(Morgue.XL)).filter(text(db_filter))
            .first()[0]), 2)
    results["mean_Str"] = round(
        custom_float(
            db_session.query(func.avg(Morgue.Str)).filter(text(db_filter))
            .first()[0]), 2)
    results["mean_AC"] = round(
        custom_float(
            db_session.query(func.avg(Morgue.AC)).filter(text(db_filter))
            .first()[0]), 2)
    results["mean_Int"] = round(
        custom_float(
            db_session.query(func.avg(Morgue.Int)).filter(text(db_filter))
            .first()[0]), 2)
    results["mean_EV"] = round(
        custom_float(
            db_session.query(func.avg(Morgue.EV)).filter(text(db_filter))
            .first()[0]), 2)
    results["mean_Dex"] = round(
        custom_float(
            db_session.query(func.avg(Morgue.Dex)).filter(text(db_filter))
            .first()[0]), 2)
    results["mean_SH"] = round(
        custom_float(
            db_session.query(func.avg(Morgue.SH)).filter(text(db_filter))
            .first()[0]), 2)

    results["games"] = morgues.count()

    results["wins"] = morgues.filter(Morgue.success).count()
    results["winrate"] = str(results["wins"] * 100 / results["games"]) + "%"

    if DEBUG:
        print("{} s to calculate means.".format(time() - t))
        t = time()

    # most played god, player, etc...
    if "name" not in kwargs:
        # Only top 100 players, as more won't be nicelly graphed
        results["players"] = db_session.query(
            Morgue.name, func.count(Morgue.name).label("c")).filter(
            text(db_filter)).group_by(Morgue.name).order_by("c DESC")\
            .all()

    if "god" not in kwargs:
        results["gods"] = db_session.query(Morgue.god, func.count(
            Morgue.god)).filter(text(db_filter)).group_by(Morgue.god).all()

    if not kwargs.get("success"):
        results["killers"] = db_session.query(
            Morgue.killer, func.count(Morgue.killer)).filter(
                text(db_filter)).group_by(Morgue.killer).all()

    if case != "race" and case != "combo":
        # this generates: [(id, number of appearences)]
        races = db_session.query(
            Morgue.race_id, func.count(Morgue.race_id)).filter(
                text(db_filter)).group_by(Morgue.race_id).all()
        # we convert to: [(abbreviation, number of appearences)]
        for i, e in enumerate(races):
            if e[0]:
                races[i] = (Race_abbreviation.query.filter(
                    Race_abbreviation.id == e[0]).first().abbreviation, e[1])

        results["races"] = races

    if case != "bg" and case != "combo":
        # this generates: [(id, number of appearences)]
        bgs = db_session.query(
            Morgue.background_id, func.count(Morgue.background_id)).filter(
                text(db_filter)).group_by(Morgue.background_id).all()
        # we convert to: [(abbreviation, number of appearences)]
        for i, e in enumerate(bgs):
            if e[0]:
                bgs[i] = (BG_abbreviation.query.filter(
                    BG_abbreviation.id == e[0]).first().abbreviation, e[1])

        results["bgs"] = bgs

    if DEBUG:
        print("{} s to obtain name, god and killer lists.".format(time() - t))
        print("{} s in total.".format(time() - t_tot))

    update_cached(stat, results)
    if "caching" not in kwargs:
        return jsonify(results)
    else:
        return()


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
        return (most_common_branch[:most_common_branch.find("Z") + 1])
    else:
        return (most_common_branch + "Z")


if len(sys.argv) == 2:
    if sys.argv[1] == "download":
        servers = [
            {
                "url": "http://crawl.xtahua.com/crawl/morgue/",
                "folder": "crawl-xtahua/"
            },
            {
                "url": "https://crawl.project357.org/morgue/",
                "folder": "crawl-project357/"
            },
            {
                "url": "http://crawl.berotato.org/crawl/morgue/",
                "folder": "crawl-berotato/"
            },
        ]

        for server in servers:
            download_morgues(server["url"], server["folder"])


def create_cached():
    """Creates json of the more general searches"""
    p = {
        "success": ["0", "1"],
        "version": ["0.13", "0.14", "0.15", "0.16", "0.17", "0.18", "0.19",
                    "0.20", "0.21"],
        "runes": ["3", "15"],
        "god": [],
        "abbreviation": []
        }

    for god in db_session.query(Morgue.god).distinct():
        if god:
            p["god"].append(god[0])

    for race in db_session.query(Race_abbreviation.abbreviation).distinct():
        if race:
            p["abbreviation"].append(race[0])

    for bg in db_session.query(BG_abbreviation.abbreviation).distinct():
        if bg:
            p["abbreviation"].append(bg[0])

    print("general")
    q = {"caching": True}
    stats(**q)

    for s in p["success"]:
        q = {"success": [s], "caching": True}
        print(q)
        stats(**q)
        for v in p["version"]:
            q = {"success": [s], "version": [v], "caching": True}
            print(q)
            stats(**q)
        for g in p["god"]:
            q = {"success": [s], "god": [g], "caching": True}
            print(q)
            stats(**q)
        for ab in p["abbreviation"]:
            q = {"success": [s], "abbreviation": [ab], "caching": True}
            print(q)
            stats(**q)

    for v in p["version"]:
        q = {"version": [v], "caching": True}
        print(q)
        stats(**q)
    for g in p["god"]:
        q = {"god": [g], "caching": True}
        print(q)
        stats(**q)
    for ab in p["abbreviation"]:
        q = {"abbreviation": [ab], "caching": True}
        print(q)
        stats(**q)


def custom_float(f):
    """Allows converting None to 0"""
    if f:
        return(float(f))
    else:
        return(0.00)
