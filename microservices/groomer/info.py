from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from wtforms import Form, StringField, TelField , IntegerField, validators


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost:3306/groomer'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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


class RegisterForm(Form):
    name = StringField('name', [validators.Length(min=4, max=25)])
    picture_url = StringField('picture_url', validators.DataRequired, validators.length(max=255))
    email = StringField('email', [validators.Length(min=6, max=35)])
    contact_no = TelField('contact_no', [validators.DataRequired])
    address = StringField('address',[validators.DataRequired])
    capacity = IntegerField('capacity', [validators.DataRequired])

    def is_present(form, field):
        if not validators.url(field.data):
            raise validators.ValidationError('Invalid URL')


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

    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        picture_url = form.picture_url.data
        email = form.email.data
        contact_no = form.contact_no.data
        address = form.address.data
        capacity = form.capacity.data
        
        groomer = Groomer(name=name, picture_url = picture_url, email=email, contact_no=contact_no, address=address, capacity=capacity) 

        try:
            db.session.add(groomer)
            db.session.commit()
    
        except Exception as e:
            return jsonify({"message": str(e)}), 500

        return jsonify(
            {
                "code": 201,
                "data": groomer.json()
            }
        ), 201
    
    else:
        return "Error in creating groomer"



if __name__ == '__main__':
    app.run(port=5000, debug=True)

    

















