"""
Gestionnaires d'erreurs globaux
"""

from flask import jsonify
import traceback


def register_error_handlers(app):
    """Enregistrer les gestionnaires d'erreurs"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Requête invalide', 'details': str(error)}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Non autorisé', 'details': str(error)}), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Accès refusé', 'details': str(error)}), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Ressource introuvable', 'details': str(error)}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        if app.debug:
            return jsonify({
                'error': 'Erreur serveur interne',
                'details': str(error),
                'traceback': traceback.format_exc()
            }), 500
        return jsonify({'error': 'Erreur serveur interne'}), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Capturer toutes les exceptions non gérées"""
        if app.debug:
            return jsonify({
                'error': 'Exception non gérée',
                'details': str(error),
                'type': type(error).__name__,
                'traceback': traceback.format_exc()
            }), 500
        return jsonify({'error': 'Une erreur est survenue'}), 500