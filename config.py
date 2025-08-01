from os import getenv


class Config:
    SECRET_KEY = getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OAUTHLIB_INSECURE_TRANSPORT = getenv("OAUTHLIB_INSECURE_TRANSPORT")

    # Email configuration
    MAIL_SERVER = getenv("MAIL_SERVER")
    MAIL_PORT = getenv("MAIL_PORT")
    MAIL_USE_TLS = getenv("MAIL_USE_TLS")
    MAIL_USERNAME = getenv("MAIL_USERNAME")
    MAIL_PASSWORD = getenv("MAIL_PASSWORD")
    ADMIN_EMAIL = getenv("ADMIN_EMAIL")

    # Google Calendar API configuration
    GOOGLE_CLIENT_ID = getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = getenv("GOOGLE_CLIENT_SECRET")
    REDIRECT_URI = getenv("REDIRECT_URI")
