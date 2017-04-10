import re
from datetime import date
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy import ForeignKey, Text, Date, Float
from sqlalchemy.orm import relationship, backref
from database import Base, db_session

debug = True


class StatRequest(Base):
    """Holds each request done to /stats, with the number of time done,
    to cache most requested
    """

    __tablename__ = "statrequests"
    __searchable__ = ["request"]

    id = Column(Integer, primary_key=True)
    request = Column(String(400))
    times = Column(Integer)

    def __init__(self, request):
        self.request = request
        self.times = 1


class Morgue(Base):
    """Main class of the  Holds most information about the run"""

    __tablename__ = "morgues"
    __searchable__ = ["filename", "name", "success", "version", "god", "runes", "killer"]

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String(30))
    name = Column(String(30))
    time = Column(Integer)
    turns = Column(Integer)
    success = Column(Boolean)
    XL = Column(Integer)
    Str = Column(Integer)
    AC = Column(Integer)
    Int = Column(Integer)
    EV = Column(Integer)
    Dex = Column(Integer)
    SH = Column(Integer)
    god = Column(String(20))
    faith = Column(Integer)
    branch_order = Column(Text)
    killer = Column(String(80))
    filename = Column(String(200))
    date = Column(Date)
    runes = Column(Integer)

    race_id = Column(Integer, ForeignKey("race_abbreviations.id"))
    race = relationship("Race_abbreviation")
    background_id = Column(Integer, ForeignKey("bg_abbreviations.id"))
    background = relationship("BG_abbreviation")

    def __init__(self, filename):
        self.version = None
        self.name = None
        self.time = None
        self.turns = None
        self.success = False
        self.XL = None
        self.Str = None
        self.AC = None
        self.EV = None
        self.Int = None
        self.SH = None
        self.Dex = None
        self.god = None
        self.faith = None
        self.branch_order = ""
        self.killer = None
        self.date = None
        self.filename = filename.split("/")[-1]
        self.runes = 0
        self.race = None
        self.background = None
        self.crawl = True

        version_regex = re.compile("version ([0-9A-Za-z\.\-]+)")
        name_regex = re.compile("(\d+ )(\w+)( the)")
        time_regex = re.compile("lasted (\d*).*?(\d\d:\d\d:\d\d) \((\d+)")
        success_regex = re.compile("Escaped with the Orb")
        race_combo_regex = re.compile("Began as an* (.*) on")
        XL_regex = re.compile("AC.+?(\d+).+?Str.+?(\d+).+?XL.+?(\d+)")
        EV_regex = re.compile("EV.+?(\d+).+?Int.+?(\d+).+?God.+?(.*)")
        faith_regex = re.compile("(.+?)\s+\[(\**)")
        SH_regex = re.compile("SH.+?(\d+).+?Dex.+?(\d+)")
        killer_regex = re.compile("by (.*?) \(|by (.*?)$")
        quit_regex = re.compile("Quit the game")
        pois_regex = re.compile("Succumbed to (.*?)\n")
        suicide_regex = re.compile("Killed themself")
        starved_regex = re.compile("Starved")
        branch_regex = re.compile("\d+\s+\|\s+(.+?)\s+\|")
        date_regex = re.compile(".*?-(\d\d\d\d)(\d\d)(\d\d)-")
        skill_regex = re.compile("...Level (\d+\.?\d?).*? (.+)\n")
        rune_regex = re.compile("(\d+)/15 runes:")
        spell_regex = re.compile("\w - (.*?)  \s*.+?#|\w - (.*?)  \s*.+?N/A")
        got_out_regex = re.compile("out of the dungeon.")
        afar_regex = re.compile("Killed from afar by (.+?) \(")

        with open(filename) as f:
            d = [int(i) for i in re.search(date_regex, filename).groups()]
            self.date = date(*d)
            self.name = re.search(re.compile("morgue-(.*?)-"), filename).group(1)
            for line in f.readlines():
                if not self.version:
                    found = re.search(version_regex, line)
                    if found:
                        self.version = found.group(1)
                        if "Sprint" in line:
                            self.crawl = False
                            break

                if not self.time:
                    found = re.search(time_regex, line)
                    if found:
                        days = found.group(1)
                        time = [int(i) for i in found.group(2).split(":")]
                        self.turns = found.group(3)
                        # time in seconds
                        if not days:
                            days = 0
                        else:
                            days = int(days)
                        self.time = days*86400+time[0]*3600+time[1]*60+time[2]

                if not self.success:
                    found = re.search(success_regex, line)
                    if found:
                        self.success = True

                if not self.race:
                    found = re.search(race_combo_regex, line)
                    if found:
                        race_string, background_string =\
                            race_background(found.group(1))
                        self.race = Race_abbreviation.query.filter_by(
                            string=race_string).first()
                        if not self.race:
                            self.race = Race_abbreviation(race_string)
                            db_session.add(self.race)
                            db_session.commit()
                        self.background = BG_abbreviation.query\
                            .filter_by(string=background_string).first()
                        if not self.background:
                            self.background = BG_abbreviation(
                                background_string)
                            db_session.add(self.background)
                            db_session.commit()

                if not self.XL:
                    found = re.search(XL_regex, line)
                    if found:
                        self.AC, self.Str, self.XL = found.groups()

                if not self.EV:
                    found = re.search(EV_regex, line)
                    if found:
                        self.EV, self.Int, god = found.groups()
                        god = god.strip()
                        if "Gozag" in god:
                            self.god = "Gozag"
                        elif "Xom" in god:
                            self.god = "Xom"
                        elif god != "" and "No God" not in god:
                            # weird morgues:
                            # morgue-NekoKawashu-20150527-130543.txt
                            if god[0] == "*":
                                c = god.count("*")
                                god = god[c:] + "  [{}]".format(c*"*")
                            found = re.search(faith_regex, god)
                            try:
                                self.god = found.groups()[0]
                                self.faith = len(found.groups()[1])
                            except AttributeError:
                                print("GodError: {}".format(god))
                                self.god = god.split(" ")[0]

                if not self.SH:
                    found = re.search(SH_regex, line)
                    if found:
                        self.SH, self.Dex = found.groups()

                if not self.killer:
                    found = re.search(killer_regex, line)
                    found2 = re.search(starved_regex, line)
                    found3 = re.search(pois_regex, line)
                    found4 = re.search(suicide_regex, line)
                    found5 = re.search(got_out_regex, line)
                    if found:
                        if found.group(1):
                            self.killer = found.group(1)
                        else:
                            self.killer = found.group(2)
                        if "Lernaean" in self.killer:
                            self.killer = "Lernaean hydra"
                        elif "hydra" in self.killer:
                            self.killer = "an hydra"
                        elif "ghost" in self.killer:
                            self.killer = "a ghost"
                    elif found2:
                        self.killer = "starved"
                    elif re.search(re.compile("Rotted away (\(.*?\))"), line):
                        self.killer = re.search(re.compile("Rotted away (\(.*?\))"), line).group(0)
                    elif re.search(re.compile("Asphyxiated"), line):
                        self.killer = "Asphyxiated"
                    elif re.search(quit_regex, line):
                        self.killer = "quit"
                    elif self.success:
                        self.killer = "won"
                    elif found3:
                        self.killer = found3.group(1)
                    elif found4:
                        self.killer = "suicide"
                    elif found5:
                        self.killer = "got out of the dungeon"

                found = re.search(branch_regex, line)
                if found:
                    branch = found.group(1)
                    self.parse_branch_order(branch)

                # check for runes
                if not self.runes:
                    found = re.search(rune_regex, line)
                    if found:
                        self.runes = found.group(1)

                # from now on, we need new tables to store what we are parsing
                # check for skills, we are using match instead of search,
                # because we only want to check against the beginning of
                # the line, to avoid false positives
                found = re.match(skill_regex, line)
                if found:
                    skill = Skill(self, found.group(2), found.group(1))
                    db_session.add(skill)


                # check for spells
                found = re.match(spell_regex, line)
                if found:
                    if found.group(1):
                        spell = Spell(self, found.group(1))
                    else:
                        spell = Spell(self, found.group(2))
                    db_session.add(spell)

        if not self.god:
            self.god = "none"
        if not self.killer and self.crawl:
            self.killer = "Error parsing"
            if debug:
                print(self.filename)


    def as_dict(self):
        return {c.name: getattr(self, c.name)
                for c in self.__table__.columns}

    def parse_branch_order(self, branch_string):
        """Adds to morgue.branch_order branch correctly"""
        # we won't add unique dungeons like sewer, volcanos...
        if self.branch_order:
            branch_order_list = self.branch_order.split()

        if branch_string.find(":") >= 0:
            branch_list = branch_string.split(":")
            branch = get_branch_abbreviation(branch_list[0])
            floor = branch_list[1]
            # check that branch follows our expected format
            if branch.isalpha() and floor.isnumeric():
                # check if we have already visited branch
                if self.branch_order:
                    if branch in branch_order_list[-1]:
                        if int(floor) > int(branch_order_list[-1].split("-")[1]):
                            branch_order_list[-1] = branch_order_list[-1].split("-")[0] + "-" + floor.strip()
                            self.branch_order = " ".join(branch_order_list) + " "
                    else:
                        self.branch_order += "{}{}-{} ".format(branch.strip(), floor.strip(), floor.strip())
                else:
                    self.branch_order = "{}{}-{} ".format(branch.strip(), floor.strip(), floor.strip())


