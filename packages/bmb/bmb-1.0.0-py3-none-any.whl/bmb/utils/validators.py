"""
Validateurs de données
"""

import re


class Validator:
    """Classe de validation des données"""
    
    @staticmethod
    def validate_email(email):
        """Valider un email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password(password, min_length=6):
        """Valider un mot de passe"""
        if len(password) < min_length:
            return False, f"Le mot de passe doit contenir au moins {min_length} caractères"
        return True, "Mot de passe valide"
    
    @staticmethod
    def validate_required_fields(data, required_fields):
        """Valider la présence des champs requis"""
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        
        if missing_fields:
            return False, f"Champs manquants: {', '.join(missing_fields)}"
        
        return True, "Tous les champs requis sont présents"