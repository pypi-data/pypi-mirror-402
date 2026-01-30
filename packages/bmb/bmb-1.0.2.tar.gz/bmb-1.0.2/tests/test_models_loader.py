"""
Tests pour le chargeur de modèles
"""

from bmb.models_loader import ModelsLoader, load_models


class TestModelsLoader:
    """Tests du chargeur de modèles BMDB"""
    
    def test_load_models(self):
        """Test du chargement des modèles"""
        models = load_models()
        
        assert models is not None
        assert 'Base' in models
        assert 'engine' in models
        assert 'SessionLocal' in models
        assert 'models' in models
    
    def test_get_model(self):
        """Test de récupération d'un modèle spécifique"""
        User = ModelsLoader.get_model('User')
        
        assert User is not None
    
    def test_list_models(self):
        """Test de listage des modèles"""
        models_list = ModelsLoader.list_models()
        
        assert isinstance(models_list, list)
        assert 'User' in models_list
    
    def test_get_engine(self):
        """Test de récupération de l'engine"""
        engine = ModelsLoader.get_engine()
        
        assert engine is not None
    
    def test_get_base(self):
        """Test de récupération de Base"""
        Base = ModelsLoader.get_base()
        
        assert Base is not None