from flask import Flask, request, jsonify
from sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqlconnector://root:toeFtmC4PkZmoeEEEGBU@containers-us-west-171.railway.app:6682/railway"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


@app.post("/create")
def create_new_user():
    pass
