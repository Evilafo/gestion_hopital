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
   cp .env
   
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

L'application sera accessible à l'adresse : http://localhost:5003

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



# Les fichiers du projet
# Rôle des Fichiers du Projet "Système de Gestion Hospitalière"

Ce document décrit la fonction principale de chaque fichier au sein de l'application de gestion hospitalière.

## Fichiers Racine

*   **`README.md`**
    *   **Rôle :** C'est le fichier de documentation principal du projet. Il fournit une vue d'ensemble de l'application, ses fonctionnalités, les instructions d'installation, de configuration, de démarrage, les comptes par défaut, la structure du projet, les rôles utilisateurs, les modèles de données, les routes principales, et des notes sur le développement et la sécurité.

*   **`app.py`**
    *   **Rôle :** C'est le cœur de l'application Flask. Il initialise l'application, la base de données (SQLAlchemy), et le gestionnaire de connexion (Flask-Login). Il définit tous les modèles de données (User, Salle, Creneau, RendezVous, FileAttente) et contient toutes les routes (URL) de l'application, gérant la logique métier, les interactions avec la base de données, et le rendu des templates HTML.

*   **`run.py`**
    *   **Rôle :** Ce script est le point d'entrée recommandé pour lancer l'application. Il initialise la base de données en créant toutes les tables si elles n'existent pas, puis il crée des données par défaut (utilisateur administrateur, médecin de test, salles) pour faciliter le démarrage et les tests. Enfin, il démarre le serveur Flask.

*   **`config.py`**
    *   **Rôle :** Ce fichier gère la configuration de l'application. Il définit différentes classes de configuration (base, développement, production, test) pour des environnements variés. Il charge les variables d'environnement (comme la clé secrète, les informations de connexion à la base de données) et configure des paramètres tels que le mode debug, la taille maximale des fichiers, etc.

*   **`/.env`**
    *   **Rôle :** C'est un fichier qui montre les variables d'environnement nécessaires au fonctionnement de l'application, permettant de stocker les informations sensibles (comme les identifiants de base de données et la clé secrète) en dehors du code source.

## Fichiers Statiques

*   **`static/css/style.css`**
    *   **Rôle :** Contient les styles CSS personnalisés de l'application. Il permet de modifier l'apparence des éléments HTML au-delà de ce que Bootstrap fournit par défaut, assurant une cohérence visuelle et une personnalisation de l'interface utilisateur.

## Fichiers de Templates HTML (`hopital/templates/`)

### Layouts

*   **`hopital/templates/layouts/base.html`**
    *   **Rôle :** C'est le template HTML de base dont héritent toutes les autres pages. Il définit la structure commune de l'application, incluant le `DOCTYPE`, les balises `head` (métadonnées, CSS), la barre de navigation (`header`), la zone de contenu principale (`main`), les messages flash, et le pied de page (`footer`). Il utilise des blocs Jinja2 (`{% block %}`) pour que les pages enfants puissent insérer leur contenu spécifique.

### Administration et Secrétariat (`admin_secretariat/`)

*   **`hopital/templates/admin_secretariat/dashboard.html`**
    *   **Rôle :** Affiche le tableau de bord principal pour les utilisateurs ayant les rôles 'secretaire' ou 'admin'. Il présente des liens rapides vers les différentes sections de gestion (personnel, patients, salles, rendez-vous, file d'attente).

*   **`hopital/templates/admin_secretariat/manage_appointments.html`**
    *   **Rôle :** Permet aux administrateurs et secrétaires de visualiser, filtrer, exporter, ajouter, modifier et annuler tous les rendez-vous du système. Il inclut un tableau listant les rendez-vous et une modale pour en créer de nouveaux.

*   **`hopital/templates/admin_secretariat/manage_patients.html`**
    *   **Rôle :** Affiche la liste de tous les patients enregistrés. Il permet de rechercher des patients, d'exporter la liste et d'accéder à leur dossier simplifié.

*   **`hopital/templates/admin_secretariat/manage_personnel.html`**
    *   **Rôle :** Permet aux administrateurs de gérer le personnel (médecins, secrétaires, autres administrateurs). Il affiche une liste du personnel avec leurs rôles et spécialités, et offre des options pour ajouter ou modifier des membres.

*   **`hopital/templates/admin_secretariat/manage_rooms.html`**
    *   **Rôle :** Permet aux administrateurs et secrétaires de gérer les salles de consultation. Il affiche l'état des salles (disponible/occupée), les médecins assignés, et offre la possibilité d'ajouter ou de supprimer des salles.

*   **`hopital/templates/admin_secretariat/queue_management.html`**
    *   **Rôle :** Gère la file d'attente des patients pour la journée en cours. Il organise les patients par médecin et permet au personnel administratif de changer le statut des patients (appeler, terminer consultation, marquer absent).

*   **`hopital/templates/admin_secretariat/edit_personnel.html`**
    *   **Rôle :** Formulaire utilisé pour ajouter un nouveau membre du personnel ou modifier les informations d'un membre existant. Il adapte les champs affichés en fonction du rôle (par exemple, spécialité et salle pour un médecin).

### Médecin (`medecin/`)

*   **`hopital/templates/medecin/dashboard.html`**
    *   **Rôle :** Tableau de bord spécifique aux médecins. Il affiche la liste des patients à consulter pour la journée, permet de gérer les créneaux horaires (ajouter, supprimer) et de consulter l'historique des consultations passées.

*   **`hopital/templates/medecin/add_slot.html`**
    *   **Rôle :** Formulaire permettant à un médecin d'ajouter de nouveaux créneaux de disponibilité à son emploi du temps.

*   **`hopital/templates/medecin/patient_dossier.html`**
    *   **Rôle :** Affiche un dossier simplifié d'un patient, incluant ses informations personnelles et l'historique de ses rendez-vous. Accessible par les médecins et le personnel administratif.

### Patient (`patient/`)

*   **`hopital/templates/patient/dashboard.html`**
    *   **Rôle :** Tableau de bord pour les patients. Il affiche leurs informations personnelles, leurs prochains rendez-vous (avec option d'annulation) et un lien pour prendre de nouveaux rendez-vous.

*   **`hopital/templates/patient/appointment_booking.html`**
    *   **Rôle :** Interface permettant aux patients de prendre un rendez-vous. Ils peuvent choisir une spécialité, puis un médecin, et enfin sélectionner un créneau horaire disponible.

*   **`hopital/templates/patient/edit_profile.html`**
    *   **Rôle :** Formulaire permettant aux patients de modifier leurs informations personnelles (nom, prénom, contact, date de naissance).

### Authentification (`auth/`)

*   **`hopital/templates/auth/login.html`**
    *   **Rôle :** Page de connexion pour tous les utilisateurs de l'application.

*   **`hopital/templates/auth/register_patient.html`**
    *   **Rôle :** Page d'inscription spécifiquement pour les nouveaux patients.
