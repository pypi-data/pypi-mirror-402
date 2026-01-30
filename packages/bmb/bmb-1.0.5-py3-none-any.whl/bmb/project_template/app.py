"""
Factory pour créer l'application Flask BMB
"""

from flask import Flask
from flask_cors import CORS

from config import AppConfig, BMDBConfig
from models_loader import load_models
from database import Database
from middleware import setup_logging, register_error_handlers


def create_app(config_class=AppConfig):
    """
    Factory pour créer l'application BMB
    
    Args:
        config_class: Classe de configuration à utiliser
        
    Returns:
        Flask app configurée
    """
    
    # Créer l'application Flask
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Valider les configurations
    print("🔧 Validation des configurations...")
    AppConfig.validate()
    BMDBConfig.validate()
    
    # Configurer CORS
    CORS(app, origins=AppConfig.CORS_ORIGINS)
    
    # Charger les modèles BMDB
    print("📦 Chargement des modèles BMDB...")
    models = load_models()
    
    # Stocker les modèles dans l'app context
    app.bmdb_models = models
    
    # Initialiser la base de données
    if BMDBConfig.CREATE_TABLES_ON_START:
        print("🗄️  Initialisation de la base de données...")
        Database.init_db()
    
    # Tester la connexion
    if Database.test_connection():
        print("✅ Connexion à la base de données établie")
    else:
        print("⚠️  Attention: Impossible de se connecter à la base de données")
    
    # Configurer le logging
    setup_logging(app)
    
    # Enregistrer les gestionnaires d'erreurs
    register_error_handlers(app)
    
    # Enregistrer les blueprints (routes)
    from routes import register_routes
    register_routes(app)
    
    print("✅ Application BMB créée avec succès")
    
    return app