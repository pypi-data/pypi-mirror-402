"""
Tests pour les routes de santé
"""


class TestHealth:
    """Tests de health check"""
    
    def test_health_check(self, client):
        """Test du health check"""
        response = client.get('/api/health')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert data['data']['status'] in ['healthy', 'unhealthy']
    
    def test_app_info(self, client):
        """Test des informations de l'application"""
        response = client.get('/api/info')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert 'name' in data['data']
        assert 'version' in data['data']