class Skill(Base):
    """Stores learned skills, backrefs to morgue"""
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    morgue_id = Column(Integer, ForeignKey("morgues.id"))
    morgue = relationship("Morgue",
                          backref=backref("skills", lazy="dynamic"))
    name_id = Column(Integer, ForeignKey("skill_table.id"))
    name = relationship("Skill_table")
    level = Column(Float)

    def __init__(self, morgue, skill_name, skill_level):
        self.morgue = morgue
        self.level = skill_level
        query = Skill_table.query.filter_by(skill_name=skill_name).first()
        if query:
            self.name = query
        else:
            self.name = Skill_table(skill_name)
            db_session.add(self.name)
            db_session.commit()


class Skill_table(Base):
    """Table containing each skill in the game"""
    __tablename__ = "skill_table"

    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_name = Column(String(20))

    def __init__(self, skill_name):
        self.skill_name = skill_name


class Spell(Base):
    """Stores learned spells, backrefs to morgue"""
    __tablename__ = "spells"

    id = Column(Integer, primary_key=True, autoincrement=True)
    morgue_id = Column(Integer, ForeignKey("morgues.id"))
    morgue = relationship("Morgue",
                          backref=backref("spells", lazy="dynamic"))
    name_id = Column(Integer, ForeignKey("spell_table.id"))
    name = relationship("Spell_table")

    def __init__(self, morgue, spell_name):
        self.morgue = morgue
        query = Spell_table.query.filter_by(spell_name=spell_name).first()
        if query:
            self.name = query
        else:
            self.name = Spell_table(spell_name)
            db_session.add(self.name)
            db_session.commit()


