"""
Enregistrement des routes
"""

def register_routes(app):
    """Enregistrer toutes les routes"""
    from .auth import auth_bp
    from .users import users_bp
    from .health import health_bp
    
    # Enregistrer les blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(health_bp, url_prefix='/api')
    
    print("✅ Routes enregistrées:")
    print("   - /api/auth/*")
    print("   - /api/users/*")
    print("   - /api/health")