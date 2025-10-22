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
