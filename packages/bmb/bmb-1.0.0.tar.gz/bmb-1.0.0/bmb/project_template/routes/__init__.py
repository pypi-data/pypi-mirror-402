"""
Enregistrement des routes
"""
from routes.auth import auth_bp
from routes.users import users_bp
from routes.health import health_bp


def register_routes(app):
    """Enregistrer toutes les routes dynamiquement"""
    
    # Liste des blueprints à enregistrer
    blueprints = [
        (auth_bp, '/api/auth'),
        (users_bp, '/api/users'),
        (health_bp, '/api'),
    ]
    
    print("\n✅ Enregistrement des routes:")
    print("=" * 70)
    
    # Enregistrer chaque blueprint et afficher ses routes
    for blueprint, url_prefix in blueprints:
        app.register_blueprint(blueprint, url_prefix=url_prefix)
        
        # Afficher le nom du blueprint
        print(f"\n📦 Blueprint: {blueprint.name}")
        print(f"   Préfixe: {url_prefix}")
        print("   Routes:")
        
        # Récupérer toutes les routes du blueprint
        routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint.startswith(f"{blueprint.name}."):
                # Extraire le nom de la fonction
                func_name = rule.endpoint.split('.')[-1]
                # Extraire les méthodes HTTP
                methods = [m for m in rule.methods if m not in ['HEAD', 'OPTIONS']]
                routes.append({
                    'path': rule.rule,
                    'methods': methods,
                    'function': func_name
                })
        
        # Afficher les routes triées
        for route in sorted(routes, key=lambda x: x['path']):
            methods_str = ', '.join(route['methods'])
            print(f"      [{methods_str:12}] {route['path']:40} → {route['function']}")
    
    # Résumé final
    print("\n" + "=" * 70)
    total_routes = sum(len([r for r in app.url_map.iter_rules() 
                           if r.endpoint.startswith(f"{bp.name}.")]) 
                      for bp, _ in blueprints)
    print(f"✅ Total: {len(blueprints)} blueprints | {total_routes} endpoints enregistrés")
    print("=" * 70 + "\n")