class Spell_table(Base):
    """Table containing each spell in the game"""
    __tablename__ = "spell_table"

    id = Column(Integer, primary_key=True, autoincrement=True)
    spell_name = Column(String(20))

    def __init__(self, spell_name):
        self.spell_name = spell_name


class Race_abbreviation(Base):
    """Links each race to its abbreviation, morgues should reffer
    to a element of this table"""
    __tablename__ = "race_abbreviations"
    __searchable__ = "abbreviation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    abbreviation = Column(String(4))
    string = Column(String(20))

    def __init__(self, string):
        self.abbreviation, self.string = get_abbreviation(string)

    def as_dict(self):
        return {c.name: getattr(self, c.name)
                for c in self.__table__.columns}


class BG_abbreviation(Base):
    """Links each background to its abbreviation, morgues should reffer
    to a element of this table"""
    __tablename__ = "bg_abbreviations"
    __searchable__ = "abbreviation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    abbreviation = Column(String(4))
    string = Column(String(20))

    def __init__(self, string):
        self.abbreviation, self.string = get_abbreviation(string)

    def as_dict(self):
        return {c.name: getattr(self, c.name)
                for c in self.__table__.columns}


def race_background(race_combo):
    """Given string consisting of race/background combo, separates it in
    the correct race | background.

    Examples:
    "Spriggan enchanter" -> "Spriggan", "enchanter"
    "Gargoyle Earth Elementalist" -> "Gargoyle", "Earth Elementalist" """

    # list of all the races consisting of 2 words, might change
    two_word_races = ["Hill Orc", "Deep Elf", "Deep Dwarf", "Vine Stalker",
                      "High Elf", "High Dwarf", "Grey Elf", "Gnome",
                      "Mountain Dwarf", "Sludge Elf"]

    # separate line into a list of words
    words = race_combo.split()

    if "Draconian" in words:
        return("Draconian", "".join(words[words.index("Draconian") + 1:]))
    # if only two words, it is already separated
    if len(words) == 2:
        return words

    # given that the max number per race/background is 2 if the combination
    # amounts to 4, we can split on the middle
    elif len(words) == 4:
        return(" ".join(words[0:2]), " ".join(words[2:]))

    # else, the len is 3 and we need to check vs two_word_races
    elif " ".join(words[0:2]) in two_word_races:
        return(" ".join(words[0:2]), words[2])

    else:
        return(words[0], " ".join(words[1:]))


