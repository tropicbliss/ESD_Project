from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost:3306/book'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Groomer(db.Model):
    __tablename__ = "groomer"
    # [{“id”: uuid, “name”: “John’s Pet Store”, “picture_url”: url, “address”: address, “contact_no”: “12345678”, “email”: “ee@gmail.com”}] 
    # (an array of pet groomer info) (if none, return an empty array [].
    id =  db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(), nullable=False)
    picture_url = db.Column(db.String(255), nullable= True)
    address = db.Column(db.String())
    contact_no = db.Column(db.String(8))
    email = db.Column(db.String())

    def __init__(self, id, picture_url, address, contact_no, email):
        self.id = id
        self.picture_url = picture_url
        self.address = address
        self.contact_no = contact_no
        self.email = email

    def json(self):
        return {"id": self.id, "picture": self.picture_url, "address": self.address, "contact_no": self.contact_no, "email": self.email}
    

















