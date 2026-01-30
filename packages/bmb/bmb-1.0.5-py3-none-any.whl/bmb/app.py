"""
Factory pour creer l'application Flask BMB
"""

from flask import Flask
from flask_cors import CORS

from .config import AppConfig, BMDBConfig
from .models_loader import load_models
from .database import Database
from .middleware import setup_logging, register_error_handlers


def create_app(config_class=AppConfig):
    """
    Factory pour creer l'application BMB
    
    Args:
        config_class: Classe de configuration a utiliser
        
    Returns:
        Flask app configuree
    """
    
    # Creer l'application Flask
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Valider les configurations
    print("🔧 Validation des configurations...")
    AppConfig.validate()
    BMDBConfig.validate()
    
    # Configurer CORS
    CORS(app, origins=AppConfig.CORS_ORIGINS)
    
    # Charger les modeles BMDB
    print("📦 Chargement des modeles BMDB...")
    models = load_models()
    
    # Stocker les modeles dans l'app context
    app.bmdb_models = models
    
    # Initialiser la base de donnees
    if BMDBConfig.CREATE_TABLES_ON_START:
        print("🗄️  Initialisation de la base de donnees...")
        Database.init_db()
    
    # Tester la connexion
    if Database.test_connection():
        print("✅ Connexion a la base de donnees etablie")
    else:
        print("⚠️  Attention: Impossible de se connecter a la base de donnees")
    
    # Configurer le logging
    setup_logging(app)
    
    # Enregistrer les gestionnaires d'erreurs
    register_error_handlers(app)
    
    # Enregistrer les blueprints (routes)
    from .routes import register_routes
    register_routes(app)
    
    print("✅ Application BMB creee avec succes")
    
    return app