def get_abbreviation(string):
    """From a race/background, returns its abbreviation.
    Ex: Spriggan -> Sp
          Enchanter -> En
          Hill Orc -> Ho"""

    # List of every race/background whose abbreviation isn't the first 2
    # letters or the initials of two words
    weird_abb = {"Demigod": "Dg", "Demonspawn": "Ds", "Draconian": "Dr",
                 "Gargoyle": "Gr", "Merfolk": "Mf", "Octopode": "Op",
                 "Vampire": "Vp", "Transmuter": "Tm", "Warper": "Wr",
                 "Wizard": "Wz", "Conjurer": "Cj", "Artificer": "Ar",
                 "Wanderer": "Wn"}

    if string in weird_abb.keys():
        abbreviation = weird_abb[string]
        string_cp = string

    # we check for number of upper letters instead of spaces because some
    # morgues are weird -> Chaos Knight as ChaosKnight -.-
    elif sum(1 for c in string if c.isupper()) == 1:
        abbreviation = string[:2]
        string_cp = string
    else:
        abbreviation = string[0]
        string_cp = string[0]
        for c in string[1:]:
            if c.isupper():
                abbreviation += c
                string_cp += " " + c
            elif c != " ":
                string_cp += c

    return abbreviation, string_cp


def get_branch_abbreviation(branch_string):
    """Returns branch_abbreviation checking for collissions.
    Dungeon -> D, Depths -> U"""

    weird_abb = {"Shoals": "A", "Snake": "P", "Spider": "N", "Slime": "M",
                 "Vaults": "V", "Tomb": "W", "Depths": "U", "Abyss": "J",
                 "Pandemonium": "R"}

    weird = weird_abb.get(branch_string.split(" ")[0])
    if weird:
        return weird
    else:
        return branch_string[0]


# %% test regex
# regex = re.compile("by (.*?) \(|by (.*?)$")
# string = "Demolished by a hill giant"
# print(re.search(regex, string).groups())
# %%
