# Système de Gestion Hospitalière

Application web de gestion d'hôpital développée avec **Flask (Python)**, **HTML/CSS/JS** et une **base de données MySQL**.

---

## Description du projet

Ce projet est une application web permettant de gérer les aspects essentiels du fonctionnement d’un hôpital : patients, médecins, personnel, salles, créneaux horaires et rendez-vous.
Elle inclut un **dashboard d’administration** pour le secrétariat et le personnel médical.

Le projet est conçu comme un **prototype évolutif**, facilement extensible avec des fonctionnalités comme la facturation, les notifications, la téléconsultation ou les statistiques médicales.

---

## Fonctionnalités principales

* ✅ **Patients** : Inscription, dossier simplifié, prise de rendez-vous
* ✅ **Médecins** : Spécialités, emploi du temps, gestion des créneaux
* ✅ **Personnel** : Secrétaires, administrateurs, gestion des rôles
* ✅ **Salles** : Gestion des salles de consultation
* ✅ **Créneaux horaires** : Création et gestion par les médecins
* ✅ **Rendez-vous** : Réservation, confirmation, annulation
* ✅ **File d'attente** : Gestion en temps réel pour les consultations
* ✅ **Dashboard** : Interface d’administration intuitive

---

## Prérequis

Avant de lancer le projet, installez :

