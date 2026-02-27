import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    # Session cookie: ensure it works on remote (HTTPS, different domains)
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    EVENTMOBI_API_KEY = os.environ.get('EVENTMOBI_API_KEY')
    EVENTMOBI_API_URL = os.environ.get('EVENTMOBI_API_URL') or 'https://api.eventmobi.com'
    API_KEY_EXPIRATION = timedelta(hours=1)
    EVENTMOBI_API_BASE_URL = "https://uapi.eventmobi.com"
    EVENTMOBI_API_VERSION = "3"
    LOG_FILE = 'logfile.csv'
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5055

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
