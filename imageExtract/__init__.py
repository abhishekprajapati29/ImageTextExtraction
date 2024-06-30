from flask import Blueprint
from google.cloud import vision
from flask import request, jsonify, current_app, session
from flask_bcrypt import Bcrypt
from flask_session import Session
from models import db, Image
import base64
from sqlalchemy import func
from datetime import datetime, timedelta

image_extraction_bp = Blueprint('image_extraction', __name__)

@image_extraction_bp.route("/<id>", methods=["GET"])
def get_user_by_id(id):
    image = Image.query.filter_by(id=id).first()

    if not image:
        return jsonify({"error": "User not found"}), 404
    
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

@image_extraction_bp.route("/all", methods=["GET"])
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

@image_extraction_bp.route('/extract', methods=['POST'])
def upload_image():
    image_data = request.files.get('image')
    print(image_data.content_length)
    
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    if image_data:
        # Read the image content
        image_content = image_data.read()
        image_base64 = base64.b64encode(image_content).decode('utf-8')

        # # Create a Vision client object
        # vision_client = vision.ImageAnnotatorClient()

        # # Construct the image object from the content
        # image = vision.Image(content=image_content)

        # # Send the image and features to the Vision API
        # response = vision_client.text_detection(image=image)
        
        ocr_result = [
            # First item is an empty dictionary
            {},
            # Subsequent items with 'description' keys
            {
                "description": "testing\nasdf"
            },
            {
                "description": "testing\nasdf"
            }
        ]
        
        extracted_text = " ".join([item['description'].replace("\n", " ") for item in ocr_result if 'description' in item])
        
        # texts = [item['description'].replace("\n", " ") for item in response.text_annotations if 'description' in item]
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
        return jsonify({"error": "No image file provided"}), 400
    