"""
Chargement dynamique des modeles BMDB
Fonction utilitaire pour importer les modeles generes par BMDB
"""

import sys
from importlib import import_module
from .config import BMDBConfig


class ModelsLoader:
    """Gestionnaire de chargement des modeles BMDB"""
    
    _loaded = False
    _models = {}
    _base = None
    _engine = None
    _session_local = None
    
    @classmethod
    def load_models(cls, force_reload=False):
        """
        Charger les modeles BMDB generes
        
        Args:
            force_reload: Forcer le rechargement meme si dejà charge
            
        Returns:
            dict: Dictionnaire contenant {Base, engine, SessionLocal, models...}
        """
        if cls._loaded and not force_reload:
            return cls.get_all()
        
        try:
            # Valider la configuration
            BMDBConfig.validate()
            
            # Ajouter le chemin des modeles au sys.path
            models_path = BMDBConfig.get_models_path()
            project_root = str(BMDBConfig.PROJECT_ROOT)
            
            if models_path not in sys.path:
                sys.path.insert(0, models_path)
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            # Tenter d'importer les modeles
            try:
                # Methode 1: Import direct depuis le dossier generated
                models_module = import_module('models')
                print(f"✅ Modeles BMDB charges depuis: {models_path}")
                
            except ImportError:
                # Methode 2: Import avec chemin complet
                try:
                    models_module = import_module('bmdb.models.generated.models')
                    print("✅ Modeles BMDB charges (chemin complet)")
                except ImportError as e:
                    raise ImportError(
                        f"Impossible de charger les modeles BMDB.\n"
                        f"Erreur: {e}\n"
                        f"Assurez-vous d'avoir execute 'bmdb generate'"
                    )
            
            # Extraire les composants essentiels
            cls._base = getattr(models_module, 'Base', None)
            cls._engine = getattr(models_module, 'engine', None)
            cls._session_local = getattr(models_module, 'SessionLocal', None)
            
            if not cls._base or not cls._engine:
                raise ImportError("Base ou engine introuvable dans les modeles BMDB")
            
            # Charger tous les modeles (classes qui heritent de Base)
            for attr_name in dir(models_module):
                if attr_name.startswith('_'):
                    continue
                    
                attr = getattr(models_module, attr_name)
                
                # Verifier si c'est un modele SQLAlchemy
                if (hasattr(attr, '__mro__') and 
                    cls._base in attr.__mro__ and 
                    attr is not cls._base):
                    cls._models[attr_name] = attr
                    print(f"   📦 Modele charge: {attr_name}")
            
            cls._loaded = True
            
            print(f"✅ {len(cls._models)} modele(s) BMDB charge(s) avec succes")
            return cls.get_all()
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement des modeles BMDB: {e}")
            raise
    
    @classmethod
    def get_all(cls):
        """Retourner tous les composants charges"""
        if not cls._loaded:
            cls.load_models()
        
        return {
            'Base': cls._base,
            'engine': cls._engine,
            'SessionLocal': cls._session_local,
            'models': cls._models,
            **cls._models  # Ajouter les modeles directement au dictionnaire
        }
    
    @classmethod
    def get_model(cls, model_name):
        """Recuperer un modele specifique par son nom"""
        if not cls._loaded:
            cls.load_models()
        
        return cls._models.get(model_name)
    
    @classmethod
    def get_base(cls):
        """Recuperer la classe Base de SQLAlchemy"""
        if not cls._loaded:
            cls.load_models()
        return cls._base
    
    @classmethod
    def get_engine(cls):
        """Recuperer l'engine SQLAlchemy"""
        if not cls._loaded:
            cls.load_models()
        return cls._engine
    
    @classmethod
    def get_session(cls):
        """Recuperer SessionLocal"""
        if not cls._loaded:
            cls.load_models()
        return cls._session_local
    
    @classmethod
    def create_tables(cls):
        """Creer toutes les tables si elles n'existent pas"""
        if not cls._loaded:
            cls.load_models()
        
        try:
            cls._base.metadata.create_all(cls._engine)
            print("✅ Tables creees avec succes")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la creation des tables: {e}")
            return False
    
    @classmethod
    def list_models(cls):
        """Lister tous les modeles disponibles"""
        if not cls._loaded:
            cls.load_models()
        
        return list(cls._models.keys())


# Fonction publique pour faciliter l'import
def load_models(force_reload=False):
    """
    Fonction utilitaire pour charger les modeles BMDB
    
    Usage:
        from bmb import load_models
        models = load_models()
        User = models['User']
    """
    return ModelsLoader.load_models(force_reload)