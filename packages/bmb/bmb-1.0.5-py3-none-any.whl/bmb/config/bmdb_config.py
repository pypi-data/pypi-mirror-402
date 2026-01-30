"""
Configuration BMDB - Chargement des modèles et connexion DB
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class BMDBConfig:
    """Configuration pour BMDB ORM"""
    
    # Chemins des modèles BMDB
    PROJECT_ROOT = Path.cwd()
    BMDB_ROOT = PROJECT_ROOT / "bmdb"
    MODELS_DIR = BMDB_ROOT / "models" / "generated"
    
    # Configuration de la base de données (gérée par BMDB)
    # BMDB lit directement DB_CONNECTION du .env
    DB_CONNECTION = os.getenv('DB_CONNECTION')
    
    # Options de chargement des modèles
    AUTO_LOAD_MODELS = os.getenv('AUTO_LOAD_MODELS', 'True').lower() == 'true'
    CREATE_TABLES_ON_START = os.getenv('CREATE_TABLES_ON_START', 'True').lower() == 'true'
    
    @classmethod
    def validate(cls):
        """Valider la configuration BMDB"""
        if not cls.DB_CONNECTION:
            raise ValueError("DB_CONNECTION doit être défini dans .env")
        
        if not cls.MODELS_DIR.exists():
            raise FileNotFoundError(
                f"Le dossier des modèles BMDB n'existe pas: {cls.MODELS_DIR}\n"
                "Exécutez 'bmdb generate' pour créer les modèles"
            )
        
        return True
    
    @classmethod
    def get_models_path(cls):
        """Retourner le chemin complet des modèles"""
        return str(cls.MODELS_DIR)