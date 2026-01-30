"""
Routes CRUD pour les utilisateurs
Utilise toutes les méthodes BMDB: get, all, filter, first, count, save, delete
"""

from flask import Blueprint, request
from werkzeug.security import generate_password_hash

from models_loader import load_models
from utils import JWTManager, Validator, success_response, error_response
from config import AppConfig

users_bp = Blueprint('users', __name__)


@users_bp.route('', methods=['GET'])
@JWTManager.token_required
def get_users(current_user):
    """
    Récupérer tous les utilisateurs avec filtres et pagination
    
    Query params:
        - age: int (filtre par âge)
        - name: string (filtre par nom)
        - email: string (filtre par email)
        - page: int (numéro de page, défaut: 1)
        - page_size: int (taille de page, défaut: 20, max: 100)
    """
    try:
        models = load_models()
        User = models.get('User')
        
        # Récupérer les paramètres de filtrage
        filters = {}
        if request.args.get('age'):
            try:
                filters['age'] = int(request.args.get('age'))
            except ValueError:
                return error_response("Le paramètre 'age' doit être un entier", 400)
        
        if request.args.get('name'):
            filters['name'] = request.args.get('name')
        
        if request.args.get('email'):
            filters['email'] = request.args.get('email')
        
        # Pagination
        try:
            page = int(request.args.get('page', 1))
            page_size = min(
                int(request.args.get('page_size', AppConfig.DEFAULT_PAGE_SIZE)),
                AppConfig.MAX_PAGE_SIZE
            )
        except ValueError:
            return error_response("Paramètres de pagination invalides", 400)
        
        # Utiliser BMDB filter() ou all()
        if filters:
            users = User.filter(**filters)
        else:
            users = User.all()
        
        # Compter avec BMDB count()
        total_count = User.count(**filters) if filters else User.count()
        
        # Pagination manuelle (ou implémenter dans BMDB)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_users = users[start:end]
        
        return success_response(
            data={
                'users': [user.to_dict() for user in paginated_users],
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size
                }
            }
        )
        
    except Exception as e:
        return error_response(f"Erreur: {str(e)}", 500)


@users_bp.route('/<int:user_id>', methods=['GET'])
@JWTManager.token_required
def get_user(current_user, user_id):
    """
    Récupérer un utilisateur par ID
    Utilise BMDB get()
    """
    try:
        models = load_models()
        User = models.get('User')
        
        # Utiliser BMDB get()
        user = User.get(user_id)
        
        if not user:
            return error_response("Utilisateur introuvable", 404)
        
        return success_response(
            data={'user': user.to_dict()}
        )
        
    except Exception as e:
        return error_response(f"Erreur: {str(e)}", 500)


@users_bp.route('/<int:user_id>', methods=['PUT'])
@JWTManager.token_required
def update_user(current_user, user_id):
    """
    Mettre à jour un utilisateur
    Utilise BMDB get() et save()
    
    Body:
        {
            "name": "string" (optionnel),
            "email": "string" (optionnel),
            "password": "string" (optionnel),
            "age": int (optionnel)
        }
    """
    try:
        # Vérifier les permissions
        if current_user.id != user_id:
            return error_response("Non autorisé à modifier cet utilisateur", 403)
        
        models = load_models()
        User = models.get('User')
        
        # Récupérer l'utilisateur avec BMDB get()
        user = User.get(user_id)
        if not user:
            return error_response("Utilisateur introuvable", 404)
        
        data = request.get_json()
        if not data:
            return error_response("Corps de requête manquant", 400)
        
        # Mettre à jour les champs
        if 'name' in data:
            user.name = data['name']
        
        if 'email' in data:
            # Valider l'email
            if not Validator.validate_email(data['email']):
                return error_response("Format d'email invalide", 400)
            
            # Vérifier si l'email est déjà utilisé
            existing = User.first(email=data['email'])
            if existing and existing.id != user_id:
                return error_response("Cet email est déjà utilisé", 409)
            
            user.email = data['email']
        
        if 'age' in data:
            try:
                user.age = int(data['age'])
            except (ValueError, TypeError):
                return error_response("L'âge doit être un entier", 400)
        
        if 'password' in data:
            # Valider le mot de passe
            is_valid, message = Validator.validate_password(data['password'])
            if not is_valid:
                return error_response(message, 400)
            
            user.password = generate_password_hash(data['password'])
        
        # Sauvegarder avec BMDB save()
        updated_user = user.save()
        
        return success_response(
            data={'user': updated_user.to_dict()},
            message="Utilisateur mis à jour avec succès"
        )
        
    except Exception as e:
        return error_response(f"Erreur: {str(e)}", 500)


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@JWTManager.token_required
def delete_user(current_user, user_id):
    """
    Supprimer un utilisateur
    Utilise BMDB get() et delete()
    """
    try:
        # Vérifier les permissions
        if current_user.id != user_id:
            return error_response("Non autorisé à supprimer cet utilisateur", 403)
        
        models = load_models()
        User = models.get('User')
        
        # Récupérer l'utilisateur avec BMDB get()
        user = User.get(user_id)
        if not user:
            return error_response("Utilisateur introuvable", 404)
        
        # Supprimer avec BMDB delete()
        success = user.delete()
        
        if success:
            return success_response(
                message="Utilisateur supprimé avec succès"
            )
        else:
            return error_response("Échec de la suppression", 500)
        
    except Exception as e:
        return error_response(f"Erreur: {str(e)}", 500)


@users_bp.route('/search', methods=['GET'])
@JWTManager.token_required
def search_user(current_user):
    """
    Rechercher un utilisateur par email
    Utilise BMDB first()
    
    Query param:
        - email: string (requis)
    """
    try:
        email = request.args.get('email')
        if not email:
            return error_response("Paramètre 'email' requis", 400)
        
        models = load_models()
        User = models.get('User')
        
        # Utiliser BMDB first()
        user = User.first(email=email)
        
        if not user:
            return error_response("Utilisateur introuvable", 404)
        
        return success_response(
            data={'user': user.to_dict()}
        )
        
    except Exception as e:
        return error_response(f"Erreur: {str(e)}", 500)


@users_bp.route('/stats', methods=['GET'])
@JWTManager.token_required
def get_user_stats(current_user):
    """
    Statistiques des utilisateurs
    Utilise BMDB count() avec différents filtres
    """
    try:
        models = load_models()
        User = models.get('User')
        
        # Compter le total avec BMDB count()
        total_users = User.count()
        
        # Récupérer tous les utilisateurs pour les stats détaillées
        all_users = User.all()
        
        # Calculer des statistiques
        ages = [user.age for user in all_users if user.age is not None]
        
        stats = {
            'total_users': total_users,
            'average_age': sum(ages) / len(ages) if ages else 0,
            'users_with_age': len(ages),
            'users_without_age': total_users - len(ages)
        }
        
        # Compter par tranche d'âge
        age_ranges = {
            '18-25': 0,
            '26-35': 0,
            '36-45': 0,
            '46+': 0
        }
        
        for age in ages:
            if 18 <= age <= 25:
                age_ranges['18-25'] += 1
            elif 26 <= age <= 35:
                age_ranges['26-35'] += 1
            elif 36 <= age <= 45:
                age_ranges['36-45'] += 1
            else:
                age_ranges['46+'] += 1
        
        stats['age_distribution'] = age_ranges
        
        return success_response(data={'stats': stats})
        
    except Exception as e:
        return error_response(f"Erreur: {str(e)}", 500)