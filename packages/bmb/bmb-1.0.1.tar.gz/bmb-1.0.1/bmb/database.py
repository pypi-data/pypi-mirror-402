"""
Gestionnaire de base de données
Fonctions utilitaires pour interagir avec BMDB
"""

from contextlib import contextmanager
from .models_loader import ModelsLoader


class Database:
    """Gestionnaire de connexion et sessions DB"""
    
    @staticmethod
    @contextmanager
    def get_session():
        """
        Context manager pour obtenir une session DB
        
        Usage:
            with Database.get_session() as session:
                users = session.query(User).all()
        """
        SessionLocal = ModelsLoader.get_session()
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    @staticmethod
    def init_db():
        """Initialiser la base de données (créer les tables)"""
        return ModelsLoader.create_tables()
    
    @staticmethod
    def test_connection():
        """Tester la connexion à la base de données"""
        try:
            engine = ModelsLoader.get_engine()
            with engine.connect() as conn:  # noqa: F841
                return True
        except Exception as e:
            print(f"❌ Erreur de connexion DB: {e}")
            return False