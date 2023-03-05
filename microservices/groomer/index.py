from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import cuid
import os


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ("DB_URI")
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
        self.id = cuid.cuid()
        self.name = name
        self.picture_url = picture_url
        self.capacity = capacity
        self.address = address
        self.contact_no = contact_no
        self.email = email

    def json(self):
        return {"id": self.id, "name": self.name, "picture_url": self.picture_url, "capacity": self.capacity, "address": self.address, "contact_no": self.contact_no, "email": self.email}


class AcceptedPets:
    id: db.Column(db.String(50), primary_key=True)
    groomer_id: db.Column(db.String(50), db.ForeignKey(
        "groomer.id"), nullable=False)
    pet_type: db.Column(db.String(50), nullable=False)

    def __init__(self, groomer_id, pet_type):
        self.id = cuid.cuid()
        self.groomer_id = groomer_id
        self.pet_type = pet_type

    def json(self):
        return {
            "id": self.id,
            "groomer_id": self.groomer_id,
            "pet_type": self.pet_type
        }


@app.post("/create")
def create_groomer():
    data = request.json()
    try:
        pet_types = data.pop("pet_types")
        # I hate Python so much
        if type(pet_types) is not list:
            raise KeyError
    except KeyError:
        return jsonify({
            "message": "pet_types not specified"
        }), 400
    # do data validation stuff
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


@app.post("/read")
def get_groomer():
    data = request.json()
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


class ApiException(Exception):
    pass


@app.post("/update/<string:id>")
def update_groomer(id):
    data = request.json()
    pet_types = None
    try:
        pet_types = data.pop("pet_types")
        if type(pet_types) is not list:
            raise ApiException
    except KeyError:
        pass
    except ApiException:
        return jsonify({
            "message": "pet_types not specified"
        }), 400
    groomer = Groomer.query.filter_by(id=id).first()
    if groomer:
        if data["address"]:
            groomer.address = data["address"]
        if data["capacity"]:
            groomer.capacity = data["capacity"]
        if data["contact_no"]:
            groomer.contact_no = data["contact_no"]
        if data["email"]:
            groomer.email = data["email"]
        if data["name"]:
            groomer.name = data["name"]
        if data["picture_url"]:
            groomer.picture_url = data["picture_url"]
        if pet_types:
            groomer.pet_types = pet_types
        db.session.commit()
        return jsonify(groomer.json()), 200
    return jsonify({
        "message": "groomer not found"
    }), 404


@app.post("/accepts/<string:id>")
def does_groomer_accept_pet(id):
    data = request.json()
    groomer = Groomer.query.filter_by(id=id).first()
    if groomer:
        if data["pet_types"]:
            if all([pet_type in groomer.pet_types for pet_type in data["pet_types"]]):
                return jsonify({
                    "message": "all pets accepted"
                }), 200
            else:
                return jsonify({
                    "message": "pet type not accepted"
                }), 400
        else:
            return jsonify({
                "message": "pet_types not specified"
            }), 400
    return jsonify({
        "message": "groomer not found"
    }), 404


if __name__ == '__main__':
    app.run(port=int(os.environ("PORT")), debug=True)
