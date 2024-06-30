from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, Text, Integer, DateTime
from uuid import uuid4
from datetime import datetime

db = SQLAlchemy()

def get_uuid():
    return uuid4().hex

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(String(32), primary_key=True, unique=True, default=get_uuid)
    first_name = db.Column(String(345))
    last_name = db.Column(String(345))
    email = db.Column(String(345), unique=True)
    password = db.Column(Text, nullable=False)

class Image(db.Model):
    __tablename__ = "image"
    id = db.Column(String(32), primary_key=True, unique=True, default=get_uuid)
    name = db.Column(Text, nullable=False)
    image = db.Column(Text, nullable=False)
    texts = db.Column(Text, nullable=False)
    size = db.Column(Integer, nullable=False)
    type = db.Column(String, nullable=False)
    word_count = db.Column(Text, nullable=False)
    created_on = db.Column(DateTime, default=datetime.now)
    user_id = db.Column(String(32), db.ForeignKey('users.id'))