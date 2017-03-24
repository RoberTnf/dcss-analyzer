from application import db
import re
from datetime import date


class Morgue(db.Model):
    """Main class of the DB. Holds most information about the run"""

    __tablename__ = "morgues"
    __searchable__ = ["filename", "name", "success"]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    version = db.Column(db.String(30))
    name = db.Column(db.String(30))
    time = db.Column(db.Integer)
    turns = db.Column(db.Integer)
    success = db.Column(db.Boolean)
    race = db.Column(db.String(40))
    background = db.Column(db.String(40))
    XL = db.Column(db.Integer)
    Str = db.Column(db.Integer)
    AC = db.Column(db.Integer)
    Int = db.Column(db.Integer)
    EV = db.Column(db.Integer)
    Dex = db.Column(db.Integer)
    SH = db.Column(db.Integer)
    god = db.Column(db.String(20))
    faith = db.Column(db.Integer)
    branch_order = db.Column(db.Text)
    killer = db.Column(db.String(40))
    filename = db.Column(db.String(200))
    date = db.Column(db.Date)
    runes = db.Column(db.Integer)

    def __init__(self, filename):
        self.version = None
        self.name = None
        self.time = None
        self.turns = None
        self.success = False
        self.race = False
        self.background = False
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

        version_regex = re.compile("version ([0-9A-Za-z\.\-]+)")
        name_regex = re.compile("(\d+ )(\w+)( the)")
        time_regex = re.compile("lasted (\d\d:\d\d:\d\d) \((\d+)")
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
                        self.time = found.group(1)
                        self.turns = found.group(2)

                if not self.success:
                    found = re.search(success_regex, line)
                    if found:
                        self.success = True

                if not self.race:
                    found = re.search(race_combo_regex, line)
                    if found:
                        self.race, self.background = \
                            race_background(found.group(1))

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
                    if branch.find(":") >= 0:
                        branch = branch.split(":")
                        branch = branch[0][0] + branch[1]
                    if branch not in self.branch_order and \
                            branch[0][0].isalpha():
                        self.branch_order += branch+" "

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
                    db.session.add(skill)

                # check for spells
                found = re.match(spell_regex, line)
                if found:
                    if found.group(1):
                        spell = Spell(self, found.group(1))
                    else:
                        spell = Spell(self, found.group(2))
                    db.session.add(spell)

                found = re.match(ability_regex, line)
                if found:
                    skill = Skill(self, found.group(1))
                    db.session.add(skill)

# %% test regex
regex = re.compile("\w - (.*?)  \s*.+?#|\w - (.*?)  \s*.+?N/A")
string = ""
print(re.match(regex, string).groups())
# %%


class Skill(db.Model):
    """Stores learned skills, backrefs to morgue"""
    __tablename__ = "skills"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    morgue_id = db.Column(db.Integer, db.ForeignKey("morgues.id"))
    morgue = db.relationship("Morgue",
                             backref=db.backref("skills", lazy="dynamic"))
    skill_name = db.Column(db.String(40))
    skill_level = db.Column(db.Float)

    def __init__(self, morgue, skill_name, skill_level):
        self.morgue = morgue
        self.skill_name = skill_name
        self.skill_level = skill_level


class Spell(db.Model):
    """Stores learned spells, backrefs to morgue"""
    __tablename__ = "spells"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    morgue_id = db.Column(db.Integer, db.ForeignKey("morgues.id"))
    morgue = db.relationship("Morgue",
                             backref=db.backref("spells", lazy="dynamic"))
    spell_name = db.Column(db.String(40))

    def __init__(self, morgue, spell_name):
        self.morgue = morgue
        self.spell_name = spell_name


def race_background(race_combo):
    """Given string consisting of race/background combo, separates it in
    the correct race | background.

    Examples:
    "Spriggan enchanter" -> "Spriggan", "enchanter"
    "Gargoyle Earth Elementalist" -> "Gargoyle", "Earth Elementalist" """

    # list of all the races consisting of 2 words, might change
    two_word_races = ["Hill Orc", "Deep Elf", "Deep Dwarf", "Vine Stalker"]

    # separate line into a list of words
    words = race_combo.split()

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
