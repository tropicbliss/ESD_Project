from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost:3306/groomer'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)


class Groomer(db.Model):
    __tablename__ = "groomer"

    id =  db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    picture_url = db.Column(db.String(255), nullable= False)
    capacity= db.Column(db.Integer(), nullable=False)
    address = db.Column(db.String(160), nullable=False)
    contact_no = db.Column(db.String(8), nullable=False)
    email = db.Column(db.String(), nullable=False)

    def __init__(self, name, picture_url, capacity, address, contact_no, email):
        self.name = name
        self.picture_url = picture_url
        self.capacity =capacity
        self.address = address
        self.contact_no = contact_no
        self.email = email

    def json(self):
        return {"id": self.id, "name": self.name, "picture_url": self.picture_url, "capacity":self.capacity, "address": self.address, "contact_no": self.contact_no, "email": self.email}
    
#get all groomers
@app.route("/groomer")
def get_all():
    groomerlist = Groomer.query.all()
    if len(groomerlist):
        return jsonify(
            {
                "code":200,
                "data": {
                    "groomers": [groomer.json() for groomer in groomerlist]
                }
            }
        )

    return jsonify(
        {
            "code": 404,
            "message": "No groomer exists."
        }
    ), 404


#search for groomer_place
@app.route("/groomer/<string:name>")

def get_groomer(name):
    groomer = Groomer.query.filter_by(name=name).first()
    if groomer:
        return jsonify(
            {
                "code": 200,
                "data": groomer.json()
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "No such place found."
        }
    ), 404


#create a groomer
@app.route("/groomer/<string:name>", methods=['POST'])
def create_groomer(name):
    if(Groomer.query.filter_by(name=name).first()):
            return jsonify(
             {
                "code": 400,
                "data": {
                    "name": name
                },
                "message": "Name already exists."
            }
        ), 400

    data = request.get_json()
    groomer = Groomer(name, **data)

    try:
        db.session.add(groomer)
        db.session.commit()

    except:
        return jsonify(
            {
                "code": 500,
                "data": {
                    "name": name
                },
                "message": "An error occurred creating the groomer."
            }
        ), 500


    return jsonify(
        {
            "code": 201,
            "data": groomer.json()
        }
    ), 201
    

if __name__ == '__main__':
    app.run(port=5000, debug=True)

    

















