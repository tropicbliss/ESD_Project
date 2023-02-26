from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from email_validator import validate_email, EmailNotValidError
import re
import os
from ariadne import load_schema_from_path, make_executable_schema, graphql_sync, snake_case_fallback_resolvers, ObjectType

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URI"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = "user"

    name = db.Column(db.String(64), primary_key=True)
    contact_no = db.Column(db.String(8), nullable=False)
    email = db.Column(db.String(64), nullable=False)

    def json(self):
        return {
            "name": self.name,
            "contact_no": self.contact_no,
            "email": self.email
        }


db.create_all()

type_defs = load_schema_from_path("schema.graphql")
schema = make_executable_schema(type_defs, snake_case_fallback_resolvers)


@app.post("/graphql")
def graphql_server():
    data = request.get_json()
    success, result = graphql_sync(schema)


@app.post("/create")
def create_new_user():
    data = request.get_json()
    user = User(**data)
    try:
        v = validate_email(user.email)
        user.email = v["email"]
    except EmailNotValidError:
        return jsonify({
            "message": "email is invalid"
        }), 400
    if not re.match(r'\b[689]\d{7}\b', user.contact_no):
        return jsonify({
            "message": "contact_no is invalid"
        }), 400
    if User.query.filter_by(name=user.name).first():
        return jsonify({
            "message": "name already exists"
        }), 400
    try:
        db.session.add(user)
        db.session.commit()
    except:
        return jsonify({
            "message": "An internal server error occurred"
        }), 500
    return jsonify({
        "data": user.json()
    }), 201


@app.get("/read/<string:name>")
def get_user(name):
    user = User.query.filter_by(name=name).first()
    if user:
        return jsonify({
            "data": user.json()
        })
    return jsonify({
        "message": "User not found"
    }), 404


@app.post("/update")
def update_user_data():
    try:
        data = request.get_json()
        user = User.query.filter_by(name=data["name"]).first()
        if not user:
            return jsonify({
                "message": "User not found"
            }), 404
        try:
            v = validate_email(data["email"])
            user.email = v["email"]
        except EmailNotValidError:
            return jsonify({
                "message": "email is invalid"
            }), 400
        if not re.match(r'\b[689]\d{7}\b', data["contact_no"]):
            return jsonify({
                "message": "contact_no is invalid"
            }), 400
        user.contact_no = data["contact_no"]
        db.session.commit()
        return jsonify(
            {
                "data": user.json()
            }
        )
    except:
        return jsonify({
            "message": "An internal server error occurred"
        }), 500


if __name__ == "__main__":
    app.run(port=int(os.environ["PORT"]), debug=False)
