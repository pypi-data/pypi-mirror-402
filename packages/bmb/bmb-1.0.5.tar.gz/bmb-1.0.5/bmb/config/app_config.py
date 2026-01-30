"""
Configuration de l'application Flask
Séparée de la configuration BMDB
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class AppConfig:
    """Configuration Flask - JWT, CORS, etc."""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_ENV', 'production') == 'development'
    TESTING = os.getenv('TESTING', 'False').lower() == 'true'
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET', SECRET_KEY)
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', 24))
    JWT_EXPIRATION_DELTA = timedelta(hours=JWT_EXPIRATION_HOURS)
    JWT_ALGORITHM = 'HS256'
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization']
    
    # Server Configuration
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # Pagination
    DEFAULT_PAGE_SIZE = int(os.getenv('DEFAULT_PAGE_SIZE', 20))
    MAX_PAGE_SIZE = int(os.getenv('MAX_PAGE_SIZE', 100))
    
    # Upload Configuration (si nécessaire)
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    
    @classmethod
    def validate(cls):
        """Valider la configuration"""
        if cls.SECRET_KEY == 'dev-secret-key-change-in-production' and not cls.DEBUG:
            raise ValueError("SECRET_KEY doit être défini en production!")
        
        if cls.JWT_SECRET_KEY == cls.SECRET_KEY and not cls.DEBUG:
            print("⚠️  Attention: JWT_SECRET devrait être différent de SECRET_KEY")
        
        return True
