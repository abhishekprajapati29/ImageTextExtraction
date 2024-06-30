from flask import Blueprint
from flask import request, jsonify, session
from flask_bcrypt import Bcrypt
from flask_session import Session
from models import db, User
from app import bcrypt
auth_bp = None

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/me")
def get_current_user():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    user = User.query.filter_by(id=user_id).first()
    return jsonify({
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name
    })

@auth_bp.route("/login", methods=["POST"])
def login_user():
    email = request.json["email"]
    password = request.json["password"]

    user = User.query.filter_by(email=email).first()

    if user is None:
        return jsonify({"error": "Unauthorized"}), 401

    if not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "Unauthorized"}), 401
    
    session["user_id"] = user.id

    return jsonify({
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email
    })

@auth_bp.route("/register", methods=["POST"])
def register_user():
    email = request.json["email"]
    first_name = request.json["first_name"]
    last_name = request.json["last_name"]
    password = request.json["password"]

    user_exists = User.query.filter_by(email=email).first() is not None

    if user_exists:
        return jsonify({"error": "User already exists"}), 409

    hashed_password = bcrypt.generate_password_hash(password)
    new_user = User(first_name=first_name, last_name=last_name, email=email, password=hashed_password, )
    db.session.add(new_user)
    db.session.commit()
    
    session["user_id"] = new_user.id

    return jsonify({
        "id": new_user.id,
        "email": new_user.email,
        "first_name": new_user.first_name,
        "last_name": new_user.last_name,
    })

@auth_bp.route("/logout", methods=["POST"])
def logout_user():
    user = session.get("user_id")
    print(user)
    if session.get("user_id") is not None:
        session.pop("user_id")
        return "Logged out successfully", 200
    else:
        return "Logged out successfully", 200