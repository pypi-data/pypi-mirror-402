"""
Tests pour les routes d'authentification
"""

class TestAuth:
    """Tests d'authentification"""
    
    def test_register_success(self, client, clean_db):
        """Test d'inscription réussie"""
        response = client.post('/api/auth/register', json={
            'name': 'Alice Johnson',
            'email': 'alice@example.com',
            'password': 'secure123',
            'age': 25
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'data' in data
        assert 'token' in data['data']
        assert 'user' in data['data']
        assert data['data']['user']['name'] == 'Alice Johnson'
        assert data['data']['user']['email'] == 'alice@example.com'
    
    def test_register_duplicate_email(self, client, clean_db):
        """Test d'inscription avec email dupliqué"""
        # Première inscription
        client.post('/api/auth/register', json={
            'name': 'User 1',
            'email': 'duplicate@example.com',
            'password': 'pass123'
        })
        
        # Deuxième inscription avec le même email
        response = client.post('/api/auth/register', json={
            'name': 'User 2',
            'email': 'duplicate@example.com',
            'password': 'pass456'
        })
        
        assert response.status_code == 409
        data = response.get_json()
        assert 'error' in data
    
    def test_register_missing_fields(self, client):
        """Test d'inscription avec champs manquants"""
        response = client.post('/api/auth/register', json={
            'name': 'Incomplete User'
            # email et password manquants
        })
        
        assert response.status_code == 400
    
    def test_register_invalid_email(self, client):
        """Test d'inscription avec email invalide"""
        response = client.post('/api/auth/register', json={
            'name': 'Bad Email User',
            'email': 'not-an-email',
            'password': 'pass123'
        })
        
        assert response.status_code == 400
    
    def test_login_success(self, client, clean_db):
        """Test de connexion réussie"""
        # Créer un utilisateur
        client.post('/api/auth/register', json={
            'name': 'Login User',
            'email': 'login@example.com',
            'password': 'mypassword'
        })
        
        # Se connecter
        response = client.post('/api/auth/login', json={
            'email': 'login@example.com',
            'password': 'mypassword'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert 'token' in data['data']
    
    def test_login_wrong_password(self, client, clean_db):
        """Test de connexion avec mauvais mot de passe"""
        # Créer un utilisateur
        client.post('/api/auth/register', json={
            'name': 'User',
            'email': 'user@example.com',
            'password': 'correct'
        })
        
        # Connexion avec mauvais mot de passe
        response = client.post('/api/auth/login', json={
            'email': 'user@example.com',
            'password': 'wrong'
        })
        
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self, client):
        """Test de connexion avec utilisateur inexistant"""
        response = client.post('/api/auth/login', json={
            'email': 'nonexistent@example.com',
            'password': 'password'
        })
        
        assert response.status_code == 401
    
    def test_get_current_user(self, auth_client):
        """Test de récupération du profil utilisateur"""
        response = auth_client.get('/api/auth/me')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert 'user' in data['data']
        assert data['data']['user']['email'] == 'test@example.com'
    
    def test_get_current_user_no_token(self, client):
        """Test de récupération du profil sans token"""
        response = client.get('/api/auth/me')
        
        assert response.status_code == 401
    
    def test_refresh_token(self, auth_client):
        """Test de renouvellement du token"""
        response = auth_client.post('/api/auth/refresh')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert 'token' in data['data']