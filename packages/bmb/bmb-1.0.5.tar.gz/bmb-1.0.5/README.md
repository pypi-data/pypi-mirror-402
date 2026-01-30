# BMB - Backend Framework

🚀 **BMB** est un framework backend Flask qui utilise **BMDB** (ORM Python) pour créer des API RESTful en quelques minutes.

## ✨ Fonctionnalités

### 🔐 Authentification JWT complète

- Inscription utilisateur (`POST /api/auth/register`)
- Connexion (`POST /api/auth/login`)
- Profil utilisateur (`GET /api/auth/me`)
- Renouvellement de token (`POST /api/auth/refresh`)
- Déconnexion (`POST /api/auth/logout`)

### 👥 CRUD Utilisateurs avec BMDB

Utilise **toutes les méthodes BMDB** :

- ✅ `save()` - Créer/modifier
- ✅ `delete()` - Supprimer
- ✅ `get(id)` - Récupérer par ID
- ✅ `all()` - Lister tous
- ✅ `filter(**kwargs)` - Filtrer
- ✅ `first(**kwargs)` - Premier résultat
- ✅ `count(**kwargs)` - Compter
- ✅ `to_dict()` - Sérialiser en JSON

### 📊 Endpoints disponibles

#### Authentification

```crul
POST   /api/auth/register    - Inscription
POST   /api/auth/login       - Connexion
GET    /api/auth/me          - Profil (protégé)
POST   /api/auth/refresh     - Renouveler token (protégé)
POST   /api/auth/logout      - Déconnexion (protégé)
```

#### Utilisateurs

```crul
GET    /api/users            - Liste avec filtres & pagination
GET    /api/users/:id        - Détails utilisateur
PUT    /api/users/:id        - Modifier utilisateur
DELETE /api/users/:id        - Supprimer utilisateur
GET    /api/users/search     - Rechercher par email
GET    /api/users/stats      - Statistiques
```

#### Monitoring

```crul
GET    /api/health           - Health check
GET    /api/info             - Informations app
```

## 🚀 Installation rapide

### 1. Installer BMB

```bash
pip install bmb
```

### 2. Créer les modèles BMDB

```bash
# Créer le fichier models.bmdb
bmdb create-model User
bmdb add-fields User name:string email:string:unique password:string age:integer

# Générer les modèles Python
bmdb generate
```

### 3. Configuration

```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer .env avec votre configuration
nano .env
```

Configuration minimale dans `.env` :

```env
DB_CONNECTION=sqlite:///./database.db
SECRET_KEY=your-secret-key
JWT_SECRET=your-jwt-secret
```

### 4. Lancer l'application

```python
# run.py
from bmb import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
```

```bash
python run.py
```

🎉 Votre API est prête sur `http://localhost:5000` !

## 📁 Structure du projet

```text
mon-projet/
│
├── bmdb/                      # Modèles BMDB
│   ├── models/
│   │   ├── generated/
│   │   │   └── models.py      # Généré par BMDB
│   │   └── models.bmdb        # Définition des modèles
│   └── __init__.py
│
├── bmb/                       # Framework BMB
│   ├── __init__.py
│   ├── app.py                 # Factory Flask
│   ├── models_loader.py       # Chargement modèles BMDB
│   ├── database.py            # Gestionnaire DB
│   │
│   ├── config/                # Configuration séparée
│   │   ├── __init__.py
│   │   ├── app_config.py      # Config Flask/JWT
│   │   └── bmdb_config.py     # Config BMDB
│   │
│   ├── routes/                # Routes (blueprints)
│   │   ├── __init__.py
│   │   ├── auth.py            # Authentification
│   │   ├── users.py           # CRUD utilisateurs
│   │   └── health.py          # Monitoring
│   │
│   ├── utils/                 # Utilitaires
│   │   ├── __init__.py
│   │   ├── jwt_utils.py       # Gestion JWT
│   │   ├── validators.py      # Validateurs
│   │   └── responses.py       # Réponses API
│   │
│   └── middleware/            # Middleware
│       ├── __init__.py
│       ├── logging.py         # Logging requests
│       └── error_handlers.py  # Gestion erreurs
│
├── .env                       # Configuration (ne pas commiter)
├── .env.example               # Exemple de configuration
├── requirements.txt           # Dépendances
├── setup.py                   # Installation
└── run.py                     # Point d'entrée
```

