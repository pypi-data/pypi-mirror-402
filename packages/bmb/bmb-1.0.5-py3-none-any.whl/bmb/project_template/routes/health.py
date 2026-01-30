"""
Routes de santé et monitoring
"""

from flask import Blueprint
import datetime

from database import Database
from models_loader import ModelsLoader
from utils import success_response, error_response
from config.bmdb_config import BMDBConfig

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Vérifier l'état de l'API et de la base de données
    Teste la connexion BMDB
    """
    try:
        # Tester la connexion DB
        db_connected = Database.test_connection()
        
        # Informations sur les modèles chargés
        models_list = ModelsLoader.list_models()
        
        # Test de requête simple
        models = ModelsLoader.get_all()
        User = models.get('User')
        
        try:
            user_count = User.count() if User else 0
            db_query_ok = True
        except Exception:
            user_count = 0
            db_query_ok = False
        
        health_status = {
            'status': 'healthy' if db_connected and db_query_ok else 'unhealthy',
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'components': {
                'database': {
                    'status': 'connected' if db_connected else 'disconnected',
                    'orm': 'BMDB'
                },
                'models': {
                    'loaded': len(models_list),
                    'list': models_list
                },
                'api': {
                    'status': 'running'
                }
            },
            'metrics': {
                'total_users': user_count
            }
        }
        
        status_code = 200 if health_status['status'] == 'healthy' else 503
        
        return success_response(
            data=health_status,
            status=status_code
        )
        
    except Exception as e:
        return error_response(
            message="Health check failed",
            status=503,
            errors={'details': str(e)}
        )


@health_bp.route('/info', methods=['GET'])
def app_info():
    """Informations sur l'application"""
    from . import __version__
    
    info = {
        'name': 'BMB Backend Framework',
        'version': __version__,
        'orm': 'BMDB',
        'database': {
            'connection_configured': bool(BMDBConfig.DB_CONNECTION)
        },
        'models': {
            'auto_load': BMDBConfig.AUTO_LOAD_MODELS,
            'loaded': ModelsLoader.list_models()
        },
        'features': [
            'JWT Authentication',
            'CRUD Operations with BMDB',
            'User Management',
            'RESTful API',
            'Error Handling',
            'Request Logging'
        ]
    }
    
    return success_response(data=info)