"""
Configuration pour les tests pytest
"""

import pytest
import sys
from pathlib import Path

# Ajouter le dossier parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bmb import create_app
from bmb.database import Database
from bmb.models_loader import load_models


@pytest.fixture(scope='session')
def app():
    """Créer l'application Flask pour les tests"""
    # Configurer pour les tests
    import os
    os.environ['TESTING'] = 'True'
    os.environ['DB_CONNECTION'] = 'sqlite:///./test.db'
    
    app = create_app()
    app.config['TESTING'] = True
    
    # Créer les tables
    Database.init_db()
    
    yield app
    
    # Cleanup: supprimer la DB de test
    test_db = Path('./test.db')
    if test_db.exists():
        test_db.unlink()


@pytest.fixture(scope='function')
def client(app):
    """Client de test Flask"""
    return app.test_client()


@pytest.fixture(scope='function')
def auth_client(client):
    """Client authentifié avec token JWT"""
    # Créer un utilisateur de test
    response = client.post('/api/auth/register', json={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'test123',
        'age': 25
    })
    
    data = response.get_json()
    token = data['data']['token']
    
    # Créer un client avec le token dans les headers
    class AuthClient:
        def __init__(self, client, token):
            self.client = client
            self.token = token
        
        def get(self, *args, **kwargs):
            kwargs.setdefault('headers', {})['Authorization'] = f'Bearer {self.token}'
            return self.client.get(*args, **kwargs)
        
        def post(self, *args, **kwargs):
            kwargs.setdefault('headers', {})['Authorization'] = f'Bearer {self.token}'
            return self.client.post(*args, **kwargs)
        
        def put(self, *args, **kwargs):
            kwargs.setdefault('headers', {})['Authorization'] = f'Bearer {self.token}'
            return self.client.put(*args, **kwargs)
        
        def delete(self, *args, **kwargs):
            kwargs.setdefault('headers', {})['Authorization'] = f'Bearer {self.token}'
            return self.client.delete(*args, **kwargs)
    
    return AuthClient(client, token)


@pytest.fixture(scope='function')
def clean_db():
    """Nettoyer la base de données après chaque test"""
    yield
    
    # Nettoyer après le test
    models = load_models()
    User = models.get('User')
    if User:
        session = Database.get_session()
        with session as s:
            s.query(User).delete()