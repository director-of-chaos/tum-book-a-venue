#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dotenv import load_dotenv
load_dotenv()
from flask import Flask
from config import Config
from models import db
from email_service import mail
from routes import main
from database import init_database

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    
    # Register blueprints
    app.register_blueprint(main)
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Initialize database
    init_database(app)
    
    app.run(debug=True, host='0.0.0.0')