* [Python 3.10+](https://www.python.org/downloads/)
* [MySQL 8+](https://dev.mysql.com/downloads/)
* [Git](https://git-scm.com/)
* [Pip](https://pip.pypa.io/en/stable/installation/)

---


Vérifiez vos versions :

```bash
python --version
mysql --version
git --version
pip --version
```

---

## Installation du projet

### 1️⃣ Cloner le dépôt

```bash
git clone https://github.com/Evilafo/gestion_hopital.git
cd gestion_hopital
```

### 2️⃣ Créer un environnement virtuel

```bash
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
```

### 3️⃣ Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4️⃣ Créer la base de données MySQL

Connectez-vous à MySQL :

```sql
CREATE DATABASE hospital_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'hospital_user'@'localhost' IDENTIFIED BY 'password123';
GRANT ALL PRIVILEGES ON hospital_db.* TO 'hospital_user'@'localhost';
FLUSH PRIVILEGES;
```

---

## Configuration

Créer un fichier **`.env`** à la racine du projet :

```
FLASK_ENV=development
SECRET_KEY=une_clef_ultra_secrete
SQLALCHEMY_DATABASE_URI=mysql+pymysql://hospital_user:password123@localhost/hospital_db
```

---

## Initialiser la base de données

Appliquer les migrations pour créer les tables :

```bash
flask db init     # une seule fois
flask db migrate -m "Initial migration"
flask db upgrade
```

---

## ▶️ Lancer l’application

```bash
flask run
```

ou

```bash
python run.py
```

L’application sera accessible sur :
👉 [http://127.0.0.1:5003](http://127.0.0.1:5003)

---

## Comptes par défaut

* **Administrateur** : `admin@hopital.com` / `admin123`
* **Médecin test** : `jean.dupont@hopital.com` / `medecin123`

---

## Structure du projet

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

---

## Rôles utilisateurs

| Rôle               | Description                                           |
| ------------------ | ----------------------------------------------------- |
| **Patient**        | Prend des rendez-vous, consulte son dossier           |
| **Médecin**        | Gère ses créneaux, consulte sa file d’attente         |
| **Secrétaire**     | Gère les rendez-vous, la file d’attente, les patients |
| **Administrateur** | Gestion complète du système                           |

---

## Modèles de données

* **User** : Utilisateurs (patients, médecins, personnel)
* **Salle** : Salles de consultation
* **Creneau** : Créneaux horaires des médecins
* **RendezVous** : Rendez-vous pris par les patients
* **FileAttente** : Gestion de la file d’attente quotidienne

---

## API et Routes principales

### Authentification

* `GET/POST /login` : Connexion
* `GET /logout` : Déconnexion
* `GET/POST /register-patient` : Inscription patient

### Patients

* `GET /book-appointment` : Prise de rendez-vous
* `POST /confirm-appointment` : Confirmation rendez-vous
* `GET/POST /edit-profile` : Modification profil

### Médecins

* `GET/POST /add-slot` : Ajout de créneaux
* `GET /start-consultation/<id>` : Démarrer consultation
* `GET /end-consultation/<id>` : Terminer consultation

### Secrétariat / Administration

* `GET /queue-management` : File d’attente
* `GET /manage-patients` : Gestion patients
* `GET /manage-personnel` : Gestion personnel
* `GET /manage-rooms` : Gestion salles
* `GET /manage-appointments` : Gestion rendez-vous

### Base de données

Pour réinitialiser la base de données :
```python
from app import app, db
with app.app_context():
    db.drop_all()
    db.create_all()
```

---

## Contribution

Les contributions sont **les bienvenues** !

1. Forker le projet
2. Créer une branche (`git checkout -b feature/ma-fonctionnalite`)
3. Commit (`git commit -m "Ajout nouvelle fonctionnalité"`)
4. Push (`git push origin feature/ma-fonctionnalite`)
5. Ouvrir une **Pull Request**

---

## Roadmap (améliorations futures)

* [ ] Notifications email/SMS pour confirmation de rendez-vous
* [ ] Facturation et gestion des paiements
* [ ] Statistiques (consultations, absences, etc.)
* [ ] Téléconsultation (Zoom / Meet / Teams)
* [ ] Application mobile (React Native/ Flutter)

---

## Sécurité

* Mots de passe hashés (Werkzeug)
* Sessions sécurisées (Flask-Login)
* Validation des entrées utilisateur

---

## Déploiement en production

1. Mettre `DEBUG = False`
2. Utiliser une clé secrète robuste
3. Configurer un serveur WSGI (Gunicorn)
4. Utiliser un proxy inverse (Nginx)
5. Activer HTTPS

---

## Rôle des Fichiers du Projet

### Fichiers Racine

* **`README.md`**
  ➤ C'est le fichier de documentation principal du projet. Il fournit une vue d'ensemble de l'application, ses fonctionnalités, les instructions d'installation, de configuration, de démarrage, les comptes par défaut, la structure du projet, les rôles utilisateurs, les modèles de données, les routes principales, et des notes sur le développement et la sécurité.

* **`app.py`**
  ➤ C'est le cœur de l'application Flask. Il initialise l'application, la base de données (SQLAlchemy), et le gestionnaire de connexion (Flask-Login). Il définit tous les modèles de données (`User`, `Salle`, `Creneau`, `RendezVous`, `FileAttente`) et contient toutes les routes (URL) de l'application, gérant la logique métier, les interactions avec la base de données, et le rendu des templates HTML.

* **`run.py`**
  ➤ Ce script est le point d'entrée recommandé pour lancer l'application. Il initialise la base de données en créant toutes les tables si elles n'existent pas, puis il crée des données par défaut (utilisateur administrateur, médecin de test, salles) pour faciliter le démarrage et les tests. Enfin, il démarre le serveur Flask.

* **`config.py`**
  ➤ Contient les classes de configuration (développement, production, test), gère la clé secrète et la connexion MySQL via les variables d’environnement.

* **`.env`**
  ➤ C'est un fichier qui montre les variables d'environnement nécessaires au fonctionnement de l'application, permettant de stocker les informations sensibles (comme les identifiants de base de données et la clé secrète) en dehors du code source.

---

### Fichiers Statiques

* **`static/css/style.css`**
  ➤ Contient les styles CSS personnalisés de l'application. Il permet de modifier l'apparence des éléments HTML au-delà de ce que Bootstrap fournit par défaut, assurant une cohérence visuelle et une personnalisation de l'interface utilisateur.

---

### Templates HTML (`hopital/templates/`)

#### **Layouts**

* **`layouts/base.html`**
  ➤ Template de base pour toutes les pages. Contient le header, footer, structure globale, et blocs Jinja2 pour les pages enfants.

#### **Administration / Secrétariat (`admin_secretariat/`)**

* `dashboard.html` → Affiche le tableau de bord principal pour les utilisateurs ayant les rôles 'secretaire' ou 'admin'. Il présente des liens rapides vers les différentes sections de gestion (personnel, patients, salles, rendez-vous, file d'attente).
* `manage_appointments.html` → Permet aux administrateurs et secrétaires de visualiser, filtrer, exporter, ajouter, modifier et annuler tous les rendez-vous du système. Il inclut un tableau listant les rendez-vous et une modale pour en créer de nouveaux.
* `manage_patients.html` → Affiche la liste de tous les patients enregistrés. Il permet de rechercher des patients, d'exporter la liste et d'accéder à leur dossier simplifié.
* `manage_personnel.html` → Permet aux administrateurs de gérer le personnel (médecins, secrétaires, autres administrateurs). Il affiche une liste du personnel avec leurs rôles et spécialités, et offre des options pour ajouter ou modifier des membres.
* `manage_rooms.html` → Permet aux administrateurs et secrétaires de gérer les salles de consultation. Il affiche l'état des salles (disponible/occupée), les médecins assignés, et offre la possibilité d'ajouter ou de supprimer des salles.
* `queue_management.html` → Gère la file d'attente des patients pour la journée en cours. Il organise les patients par médecin et permet au personnel administratif de changer le statut des patients (appeler, terminer consultation, marquer absent).
* `edit_personnel.html` → Formulaire utilisé pour ajouter un nouveau membre du personnel ou modifier les informations d'un membre existant. Il adapte les champs affichés en fonction du rôle (par exemple, spécialité et salle pour un médecin).

#### **Médecin (`medecin/`)**

* `dashboard.html` → Tableau de bord spécifique aux médecins. Il affiche la liste des patients à consulter pour la journée, permet de gérer les créneaux horaires (ajouter, supprimer) et de consulter l'historique des consultations passées.
* `add_slot.html` → Gestion des créneaux de disponibilité.
* `patient_dossier.html` → Consultation du dossier simplifié d’un patient.

#### **Patient (`patient/`)**

* `dashboard.html` → Tableau de bord patient (rendez-vous, profil).
* `appointment_booking.html` → Prise de rendez-vous en ligne.
* `edit_profile.html` → Modification des informations personnelles.

#### **Authentification (`auth/`)**

* `login.html` → Page de connexion.
* `register_patient.html` → Page d’inscription des patients.

---

## Licence

Projet open-source sous licence **MIT**.
Vous êtes libre de l’utiliser, le modifier et le redistribuer.
