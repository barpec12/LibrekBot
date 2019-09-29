from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Recipient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_class = db.Column(db.String(2), primary_key=True)


class SentAnnouncement(db.Model):
    unique_id = db.Column(db.String(40), primary_key=True)
    checksum = db.Column(db.String(43), unique=True, nullable=False)
