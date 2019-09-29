from librekbot import db


class Recipient(db.Model):
    fb_id = db.Column(db.BigInteger, unique=True, primary_key=True)
    student_class = db.Column(db.String(2), primary_key=True)


class SentAnnouncement(db.Model):
    unique_id = db.Column(db.String(40), unique=True, primary_key=True)
    checksum = db.Column(db.String(43), unique=True, nullable=False)
