from flask import Flask, request, jsonify, render_template, redirect, url_for, g
from flask_sqlalchemy import SQLAlchemy
import os
import string_validator
from flask_expects_json import expects_json


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+mysqlconnector://root:PG6k20YjR5mrPFCSfJ8b@containers-us-west-97.railway.app:7626/railway"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Groomer(db.Model):
    __tablename__ = "groomer"

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    picture_url = db.Column(db.String(255), nullable=False)
    capacity = db.Column(db.Integer(), nullable=False)
    address = db.Column(db.String(160), nullable=False)
    contact_no = db.Column(db.String(11), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    pet_types = db.relationship("AcceptedPets", backref="groomer", lazy=True)

    def __init__(self, name, picture_url, capacity, address, contact_no, email):
        self.id = string_validator.create_cuid()
        self.name = name
        self.picture_url = picture_url
        self.capacity = capacity
        self.address = address
        self.contact_no = contact_no
        self.email = email

    def json(self):
        return {"id": self.id, "name": self.name, "picture_url": self.picture_url, "capacity": self.capacity, "address": self.address, "contact_no": self.contact_no, "email": self.email}


class AcceptedPets(db.Model):
    __tablename__ = "acceptedpets"

    id: db.Column(db.String(50), primary_key=True)
    groomer_id: db.Column(db.String(50), db.ForeignKey(
        "groomer.id"), nullable=False)
    pet_type: db.Column(db.String(50), nullable=False)

    def __init__(self, groomer_id, pet_type):
        self.id = string_validator.create_cuid()
        self.groomer_id = groomer_id
        self.pet_type = pet_type

    def json(self):
        return {
            "id": self.id,
            "groomer_id": self.groomer_id,
            "pet_type": self.pet_type
        }


def validate_data(picture_url, email, phone_no):
    if picture_url:
        valid_picture_url = string_validator.validate_url(picture_url)
        if not valid_picture_url:
            return False
    if email:
        valid_email = string_validator.validate_email(email)
        if not valid_email:
            return False
    if phone_no:
        valid_phone = string_validator.validate_phone(phone_no)
        if not valid_phone:
            return False
    return True


create_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "picture_url": {"type": "string"},
        "capacity": {"type": "number", "minimum": 1},
        "address": {"type": "string"},
        "contact_no": {"type": "string"},
        "email": {"type": "string"},
        "pet_types": {"type": "array", "items": {
            "type": "string"
        }, "minItems": 1},
    },
    "required": ["name", "picture_url", "capacity", "address", "contact_no", "email", "pet_types"]
}


@app.post("/create")
@expects_json(create_schema)
def create_groomer():
    data = g.data
    if not validate_data(data["picture_url"], data["email"], data["contact_no"]):
        return jsonify({
            "message": "data provided is invalid"
        }), 400
    pet_types = data.pop("pet_types")
    groomer = Groomer(**data)
    pet_type_data = list()
    for pet_type in pet_types:
        pet_data = AcceptedPets(groomer.id, pet_type)
        pet_type_data.append(pet_data)
    try:
        db.session.add(groomer)
        db.session.add_all(pet_type_data)
        db.session.commit()
    except:
        return jsonify({
            "message": "internal server error"
        }), 400
    return jsonify({
        "id": groomer.id
    }), 200


get_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "picture_url": {"type": "string"},
        "capacity": {"type": "number", "minimum": 1},
        "address": {"type": "string"},
        "contact_no": {"type": "string"},
        "email": {"type": "string"},
        "pet_types": {"type": "array", "items": {
            "type": "string"
        }, "minItems": 1},
    },
    "required": []
}


@app.post("/read")
@expects_json(get_schema)
def get_groomer():
    data = g.data
    res = Groomer.query.filter_by(**data)
    return jsonify([r.json() for r in res]), 200


@app.get("/search/keyword/<string:keyword>")
def search_groomer_by_name(keyword):
    res = Groomer.query.filter(Groomer.name.contains(keyword))
    return jsonify([r.json() for r in res]), 200


@app.get("/search/id/<string:id>")
def search_groomer_by_id(id):
    res = Groomer.query.filter_by(id=id).first()
    return jsonify(res.json()), 200


update_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "picture_url": {"type": "string"},
        "capacity": {"type": "number", "minimum": 1},
        "address": {"type": "string"},
        "contact_no": {"type": "string"},
        "email": {"type": "string"},
        "pet_types": {"type": "array", "items": {
            "type": "string"
        }, "minItems": 1},
    },
    "required": []
}


@app.post("/update/<string:id>")
@expects_json(update_schema)
def update_groomer(id):
    data = g.data
    pet_types = None
    if not validate_data(data.get("picture_url"), data.get("email"), data.get("contact_no")):
        return jsonify({
            "message": "data provided is invalid"
        }), 400
    try:
        pet_types = data.pop("pet_types")
    except KeyError:
        pass
    groomer = Groomer.query.filter_by(id=id).first()
    if groomer:
        if data.get("address"):
            groomer.address = data["address"]
        if data.get("capacity"):
            groomer.capacity = data["capacity"]
        if data.get("contact_no"):
            groomer.contact_no = data["contact_no"]
        if data.get("email"):
            groomer.email = data["email"]
        if data.get("name"):
            groomer.name = data["name"]
        if data.get("picture_url"):
            groomer.picture_url = data["picture_url"]
        if pet_types:
            groomer.pet_types = pet_types
        db.session.commit()
        return jsonify(groomer.json()), 200
    return jsonify({
        "message": "groomer not found"
    }), 404


accepts_schema = {
    "type": "object",
    "properties": {
        "pet_types": {"type": "array", "items": {
            "type": "string"
        }, "minItems": 1},
    },
    "required": []
}


@app.post("/accepts/<string:id>")
@expects_json(accepts_schema)
def does_groomer_accept_pet(id):
    data = g.data
    groomer = Groomer.query.filter_by(id=id).first()
    if groomer:
        if all([pet_type in groomer.pet_types for pet_type in data["pet_types"]]):
            return jsonify({
                "message": "all pets accepted"
            }), 200
        else:
            return jsonify({
                "message": "pet type not accepted"
            }), 400
    return jsonify({
        "message": "groomer not found"
    }), 404


if __name__ == '__main__':
    app.run(port=int(5000), debug=True)
