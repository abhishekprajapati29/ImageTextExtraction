from flask import Flask, request, jsonify, session
from flask_bcrypt import Bcrypt
from flask_cors import CORS, cross_origin
from flask_session import Session
from config import ApplicationConfig
from models import db, User

app = Flask(__name__)
app.config.from_object(ApplicationConfig)

bcrypt = Bcrypt(app)
CORS(app, supports_credentials=True)
server_session = Session(app)
db.init_app(app)

with app.app_context():
    db.create_all()

    from auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from imageExtract import image_extraction_bp
    app.register_blueprint(image_extraction_bp, url_prefix='/api/image')


if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0')