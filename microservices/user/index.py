from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from email_validator import validate_email, EmailNotValidError
import re
import os
from ariadne import load_schema_from_path, make_executable_schema, graphql_sync, snake_case_fallback_resolvers, ObjectType
#trying to download all the functions
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


def getUser_resolver(obj, info, name):
    try:
        user = User.query.get(name)
        payload = {
            "success": True,
            "post": user.json()
        }
    except AttributeError:
        payload = {
            "success": False,
            "errors": ["User item matching {name} not found"]
        }
    return payload


class ContactNotValidError(Exception):
    pass


def create_user_resolver(obj, info, name, contact_no, email):
    try:
        normalised_email = validate_email(email)
        if not re.match(r'\b[689]\d{7}\b', contact_no):
            raise ContactNotValidError
        user = User(name, contact_no, email=normalised_email)
        db.session.add(user)
        db.session.commit()
        payload = {
            "success": True,
            "user": user.json()
        }
    except EmailNotValidError:
        payload = {
            "success": False,
            "errors": ["email is invalid"]
        }
    except ContactNotValidError:
        payload = {
            "success": False,
            "errors": ["contact_no is invalid"]
        }
    return payload


def update_user_resolver(obj, info, name, contact_no, email):
    try:
        user = User.query.get(name)
        if user:
            normalised_email = validate_email(email)
            if not re.match(r'\b[689]\d{7}\b', contact_no):
                raise ContactNotValidError
            user.contact_no = contact_no
            user.email = normalised_email
        db.session.add(user)
        db.session.commit()
        payload = {
            "success": True,
            "user": user.json()
        }
    except EmailNotValidError:
        payload = {
            "success": False,
            "errors": ["email is invalid"]
        }
    except ContactNotValidError:
        payload = {
            "success": False,
            "errors": ["contact_no is invalid"]
        }
    except AttributeError:
        payload = {
            "success": False,
            "errors": ["User item matching {name} not found"]
        }
    return payload


query = ObjectType("Query")
mutation = ObjectType("Mutation")
query.set_field("getUser", getUser_resolver)
mutation.set_field("createUser", create_user_resolver)
mutation.set_field("updateUser", update_user_resolver)

type_defs = load_schema_from_path("schema.graphql")
schema = make_executable_schema(type_defs, snake_case_fallback_resolvers)


@app.post("/graphql")
def graphql_server():
    data = request.get_json()
    success, result = graphql_sync(
        schema, data, context_value=request, debug=app.debug)
    status_code = 200 if success else 400
    return jsonify(result), status_code


if __name__ == "__main__":
    app.run(port=int(os.environ["PORT"]), debug=False)