## 🔧 Architecture modulaire

### Séparation des configurations

```python
# Config Flask (bmb/config/app_config.py)
class AppConfig:
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET')
    # ...

# Config BMDB (bmb/config/bmdb_config.py)
class BMDBConfig:
    DB_CONNECTION = os.getenv('DB_CONNECTION')
    MODELS_DIR = Path.cwd() / "bmdb" / "models" / "generated"
    # ...
```

### Chargement dynamique des modèles

```python
from bmb import load_models

# Charger tous les modèles BMDB
models = load_models()

# Accéder à un modèle
User = models['User']
Post = models['Post']

# Utiliser les méthodes BMDB
users = User.all()
user = User.get(1)
new_user = User(name="Alice").save()
```

### Factory Pattern pour Flask

```python
from bmb import create_app

# Créer l'application avec configuration
app = create_app()

# Les modèles sont automatiquement chargés
# La DB est automatiquement initialisée
```

## 💡 Exemples d'utilisation

### Inscription d'un utilisateur

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Johnson",
    "email": "alice@example.com",
    "password": "secure123",
    "age": 25
  }'
```

Réponse :

```json
{
  "message": "Utilisateur créé avec succès",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "name": "Alice Johnson",
      "email": "alice@example.com",
      "age": 25
    }
  }
}
```

### Connexion

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "secure123"
  }'
```

### Récupérer son profil

```bash
curl http://localhost:5000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Lister les utilisateurs (avec filtres)

```bash
curl "http://localhost:5000/api/users?age=25&page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Rechercher un utilisateur

```bash
curl "http://localhost:5000/api/users/search?email=alice@example.com" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🎯 Points forts

✅ **Installation ultra-rapide** - `pip install bmb`  
✅ **Configuration simple** - Un seul fichier `.env`  
✅ **Authentification JWT incluse** - Prête à l'emploi  
✅ **CRUD automatique** - Utilise BMDB ORM  
✅ **Architecture modulaire** - Code propre et organisé  
✅ **Chargement dynamique** - Modèles chargés automatiquement  
✅ **Pagination intégrée** - Pages de résultats  
✅ **Validation des données** - Sécurité renforcée  
✅ **Gestion d'erreurs** - Messages clairs  
✅ **Logging automatique** - Suivi des requêtes  
✅ **Health checks** - Monitoring inclus  

## 🔌 Intégration avec BMDB

BMB utilise **intelligemment** toutes les fonctionnalités de BMDB :

```python
# Dans vos routes
from bmb import load_models

models = load_models()
User = models['User']

# Utiliser les méthodes BMDB
user = User.get(user_id)           # Récupérer par ID
users = User.all()                 # Tous les utilisateurs
filtered = User.filter(age=25)     # Filtrer
first = User.first(email="x@y.z")  # Premier résultat
count = User.count(age=25)         # Compter
user_dict = user.to_dict()         # Sérialiser

# Créer/Modifier
new_user = User(name="Bob").save()
user.age = 30
user.save()

# Supprimer
user.delete()
```

## 🗄️ Bases de données supportées

Via BMDB, BMB supporte :

- **PostgreSQL** - Production recommandée
- **MySQL** - Alternative solide
- **SQLite** - Développement rapide

## 🛠️ Développement

### Tests

```bash
# Installer les dépendances de dev
pip install -e ".[dev]"

# Lancer les tests
pytest

# Avec couverture
pytest --cov=bmb
```

### Linting

```bash
# Formater le code
black bmb/

# Vérifier le style
flake8 bmb/

# Type checking
mypy bmb/
```

## 📦 Publier sur PyPI

```bash
# Build
python setup.py sdist bdist_wheel

# Upload
twine upload dist/*
```

## 🤝 Contribution

Les contributions sont les bienvenues ! Ouvrez une issue ou un PR sur GitHub.

## 📄 Licence

MIT License - Voir LICENSE pour plus de détails.

## 🔗 Liens

- **GitHub**: <https://github.com/BM-Framework/bmb>
- **PyPI**: <https://pypi.org/project/bmb>
- **BMDB**: <https://github.com/BM-Framework/bmdb>
- **Documentation**: <https://bm-framework.github.io>

---

Développé avec ❤️ par **BM Framework | Marouan Bouchettoy**
