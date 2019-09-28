from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Recipient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    grade = db.Column(db.String(2), primary_key=True)


class SentAnnouncement(db.Model):
    id = db.Column(db.String(40), primary_key=True)
    checksum = db.Column(db.String(40), unique=True, nullable=False)
