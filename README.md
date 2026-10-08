# Clinique Bodo - Système de Gestion Hospitalière

Application web de gestion de clinique développée avec Flask (Python), HTML/CSS/JS et une base de données MySQL.

## Fonctionnalités

L'application permet de gérer :

- ✅ **Patients** : Inscription (8 caractères alphanumériques), dossier médical, prise de rendez-vous
- ✅ **Médecins** : Spécialités multiples, emploi du temps, gestion des créneaux (création rapide matinée/après-midi/journée)
- ✅ **Personnel** : Secrétaires, administrateurs, gestion des rôles
- ✅ **Salles** : Gestion des salles de consultation avec statut d'occupation en temps réel
- ✅ **Créneaux** : Gestion des créneaux horaires disponibles
- ✅ **Rendez-vous** : Prise de rendez-vous par les patients
- ✅ **File d'attente** : Gestion de la file le jour de la consultation avec appel automatique
- ✅ **Écran d'appel** : Affichage en temps réel des patients appelés dans la salle d'attente
- ✅ **Dashboard** : Interface d'administration pour le secrétariat
- ✅ **Notes de consultation** : Enregistrement des diagnostics et ordonnances

## Installation avec Docker

### Prérequis

- Docker
- Docker Compose

### Démarrage rapide

```bash
# Cloner le projet
git clone <repository-url>
cd juniorfrebonne

# Démarrer les conteneurs
docker compose up -d

# L'application sera accessible à http://localhost:5002
# phpMyAdmin sera accessible à http://localhost:8080
```

### Arrêt

```bash
docker compose down
```

## Installation locale

### Prérequis

- Python 3.8 ou supérieur
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

## Comptes de test

Comptes disponibles pour les tests :

| Rôle | Email | Mot de passe |
| --- | --- | --- |
| Admin | admin@hopital.com | admin123 |
| Secrétaire | marie.dupont@cliniquebodo.com | Secret1234 |
| Médecin | pierre.bernard@cliniquebodo.com | Medecin1234 |
| Patient | aya.kouassi@email.com | Patient1234 |


## Structure de l'application

```
├── app.py                 # Application Flask principale
├── config.py              # Configuration
├── run.py                 # Script de démarrage
├── requirements.txt       # Dépendances Python
├── docker-compose.yml     # Configuration Docker
├── static/
│   ├── css/
│   │   └── style.css      # Styles personnalisés
│   └── js/
│       └── main.js        # Scripts JavaScript
├── migrations/            # Migrations de base de données
│   └── versions/
└── hopital/
    ├── extensions.py      # Extensions Flask
    ├── models.py          # Modèles de données
    ├── routes/            # Routes de l'application
    │   ├── admin.py
    │   ├── auth.py
    │   ├── medecin.py
    │   ├── patient.py
    │   └── api.py
    ├── services/          # Logique métier
    │   ├── admin_service.py
    │   ├── appointment_service.py
    │   ├── auth_service.py
    │   ├── medecin_service.py
    │   ├── patient_service.py
    │   └── queue_service.py
    ├── security.py        # Configuration sécurité
    └── templates/         # Templates HTML
        ├── layouts/
        ├── auth/
        ├── admin_secretariat/
        ├── medecin/
        └── patient/
```

## Rôles utilisateurs

1. **Patient** : Peut prendre des rendez-vous, consulter son dossier, effectuer un check-in
2. **Médecin** : Gère ses créneaux, consulte sa file d'attente, rédige des notes de consultation
3. **Secrétaire** : Gère les rendez-vous, la file d'attente, les patients, appelle les patients
4. **Administrateur** : Accès complet au système, gestion du personnel et des salles

## Modèles de données

- **User** : Utilisateurs (patients, médecins, personnel)
- **PatientProfil** : Profil détaillé des patients
- **Salle** : Salles de consultation avec statut d'occupation
- **Creneau** : Créneaux horaires des médecins
- **RendezVous** : Rendez-vous pris par les patients
- **FileAttente** : Gestion de la file d'attente quotidienne
- **NoteConsultation** : Notes et diagnostics des consultations
- **JournalAcces** : Journal des accès aux dossiers patients

