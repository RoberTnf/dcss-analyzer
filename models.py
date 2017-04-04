import re
from datetime import date
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy import ForeignKey, Text, Date, Float
from sqlalchemy.orm import relationship, backref
from database import Base, db_session


class Morgue(Base):
    """Main class of the  Holds most information about the run"""

    __tablename__ = "morgues"
    __searchable__ = ["filename", "name", "success", "version", "god", "runes"]

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
    killer = Column(String(40))
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
        faith_regex = re.compile("(\w+) \[(\**)")
        SH_regex = re.compile("SH.+?(\d+).+?Dex.+?(\d+)")
        killer_regex = re.compile("by (.*?) \(")
        quit_regex = re.compile("Quit the game")
        anih_regex = re.compile("\w+ by (.+?)\n")
        pois_regex = re.compile("Succumbed to (.*?)\n")
        suicide_regex = re.compile("Killed themself")
        branch_regex = re.compile("\d+\s+\|\s+(.+?)\s+\|")
        date_regex = re.compile(".*?-(\d\d\d\d)(\d\d)(\d\d)-")
        skill_regex = re.compile("...Level (\d+\.?\d?).*? (.+)\n")
        rune_regex = re.compile("(\d+)/15 runes:")
        spell_regex = re.compile("\w - (.*?)  \s*.+?#|\w - (.*?)  \s*.+?N/A")

        with open(filename) as f:
            d = [int(i) for i in re.search(date_regex, filename).groups()]
            self.date = date(*d)

            for line in f.readlines():
                if not self.version:
                    found = re.search(version_regex, line)
                    if found:
                        self.version = found.group(1)
                        if "Sprint" in line:
                            self.crawl = False
                            break

                if not self.name:
                    found = re.search(killer_regex, line)
                    found2 = re.search(anih_regex, line)
                    found3 = re.search(pois_regex, line)
                    found4 = re.search(suicide_regex, line)
                    if found:
                        self.killer = found.group(1)
                    found = re.search(name_regex, line)
                    if found:
                        self.name = found.group(2)

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
                        # TODO: Get this shit finding shit
                        race_string, background_string =\
                            race_background(found.group(1))
                        self.race = Race_abbreviation.query.filter_by(
                            string=race_string).first()
                        if not self.race:
                            self.race = Race_abbreviation(race_string)
                            db_session.add(self.race)
                        self.background = BG_abbreviation.query\
                            .filter_by(string=background_string).first()
                        if not self.background:
                            self.background = BG_abbreviation(
                                background_string)
                            db_session.add(self.background)

                if not self.XL:
                    found = re.search(XL_regex, line)
                    if found:
                        self.AC, self.Str, self.XL = found.groups()

                if not self.EV:
                    found = re.search(EV_regex, line)
                    if found:
                        self.EV, self.Int, god = found.groups()
                        if "Gozag" in god:
                            self.god = "Gozag"
                        elif "Xom" in god:
                            self.god = "Xom"
                        elif god.strip() != "":
                            found = re.search(faith_regex, god)
                            self.god = found.groups()[0]
                            self.faith = len(found.groups()[1])

                if not self.SH:
                    found = re.search(SH_regex, line)
                    if found:
                        self.SH, self.Dex = found.groups()

                if not self.killer:
                    found = re.search(killer_regex, line)
                    found2 = re.search(anih_regex, line)
                    found3 = re.search(pois_regex, line)
                    found4 = re.search(suicide_regex, line)
                    if found:
                        self.killer = found.group(1)
                    elif found2:
                        self.killer = found2.group(1)
                    elif re.search(quit_regex, line):
                        self.killer = "quit"
                    elif self.success:
                        self.killer = "won"
                    elif found3:
                        self.killer = found3.group(1)
                    elif found4:
                        self.killer = "suicide"

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
                            branch_order_list[-1] = self.branch_order.split("-")[0] + "-" + floor.strip()
                            self.branch_order = " ".join(branch_order_list) + " "
                    else:
                        self.branch_order += "{}{}-{} ".format(branch.strip(), floor.strip(), floor.strip())
                else:
                    self.branch_order = "{}{}-{} ".format(branch.strip(), floor.strip(), floor.strip())


# %% test regex
# regex = re.compile("lasted (\d*).*?(\d\d:\d\d:\d\d) \((\d+)")
# string = "             The game lasted 00:02:17 (1841 turns)."
# print(re.search(regex, string).groups())
# %%


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
        self.abbreviation = get_abbreviation(string)
        self.string = string

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
        self.abbreviation = get_abbreviation(string)
        self.string = string

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
    elif len(string.split(" ")) == 1:
        abbreviation = string[:2]
    else:
        abbreviation = string.split(" ")[0][0] + string.split(" ")[1][0]

    return abbreviation


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
