#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dotenv import load_dotenv

load_dotenv()

from flask import Flask
import json
from config import Config
from models import db
from email_service import mail
from routes import main
from database import init_database


# <<< FIX: Define the custom filter function >>>
# This function uses json.dumps to safely escape a string for use in JavaScript.
def escapejs_filter(value):
    return json.dumps(value)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # <<< FIX: Register the custom filter with Jinja2 >>>
    app.jinja_env.filters["escapejs"] = escapejs_filter

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)

    # Register blueprints
    app.register_blueprint(main)

    return app


if __name__ == "__main__":
    app = create_app()

    # Initialize database
    init_database(app)
    # In prod, run gunicorn and behind a reverse proxy
    app.run(debug=True, host="0.0.0.0")