## API et Routes

### Authentification
- `GET/POST /login` : Connexion avec affichage/masquage du mot de passe
- `GET /logout` : Déconnexion
- `GET/POST /register-patient` : Inscription patient

### Patients
- `GET /book-appointment` : Prise de rendez-vous
- `POST /confirm-appointment` : Confirmation rendez-vous
- `GET/POST /edit-profile` : Modification profil
- `GET /ma-file` : Position dans la file d'attente
- `POST /check-in/<id>` : Enregistrement d'arrivée

### Médecins
- `GET /medecin/dashboard` : Tableau de bord médecin
- `GET/POST /add-slot` : Ajout de créneaux (avec sélection rapide)
- `GET /planning-semaine` : Planning hebdomadaire
- `POST /delete-slot/<id>` : Suppression de créneau
- `POST /start-consultation/<id>` : Démarrer consultation
- `POST /end-consultation/<id>` : Terminer consultation
- `GET/POST /consultation-note/<id>` : Note de consultation
- `GET /view-patient-dossier/<id>` : Consultation dossier patient

### Secrétariat/Administration
- `GET /queue-management` : Gestion file d'attente
- `GET /waiting-room` : Écran d'appel
- `GET /queue-print` : Impression de la file
- `POST /call-patient/<id>` : Appeler un patient
- `POST /next-patient/<id>` : Patient suivant
- `POST /finish-consultation/<id>` : Terminer consultation
- `POST /mark-absent/<id>` : Marquer absent
- `POST /delay-patient/<id>` : Enregistrer retard
- `POST /move-queue/<id>/<direction>` : Déplacer dans la file
- `GET /manage-patients` : Gestion patients
- `GET/POST /add-patient` : Ajouter patient
- `GET/POST /edit-patient/<id>` : Modifier patient
- `GET /manage-personnel` : Gestion personnel
- `GET/POST /add-personnel` : Ajouter personnel
- `GET/POST /edit-personnel/<id>` : Modifier personnel
- `POST /delete-personnel/<id>` : Supprimer personnel
- `GET /manage-rooms` : Gestion salles
- `POST /add-room` : Ajouter salle
- `POST /edit-room/<id>` : Modifier salle
- `POST /delete-room/<id>` : Supprimer salle
- `GET /manage-appointments` : Gestion rendez-vous
- `GET /stats` : Statistiques

### API
- `GET /api/queue-today` : API pour l'écran d'appel (polling)

## Sécurité

- Mots de passe hashés avec Werkzeug (PBKDF2)
- Sessions gérées par Flask-Login
- Protection CSRF avec Flask-WTF
- Rate limiting avec Flask-Limiter
- Validation des mots de passe (8 caractères alphanumériques minimum)
- Headers de sécurité configurés

## Données de test

Une migration de données de test est disponible (`migrations/versions/003_seed_sample_data.py`) qui crée :
- 44 patients avec des noms ivoiriens
- 10 médecins avec différentes spécialités
- 10 salles de consultation
- 800 créneaux sur 2 semaines
- 58 rendez-vous

Pour appliquer les données de test avec Docker :
```bash
docker exec hopital-web python -c "
import sys
sys.path.insert(0, '/app')
from app import create_app
from hopital.extensions import db
from hopital.models import Salle
from datetime import date

app = create_app()
with app.app_context():
    # Exécuter le script de migration manuellement
    exec(open('/app/migrations/versions/003_seed_sample_data.py').read())
"
```

## Production

Pour un déploiement en production :

1. Modifier `FLASK_ENV=production` dans docker-compose.yml
2. Utiliser une clé secrète robuste via `SECRET_KEY` env var
3. Configurer un serveur WSGI (Gunicorn)
4. Utiliser un serveur web (Nginx)
5. Configurer HTTPS
6. Utiliser des variables d'environnement pour les credentials

## Support

Cette application constitue une base solide pour un système de gestion hospitalière. Elle peut être étendue selon les besoins spécifiques de chaque établissement.