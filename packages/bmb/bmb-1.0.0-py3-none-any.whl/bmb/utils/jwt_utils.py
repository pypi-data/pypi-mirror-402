"""
Gestionnaire JWT
"""

import jwt
import datetime
from functools import wraps
from flask import request, jsonify
from ..config import AppConfig
from ..models_loader import load_models


class JWTManager:
    """Gestionnaire de tokens JWT"""
    
    @staticmethod
    def generate_token(user_id, expiration_hours=None):
        """Générer un token JWT"""
        if expiration_hours is None:
            expiration_hours = AppConfig.JWT_EXPIRATION_HOURS
        
        payload = {
            'user_id': user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=expiration_hours),
            'iat': datetime.datetime.utcnow()
        }
        
        return jwt.encode(payload, AppConfig.JWT_SECRET_KEY, algorithm=AppConfig.JWT_ALGORITHM)
    
    @staticmethod
    def decode_token(token):
        """Décoder un token JWT"""
        try:
            return jwt.decode(
                token,
                AppConfig.JWT_SECRET_KEY,
                algorithms=[AppConfig.JWT_ALGORITHM]
            )
        except jwt.ExpiredSignatureError:
            raise ValueError("Token expiré")
        except jwt.InvalidTokenError:
            raise ValueError("Token invalide")
    
    @staticmethod
    def token_required(f):
        """Décorateur pour protéger les routes"""
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            
            # Récupérer le token
            if 'Authorization' in request.headers:
                auth_header = request.headers['Authorization']
                try:
                    token = auth_header.split(" ")[1]  # Bearer TOKEN
                except IndexError:
                    return jsonify({'error': 'Format de token invalide'}), 401
            
            if not token:
                return jsonify({'error': 'Token manquant'}), 401
            
            try:
                # Décoder le token
                data = JWTManager.decode_token(token)
                
                # Charger le modèle User
                models = load_models()
                User = models.get('User')
                
                if not User:
                    return jsonify({'error': 'Modèle User introuvable'}), 500
                
                # Récupérer l'utilisateur
                current_user = User.get(data['user_id'])
                
                if not current_user:
                    return jsonify({'error': 'Utilisateur introuvable'}), 401
                
            except ValueError as e:
                return jsonify({'error': str(e)}), 401
            except Exception as e:
                return jsonify({'error': f'Erreur d\'authentification: {str(e)}'}), 401
            
            return f(current_user, *args, **kwargs)
        
        return decorated