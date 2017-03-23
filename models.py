from application import db
import re


class Morgue(db.Model):
    __tablename__ = "morgues"
    __searchable__ = ['filename']

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    version = db.Column(db.String(30))
    name = db.Column(db.String(30))
    time = db.Column(db.Integer)
    turns = db.Column(db.Integer)
    success = db.Column(db.Boolean)
    race_combo = db.Column(db.String(40))
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

    def __init__(self, filename):
        self.version = None
        self.name = None
        self.time = None
        self.turns = None
        self.success = False
        self.race_combo = False
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
        self.filename = filename

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

        with open(filename) as f:
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

                if not self.race_combo:
                    found = re.search(race_combo_regex, line)
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

        # %% test
        XL_regex = re.compile("\d+\s+\|\s+(.+?)\s+\|")
        string = "  8420 | IceCv    | Entered an ice cave"
        #print(re.search(XL_regex, string).groups())
        # %%


class Rune(db.Model):
    __tablename__ = "runes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    morgue_id = db.Column(db.Integer, db.ForeignKey("morgues.id"))
    morgue = db.relationship("Morgue",
                             backref=db.backref("runes", lazy="dynamic"))
    rune_name = db.Column(db.String(15))

    def __init__(self, morgue, rune_name):
        self.morgue = morgue
        self.rune_name = rune_name


class Item(db.Model):
    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    morgue_id = db.Column(db.Integer, db.ForeignKey("morgues.id"))
    morgue = db.relationship("Morgue",
                             backref=db.backref("items", lazy="dynamic"))
    item_name = db.Column(db.String(150))

    def __init__(self, morgue, item_name):
        self.morgue = morgue
        self.item_name = item_name


class Mutation(db.Model):
    __tablename__ = "mutations"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    morgue_id = db.Column(db.Integer, db.ForeignKey("morgues.id"))
    morgue = db.relationship("Morgue",
                             backref=db.backref("mutations", lazy="dynamic"))
    muation_name = db.Column(db.String(40))

    def __init__(self, morgue, mutation_name):
        self.morgue = morgue
        self.mutation_name = mutation_name


class Ability(db.Model):
    __tablename__ = "abilities"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    morgue_id = db.Column(db.Integer, db.ForeignKey("morgues.id"))
    morgue = db.relationship("Morgue",
                             backref=db.backref("abilities", lazy="dynamic"))
    muation_name = db.Column(db.String(40))

    def __init__(self, morgue, ability_name):
        self.morgue = morgue
        self.ability_name = ability_name


class Skill(db.Model):
    __tablename__ = "skills"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    morgue_id = db.Column(db.Integer, db.ForeignKey("morgues.id"))
    morgue = db.relationship("Morgue",
                             backref=db.backref("skills", lazy="dynamic"))
    muation_name = db.Column(db.String(40))

    def __init__(self, morgue, skill_name, skill_level):
        self.morgue = morgue
        self.skill_name = skill_name
        self.skill_level = skill_level
