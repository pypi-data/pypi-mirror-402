"""
Helpers pour les réponses API standardisées
"""

from flask import jsonify


def api_response(data=None, message=None, status=200):
    """Réponse API standardisée"""
    response = {}
    
    if message:
        response['message'] = message
    
    if data is not None:
        response['data'] = data
    
    return jsonify(response), status


def success_response(data=None, message="Succès", status=200):
    """Réponse de succès"""
    return api_response(data=data, message=message, status=status)


def error_response(message, status=400, errors=None):
    """Réponse d'erreur"""
    response = {'error': message}
    
    if errors:
        response['errors'] = errors
    
    return jsonify(response), status