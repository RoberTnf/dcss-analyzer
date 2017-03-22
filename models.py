from application import db


class Morgue(db.Model):
    __tablename__ = "morgues"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    version = db.Column(db.String(30))
    name = db.Column(db.String(30), unique=True)
    time = db.Column(db.Integer)
    succes = db.Column(db.Boolean)
    race = db.Column(db.String(20))
    background = db.Column(db.String(20))
    XL = db.Column(db.Integer)
    Str = db.Column(db.Integer)
    Int = db.Column(db.Integer)
    Dex = db.Column(db.Integer)
    god = db.Column(db.String(20))
    faith = db.Column(db.Integer)
    branch_order = db.Column(db.string(200))
    killer = db.Column(db.String(40))


    def __init__(self, version, name, time, succes):
        self.version = version
        self.name = name
        self.time = time
        self.succes = succes


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
