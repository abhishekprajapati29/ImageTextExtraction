from flask import Flask, request, jsonify, session
from flask_bcrypt import Bcrypt
from flask_cors import CORS, cross_origin
from flask_session import Session
from config import ApplicationConfig
from google.cloud import vision
from flask import request, jsonify, current_app, session
from flask_bcrypt import Bcrypt
from flask_session import Session
from models import db, Image, User
import base64
from sqlalchemy import func
from datetime import datetime, timedelta

app = Flask(__name__)
app.config.from_object(ApplicationConfig)

bcrypt = Bcrypt(app)
CORS(app, supports_credentials=True)
server_session = Session(app)
db.init_app(app)

with app.app_context():
    db.create_all()

    @app.route("/api/auth/me")
    def get_current_user():
        user_id = session.get("user_id")

        if not user_id:
            return jsonify({"message": "Unauthorized"})
        
        user = User.query.filter_by(id=user_id).first()
        return jsonify({
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name
        })

    @app.route("/api/auth/login", methods=["POST"])
    def login_user():
        email = request.json["email"]
        password = request.json["password"]

        user = User.query.filter_by(email=email).first()

        if user is None:
            return jsonify({"error": "Invalid credentials"}), 401

        if not bcrypt.check_password_hash(user.password, password):
            return jsonify({"error": "Invalid credentials"}), 401
        
        session["user_id"] = user.id

        return jsonify({
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email
        })

    @app.route("/api/auth/register", methods=["POST"])
    def register_user():
        email = request.json["email"]
        first_name = request.json["first_name"]
        last_name = request.json["last_name"]
        password = request.json["password"]

        user_exists = User.query.filter_by(email=email).first() is not None

        if user_exists:
            return jsonify({"message": "User already exists"}), 409

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

    @app.route("/api/auth/logout", methods=["POST"])
    def logout_user():
        user = session.get("user_id")
        print(user)
        if session.get("user_id") is not None:
            session.pop("user_id")
            return "Logged out successfully", 200
        else:
            return "Logged out successfully", 200

    @app.route("/api/image/<id>", methods=["GET"])
    def get_user_by_id(id):
        image = Image.query.filter_by(id=id).first()

        if not image:
            return jsonify({"message": "User not found"}), 404
        
        return jsonify({
            "id": image.id,
            "image": image.image,
            "texts": image.texts,
            "word_count": image.word_count,
            "user_id": image.user_id,
            "size": image.size,
            "name": image.name,
            "type": image.type,
        })

    @app.route("/api/image/all", methods=["GET"])
    def get_all_images():
        user_id = session.get("user_id")
        images = Image.query.filter_by(user_id=user_id).all()

        if not images:
            return jsonify([])
        
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        last_week = today - timedelta(weeks=1)
        last_month = today - timedelta(days=30)  # Approximate, adjust as needed

        # Count images for each time period
        counts_today = db.session.query(func.count(Image.id)).filter(Image.created_on >= today).scalar()
        counts_yesterday = db.session.query(func.count(Image.id)).filter(Image.created_on >= yesterday, Image.created_on < today).scalar()
        counts_last_week = db.session.query(func.count(Image.id)).filter(Image.created_on >= last_week, Image.created_on < today).scalar()
        counts_last_month = db.session.query(func.count(Image.id)).filter(Image.created_on >= last_month, Image.created_on < today).scalar()

        image_list = []
        for image in images:
            image_list.append({
                "id": image.id,
                "image": image.image,
                "texts": image.texts,
                "word_count": image.word_count,
                "user_id": image.user_id,
                "size": image.size,
                "name": image.name,
                "type": image.type,
            })
        

        return jsonify({
            "image_list": image_list, 
            "counts": {
                "today": counts_today,
                "yesterday": counts_yesterday,
                "last_week": counts_last_week,
                "last_month": counts_last_month
            }})

    @app.route('/api/image/extract', methods=['POST'])
    def upload_image():
        image_data = request.files.get('image')
        print(image_data.content_length)
        
        user_id = session.get("user_id")

        if not user_id:
            return jsonify({"message": "Unauthorized"}), 401
        
        if image_data:
            # Read the image content
            image_content = image_data.read()
            image_base64 = base64.b64encode(image_content).decode('utf-8')

            # Create a Vision client object
            vision_client = vision.ImageAnnotatorClient()

            # Construct the image object from the content
            image = vision.Image(content=image_content)

            # Send the image and features to the Vision API
            response = vision_client.text_detection(image=image)
            extracted_info = response.text_annotations[0]
            extracted_text = " ".join(extracted_info.description.split('\n'))
            
            word_count = len(extracted_text.split(" "))
            
            
            print(image_data)
            
            new_image = Image(
                image=image_base64,
                texts=extracted_text,
                word_count=word_count,
                user_id=user_id,
                name=image_data.filename,
                type=image_data.content_type.split('/').pop(),
                size=image_data.content_length
            )
            db.session.add(new_image)
            db.session.commit()
            
            return jsonify({
                "id": new_image.id,
                "image": image_base64,
                "texts": extracted_text,
                "word_count": word_count,
                "user_id": user_id,
                "size": image_data.content_length,
                "name": image_data.filename,
                "type": image_data.content_type
            })
                    
        else:
            return jsonify({"message": "No image file provided"}), 400
        


if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0')