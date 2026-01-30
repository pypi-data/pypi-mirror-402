"""
Chargement dynamique des modèles BMDB
Fonction utilitaire pour importer les modèles générés par BMDB
"""

import sys
from importlib import import_module
from .config import BMDBConfig


class ModelsLoader:
    """Gestionnaire de chargement des modèles BMDB"""
    
    _loaded = False
    _models = {}
    _base = None
    _engine = None
    _session_local = None
    
    @classmethod
    def load_models(cls, force_reload=False):
        """
        Charger les modèles BMDB générés
        
        Args:
            force_reload: Forcer le rechargement même si déjà chargé
            
        Returns:
            dict: Dictionnaire contenant {Base, engine, SessionLocal, models...}
        """
        if cls._loaded and not force_reload:
            return cls.get_all()
        
        try:
            # Valider la configuration
            BMDBConfig.validate()
            
            # Ajouter le chemin des modèles au sys.path
            models_path = BMDBConfig.get_models_path()
            project_root = str(BMDBConfig.PROJECT_ROOT)
            
            if models_path not in sys.path:
                sys.path.insert(0, models_path)
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            # Tenter d'importer les modèles
            try:
                # Méthode 1: Import direct depuis le dossier generated
                models_module = import_module('models')
                print(f"✅ Modèles BMDB chargés depuis: {models_path}")
                
            except ImportError:
                # Méthode 2: Import avec chemin complet
                try:
                    models_module = import_module('bmdb.models.generated.models')
                    print("✅ Modèles BMDB chargés (chemin complet)")
                except ImportError as e:
                    raise ImportError(
                        f"Impossible de charger les modèles BMDB.\n"
                        f"Erreur: {e}\n"
                        f"Assurez-vous d'avoir exécuté 'bmdb generate'"
                    )
            
            # Extraire les composants essentiels
            cls._base = getattr(models_module, 'Base', None)
            cls._engine = getattr(models_module, 'engine', None)
            cls._session_local = getattr(models_module, 'SessionLocal', None)
            
            if not cls._base or not cls._engine:
                raise ImportError("Base ou engine introuvable dans les modèles BMDB")
            
            # Charger tous les modèles (classes qui héritent de Base)
            for attr_name in dir(models_module):
                if attr_name.startswith('_'):
                    continue
                    
                attr = getattr(models_module, attr_name)
                
                # Vérifier si c'est un modèle SQLAlchemy
                if (hasattr(attr, '__mro__') and 
                    cls._base in attr.__mro__ and 
                    attr is not cls._base):
                    cls._models[attr_name] = attr
                    print(f"   📦 Modèle chargé: {attr_name}")
            
            cls._loaded = True
            
            print(f"✅ {len(cls._models)} modèle(s) BMDB chargé(s) avec succès")
            return cls.get_all()
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement des modèles BMDB: {e}")
            raise
    
    @classmethod
    def get_all(cls):
        """Retourner tous les composants chargés"""
        if not cls._loaded:
            cls.load_models()
        
        return {
            'Base': cls._base,
            'engine': cls._engine,
            'SessionLocal': cls._session_local,
            'models': cls._models,
            **cls._models  # Ajouter les modèles directement au dictionnaire
        }
    
    @classmethod
    def get_model(cls, model_name):
        """Récupérer un modèle spécifique par son nom"""
        if not cls._loaded:
            cls.load_models()
        
        return cls._models.get(model_name)
    
    @classmethod
    def get_base(cls):
        """Récupérer la classe Base de SQLAlchemy"""
        if not cls._loaded:
            cls.load_models()
        return cls._base
    
    @classmethod
    def get_engine(cls):
        """Récupérer l'engine SQLAlchemy"""
        if not cls._loaded:
            cls.load_models()
        return cls._engine
    
    @classmethod
    def get_session(cls):
        """Récupérer SessionLocal"""
        if not cls._loaded:
            cls.load_models()
        return cls._session_local
    
    @classmethod
    def create_tables(cls):
        """Créer toutes les tables si elles n'existent pas"""
        if not cls._loaded:
            cls.load_models()
        
        try:
            cls._base.metadata.create_all(cls._engine)
            print("✅ Tables créées avec succès")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la création des tables: {e}")
            return False
    
    @classmethod
    def list_models(cls):
        """Lister tous les modèles disponibles"""
        if not cls._loaded:
            cls.load_models()
        
        return list(cls._models.keys())


# Fonction publique pour faciliter l'import
def load_models(force_reload=False):
    """
    Fonction utilitaire pour charger les modèles BMDB
    
    Usage:
        from bmb import load_models
        models = load_models()
        User = models['User']
    """
    return ModelsLoader.load_models(force_reload)