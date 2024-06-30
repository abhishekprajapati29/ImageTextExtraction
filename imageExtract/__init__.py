from flask import Blueprint

image_extraction_bp = Blueprint('image_extraction', __name__)

from imageExtract import routes