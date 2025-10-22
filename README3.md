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

Vérifiez vos versions :

```bash
python --version
mysql --version
git --version
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
👉 [http://127.0.0.1:5000](http://127.0.0.1:5000)

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
* [ ] Téléconsultation (Zoom / Meet / Jitsi)
* [ ] Application mobile (Capacitor / Flutter)

---

## Sécurité

* Mots de passe hashés (Werkzeug)
* Sessions sécurisées (Flask-Login)
* Protection CSRF (à implémenter)
* Validation des entrées utilisateur

---

## Déploiement en production

1. Mettre `DEBUG = False`
2. Utiliser une clé secrète robuste
3. Configurer un serveur WSGI (Gunicorn)
4. Utiliser un proxy inverse (Nginx)
5. Activer HTTPS

---

## Licence

Projet open-source sous licence **MIT**.
Vous êtes libre de l’utiliser, le modifier et le redistribuer.

