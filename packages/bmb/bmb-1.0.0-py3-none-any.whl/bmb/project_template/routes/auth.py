"""
Routes d'authentification
"""

from flask import Blueprint, request
from werkzeug.security import generate_password_hash, check_password_hash

from models_loader import load_models
from utils import JWTManager, Validator, success_response, error_response

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Inscription d'un nouvel utilisateur
    
    Body:
        {
            "name": "string",
            "email": "string",
            "password": "string",
            "age": int (optionnel)
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response("Corps de requête manquant", 400)
        
        # Validation des champs requis
        is_valid, message = Validator.validate_required_fields(
            data,
            ['name', 'email', 'password']
        )
        if not is_valid:
            return error_response(message, 400)
        
        # Validation de l'email
        if not Validator.validate_email(data['email']):
            return error_response("Format d'email invalide", 400)
        
        # Validation du mot de passe
        is_valid, message = Validator.validate_password(data['password'])
        if not is_valid:
            return error_response(message, 400)
        
        # Charger le modèle User
        models = load_models()
        User = models.get('User')
        
        if not User:
            return error_response("Modèle User introuvable", 500)
        
        # Vérifier si l'email existe déjà
        existing_user = User.first(email=data['email'])
        if existing_user:
            return error_response("Cet email est déjà utilisé", 409)
        
        # Hasher le mot de passe
        hashed_password = generate_password_hash(data['password'])
        
        # Créer le nouvel utilisateur
        new_user = User(
            name=data['name'],
            email=data['email'],
            password=hashed_password,
            age=data.get('age')
        )
        
        # Sauvegarder avec BMDB save()
        saved_user = new_user.save()
        
        # Générer le token JWT
        token = JWTManager.generate_token(saved_user.id)
        
        return success_response(
            data={
                'token': token,
                'user': saved_user.to_dict()
            },
            message="Utilisateur créé avec succès",
            status=201
        )
        
    except Exception as e:
        return error_response(f"Erreur lors de l'inscription: {str(e)}", 500)


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Connexion utilisateur
    
    Body:
        {
            "email": "string",
            "password": "string"
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response("Corps de requête manquant", 400)
        
        # Validation des champs
        is_valid, message = Validator.validate_required_fields(
            data,
            ['email', 'password']
        )
        if not is_valid:
            return error_response(message, 400)
        
        # Charger le modèle User
        models = load_models()
        User = models.get('User')
        
        # Trouver l'utilisateur avec BMDB first()
        user = User.first(email=data['email'])
        
        if not user:
            return error_response("Email ou mot de passe incorrect", 401)
        
        # Vérifier le mot de passe
        if not check_password_hash(user.password, data['password']):
            return error_response("Email ou mot de passe incorrect", 401)
        
        # Générer le token JWT
        token = JWTManager.generate_token(user.id)
        
        return success_response(
            data={
                'token': token,
                'user': user.to_dict()
            },
            message="Connexion réussie"
        )
        
    except Exception as e:
        return error_response(f"Erreur lors de la connexion: {str(e)}", 500)


@auth_bp.route('/me', methods=['GET'])
@JWTManager.token_required
def get_current_user(current_user):
    """Récupérer les informations de l'utilisateur connecté"""
    try:
        return success_response(
            data={'user': current_user.to_dict()},
            message="Profil récupéré"
        )
    except Exception as e:
        return error_response(f"Erreur: {str(e)}", 500)


@auth_bp.route('/refresh', methods=['POST'])
@JWTManager.token_required
def refresh_token(current_user):
    """Renouveler le token JWT"""
    try:
        # Générer un nouveau token
        new_token = JWTManager.generate_token(current_user.id)
        
        return success_response(
            data={'token': new_token},
            message="Token renouvelé"
        )
        
    except Exception as e:
        return error_response(f"Erreur lors du renouvellement: {str(e)}", 500)


@auth_bp.route('/logout', methods=['POST'])
@JWTManager.token_required
def logout(current_user):
    """
    Déconnexion (côté client, il faut supprimer le token)
    Cette route existe surtout pour des logs ou futures fonctionnalités
    """
    return success_response(message="Déconnexion réussie")