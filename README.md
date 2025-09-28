# 📘 Hospital Management System (Flask + MySQL)

## 🚀 Description du projet

Ce projet est une application web de gestion d’hôpital développée avec **Flask (Python)**, **HTML/CSS/JS** et une **base de données MySQL**.

L’application permet de gérer :

* Les **patients** (inscription, dossier simplifié).
* Les **médecins** (spécialités, emploi du temps).
* Le **personnel** (secrétaires, administrateurs).
* Les **salles** de consultation.
* Les **créneaux horaires** disponibles.
* La **prise de rendez-vous** par les patients.
* La **file d’attente** le jour de la consultation.
* Un **dashboard d’administration** pour le secrétariat.

Ce projet est conçu comme un **prototype évolutif** : il peut être enrichi avec la facturation, les notifications (SMS/Email), la téléconsultation, ou encore des statistiques médicales.

---

## 📂 Structure du projet

```
hospital/
│
├── app/
│   ├── __init__.py        # Configuration Flask
│   ├── models.py          # Définition des modèles SQLAlchemy
│   ├── routes/            # Routes organisées par module
│   │    ├── auth.py
│   │    ├── patients.py
│   │    ├── doctors.py
│   │    ├── appointments.py
│   │    └── admin.py
│   ├── templates/         # Pages HTML (Jinja2)
│   │    ├── base.html
│   │    ├── index.html
│   │    ├── booking.html
│   │    └── dashboard.html
│   └── static/            # CSS, JS, images
│
├── migrations/            # Gestion des migrations (Flask-Migrate)
├── requirements.txt       # Dépendances Python
├── config.py              # Configuration (MySQL, secrets)
├── run.py                 # Point d’entrée de l’application
└── README.md              # Documentation du projet
```

---

## ⚙️ Prérequis

Avant de lancer le projet, assurez-vous d’avoir installé :

* [Python 3.10+](https://www.python.org/downloads/)
* [MySQL 8+](https://dev.mysql.com/downloads/)
* [Git](https://git-scm.com/)

Vérifiez les versions :

```bash
python --version
mysql --version
git --version
```

---

## 📦 Installation du projet

### 1. Cloner le dépôt

```bash
git clone https://github.com/<TON-UTILISATEUR>/hospital.git
cd hospital
```

### 2. Créer un environnement virtuel

```bash
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Créer la base MySQL

Connectez-vous à MySQL :

```sql
CREATE DATABASE hospital_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'hospital_user'@'localhost' IDENTIFIED BY 'password123';
GRANT ALL PRIVILEGES ON hospital_db.* TO 'hospital_user'@'localhost';
FLUSH PRIVILEGES;
```

---

## 🔑 Configuration

Créer un fichier **`.env`** à la racine :

```
FLASK_ENV=development
SECRET_KEY=une_clef_ultra_secrete
SQLALCHEMY_DATABASE_URI=mysql+pymysql://hospital_user:password123@localhost/hospital_db
```

---

## 🛠️ Initialiser la base de données

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

Ouvrez votre navigateur et allez sur :
👉 [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 👥 Utilisateurs & Rôles

* **Admin** : gestion globale (médecins, patients, salles, planning).
* **Secrétaire** : gestion des rendez-vous, file d’attente, accueil.
* **Médecin** : consultation de ses patients, mise à jour de l’agenda.
* **Patient** : réservation de créneaux en ligne.

---

## 📌 Fonctionnalités principales

✅ Gestion des patients (CRUD)
✅ Gestion des médecins et spécialités
✅ Gestion du personnel et rôles
✅ Gestion des salles
✅ Créneaux horaires par médecin
✅ Prise de rendez-vous par les patients
✅ File d’attente avec check-in/call-next
✅ Dashboard pour secrétaires et administrateurs

---

## 🌱 Roadmap (Améliorations futures)

* [ ] Notifications email/SMS pour confirmation de rendez-vous.
* [ ] Facturation et gestion des paiements.
* [ ] Statistiques (consultations par jour, taux d’absences).
* [ ] Téléconsultation via Zoom/Meet/Jitsi.
* [ ] Application mobile (Capacitor/Flutter).

---

## 🤝 Contribution

Les contributions sont les bienvenues !

1. Forker le projet
2. Créer une branche (`git checkout -b feature/ma-fonctionnalite`)
3. Commit (`git commit -m "Ajout nouvelle fonctionnalité"`)
4. Push (`git push origin feature/ma-fonctionnalite`)
5. Ouvrir une Pull Request

---

## 📝 Licence

Projet open-source sous licence **MIT**.
Vous êtes libre de l’utiliser, le modifier et le redistribuer.
