# Système de Gestion Hospitalière

Application web de gestion d'hôpital développée avec Flask (Python), HTML/CSS/JS et une base de données MySQL.

## Fonctionnalités

L'application permet de gérer :

- ✅ **Patients** : Inscription, dossier simplifié, prise de rendez-vous
- ✅ **Médecins** : Spécialités, emploi du temps, gestion des créneaux
- ✅ **Personnel** : Secrétaires, administrateurs, gestion des rôles
- ✅ **Salles** : Gestion des salles de consultation
- ✅ **Créneaux** : Gestion des créneaux horaires disponibles
- ✅ **Rendez-vous** : Prise de rendez-vous par les patients
- ✅ **File d'attente** : Gestion de la file le jour de la consultation
- ✅ **Dashboard** : Interface d'administration pour le secrétariat

## Installation

### Prérequis

- Python 3.7 ou supérieur
- MySQL 5.7 ou supérieur
- pip (gestionnaire de paquets Python)

### Configuration

1. **Cloner ou télécharger le projet**

2. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configuration de la base de données**
   - Créer une base de données MySQL nommée `hopital_db`
   - Configurer les paramètres dans `config.py` ou via les variables d'environnement

4. **Variables d'environnement** (optionnel)
   ```bash
   # Copier le fichier d'exemple
   cp env_example.txt .env
   
   # Modifier les valeurs selon votre configuration
   DB_HOST=localhost
   DB_USER=votre_utilisateur
   DB_PASSWORD=votre_mot_de_passe
   DB_NAME=hopital_db
   SECRET_KEY=votre_cle_secrete_unique
   ```

### Démarrage

```bash
python run.py
```

L'application sera accessible à l'adresse : http://localhost:5002

## Comptes par défaut

Après le premier démarrage, les comptes suivants sont créés automatiquement :

- **Administrateur** : `admin@hopital.com` / `admin123`
- **Médecin test** : `jean.dupont@hopital.com` / `medecin123`

## Structure de l'application

```
├── app.py                 # Application Flask principale
├── config.py              # Configuration
├── run.py                 # Script de démarrage
├── requirements.txt       # Dépendances Python
├── static/
│   └── css/
│       └── style.css      # Styles personnalisés
└── hopital/
    └── templates/         # Templates HTML
        ├── layouts/
        ├── auth/
        ├── admin_secretariat/
        ├── medecin/
        └── patient/
```

## Rôles utilisateurs

1. **Patient** : Peut prendre des rendez-vous, consulter son dossier
2. **Médecin** : Gère ses créneaux, consulte sa file d'attente
3. **Secrétaire** : Gère les rendez-vous, la file d'attente, les patients
4. **Administrateur** : Accès complet au système, gestion du personnel

## Modèles de données

- **User** : Utilisateurs (patients, médecins, personnel)
- **Salle** : Salles de consultation
- **Creneau** : Créneaux horaires des médecins
- **RendezVous** : Rendez-vous pris par les patients
- **FileAttente** : Gestion de la file d'attente quotidienne

## API et Routes

### Authentification
- `GET/POST /login` : Connexion
- `GET /logout` : Déconnexion
- `GET/POST /register-patient` : Inscription patient

### Patients
- `GET /book-appointment` : Prise de rendez-vous
- `POST /confirm-appointment` : Confirmation rendez-vous
- `GET/POST /edit-profile` : Modification profil

### Médecins
- `GET/POST /add-slot` : Ajout de créneaux
- `GET /start-consultation/<id>` : Démarrer consultation
- `GET /end-consultation/<id>` : Terminer consultation

### Secrétariat/Administration
- `GET /queue-management` : Gestion file d'attente
- `GET /manage-patients` : Gestion patients
- `GET /manage-personnel` : Gestion personnel
- `GET /manage-rooms` : Gestion salles
- `GET /manage-appointments` : Gestion rendez-vous

## Développement

### Ajout de nouvelles fonctionnalités

1. Modifier les modèles dans `app.py` si nécessaire
2. Ajouter les routes correspondantes
3. Créer les templates HTML dans `hopital/templates/`
4. Tester les fonctionnalités

### Base de données

Pour réinitialiser la base de données :
```python
from app import app, db
with app.app_context():
    db.drop_all()
    db.create_all()
```

## Sécurité

- Mots de passe hashés avec Werkzeug
- Sessions gérées par Flask-Login
- Protection CSRF (à implémenter si nécessaire)
- Validation des entrées utilisateur (à étendre)

## Production

Pour un déploiement en production :

1. Modifier `DEBUG = False` dans la configuration
2. Utiliser une clé secrète robuste
3. Configurer un serveur WSGI (Gunicorn)
4. Utiliser un serveur web (Nginx)
5. Configurer HTTPS

## Support

Cette application constitue une base solide pour un système de gestion hospitalière. Elle peut être étendue selon les besoins spécifiques de chaque établissement.
