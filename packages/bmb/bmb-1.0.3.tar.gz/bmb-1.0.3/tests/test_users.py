"""
Tests pour les routes utilisateurs (CRUD)
"""

class TestUsers:
    """Tests CRUD utilisateurs"""
    
    def test_get_users_list(self, auth_client):
        """Test de récupération de la liste des utilisateurs"""
        response = auth_client.get('/api/users')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert 'users' in data['data']
        assert 'pagination' in data['data']
    
    def test_get_users_with_pagination(self, auth_client):
        """Test de pagination"""
        response = auth_client.get('/api/users?page=1&page_size=5')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['pagination']['page'] == 1
        assert data['data']['pagination']['page_size'] == 5
    
    def test_get_user_by_id(self, auth_client, client, clean_db):
        """Test de récupération d'un utilisateur par ID"""
        # Créer un utilisateur
        reg_response = client.post('/api/auth/register', json={
            'name': 'Get Me',
            'email': 'getme@example.com',
            'password': 'pass123',
            'age': 30
        })
        user_id = reg_response.get_json()['data']['user']['id']
        
        # Récupérer l'utilisateur
        response = auth_client.get(f'/api/users/{user_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['user']['id'] == user_id
        assert data['data']['user']['name'] == 'Get Me'
    
    def test_get_nonexistent_user(self, auth_client):
        """Test de récupération d'un utilisateur inexistant"""
        response = auth_client.get('/api/users/99999')
        
        assert response.status_code == 404
    
    def test_update_user(self, auth_client, client):
        """Test de mise à jour d'un utilisateur"""
        # Créer un utilisateur et obtenir son token
        reg_response = client.post('/api/auth/register', json={
            'name': 'Update Me',
            'email': 'updateme@example.com',
            'password': 'pass123',
            'age': 25
        })
        
        user_id = reg_response.get_json()['data']['user']['id']
        token = reg_response.get_json()['data']['token']
        
        # Mettre à jour avec le bon token
        response = client.put(
            f'/api/users/{user_id}',
            json={'name': 'Updated Name', 'age': 26},
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['user']['name'] == 'Updated Name'
        assert data['data']['user']['age'] == 26
    
    def test_update_other_user_forbidden(self, auth_client):
        """Test de modification d'un autre utilisateur (interdit)"""
        response = auth_client.put('/api/users/99999', json={'name': 'Hacker'})
        
        # Doit retourner 403 (Forbidden) ou 404 (Not Found)
        assert response.status_code in [403, 404]
    
    def test_delete_user(self, client):
        """Test de suppression d'un utilisateur"""
        # Créer un utilisateur
        reg_response = client.post('/api/auth/register', json={
            'name': 'Delete Me',
            'email': 'deleteme@example.com',
            'password': 'pass123'
        })
        
        user_id = reg_response.get_json()['data']['user']['id']
        token = reg_response.get_json()['data']['token']
        
        # Supprimer l'utilisateur
        response = client.delete(
            f'/api/users/{user_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
    
    def test_search_user_by_email(self, auth_client, client, clean_db):
        """Test de recherche par email"""
        # Créer un utilisateur
        client.post('/api/auth/register', json={
            'name': 'Searchable',
            'email': 'search@example.com',
            'password': 'pass123'
        })
        
        # Rechercher
        response = auth_client.get('/api/users/search?email=search@example.com')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['user']['email'] == 'search@example.com'
    
    def test_get_user_stats(self, auth_client):
        """Test de récupération des statistiques"""
        response = auth_client.get('/api/users/stats')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert 'stats' in data['data']