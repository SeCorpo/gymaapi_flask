import logging
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import scoped_session, sessionmaker
from database import Base

from router.authRouter import auth
from router.userRouter import user
from router.gymaRouter import gyma
from router.mineRouter import mine
from router.pubRouter import pub
from router.personRouter import person
from router.profileRouter import profile
from router.gymbroRouter import gymbro

# Initialize logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('PIL').setLevel(logging.WARNING)

# Initialize Flask application
app = Flask(__name__)

# Enable CORS middleware
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True, allow_headers=["Authorization", "Content-Type", "Gymakeys"])

# Database configuration (you can replace this with your actual DB URL)
DATABASE_URL = 'sqlite:///./test.db'  # Replace with your actual database connection string
engine = create_engine(DATABASE_URL)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# Static file serving (you can replace the directories)
app.config['UPLOAD_FOLDER_LARGE'] = './images/large'
app.config['UPLOAD_FOLDER_MEDIUM'] = './images/medium'

@app.route('/images/large/<path:filename>')
def serve_large_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER_LARGE'], filename)

@app.route('/images/medium/<path:filename>')
def serve_medium_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER_MEDIUM'], filename)

def initialize_database():
    session = SessionLocal()
    try:
        session.execute(text('SELECT 1'))
        session.commit()
        logging.info("Successfully connected to the database.")

        Base.metadata.create_all(bind=engine)
        logging.info("Database tables setup successfully.")
    except SQLAlchemyError as e:
        logging.error(f"Failed to connect or setup the database: {e}")
    finally:
        session.close()

# initialize_database()

# Root route
@app.route('/')
def root():
    return jsonify({"message": "Hello World"})

# Dynamic route example
@app.route('/hello/<name>')
def say_hello(name):
    return jsonify({"message": f"Hello {name}"})

# Including other routes (import routers)
app.register_blueprint(auth)
app.register_blueprint(user)
app.register_blueprint(gyma)
app.register_blueprint(mine)
app.register_blueprint(pub)
app.register_blueprint(person)
app.register_blueprint(profile)
app.register_blueprint(gymbro)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
