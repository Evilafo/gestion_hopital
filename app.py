from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, time, timedelta
from sqlalchemy.orm import aliased # Import aliased for complex joins
import os
import pandas as pd
import io
from config import config # Import the configuration object
# --- Initialisation de l'application Flask ---
app = Flask(__name__, template_folder='hopital/templates', static_folder='static')

# --- Configuration ---
# Charge la configuration appropriée (développement, production) en fonction de la variable d'environnement FLASK_ENV.
# Si FLASK_ENV n'est pas définie, la configuration par défaut ('development') est utilisée.
app_env = os.environ.get('FLASK_ENV')
app.config.from_object(config[app_env])

# --- Initialisation de la base de données ---
db = SQLAlchemy(app)

# --- Gestion de la connexion des utilisateurs (Login) ---
login_manager = LoginManager()
login_manager.init_app(app)
# 'login_view' est la route vers laquelle les utilisateurs non connectés sont redirigés
# lorsqu'ils essaient d'accéder à une page protégée.
login_manager.login_view = 'login'

# --- Modèles de base de données (SQLAlchemy ORM) ---
# Chaque classe représente une table dans la base de données.

class User(UserMixin, db.Model):
    """Modèle pour les utilisateurs (patients, médecins, secrétaires, admins)."""
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'patient', 'medecin', 'secretaire', 'admin'
    contact = db.Column(db.String(20))
    date_naissance = db.Column(db.Date)
    specialite = db.Column(db.String(100))  # Pour les médecins
    salle_id = db.Column(db.Integer, db.ForeignKey('salle.id'))  # Pour les médecins
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Méthode pour hasher le mot de passe avant de le stocker
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    # Méthode pour vérifier si le mot de passe fourni correspond au hash stocké
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # Propriété calculée pour obtenir l'âge de l'utilisateur
    @property
    def age(self):
        if self.date_naissance:
            today = date.today()
            return today.year - self.date_naissance.year - ((today.month, today.day) < (self.date_naissance.month, self.date_naissance.day))
        return None

class Salle(db.Model):
    """Modèle pour les salles de consultation."""
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), nullable=False, unique=True)
    nom = db.Column(db.String(100))
    disponible = db.Column(db.Boolean, default=True)
    medecins = db.relationship('User', backref='salle_ref')

class Creneau(db.Model):
    """Modèle pour les créneaux horaires disponibles des médecins."""
    id = db.Column(db.Integer, primary_key=True)
    medecin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    heure_debut = db.Column(db.Time, nullable=False)
    heure_fin = db.Column(db.Time, nullable=False)
    disponible = db.Column(db.Boolean, default=True)
    medecin = db.relationship('User', backref='creneaux')

class RendezVous(db.Model):
    """Modèle pour les rendez-vous pris par les patients."""
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    medecin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creneau_id = db.Column(db.Integer, db.ForeignKey('creneau.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    heure = db.Column(db.Time, nullable=False)
    statut = db.Column(db.String(50), default='Confirmé')  # Confirmé, Annulé, Terminé
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations pour accéder facilement aux objets User et Creneau liés
    patient = db.relationship('User', foreign_keys=[patient_id], backref='rendez_vous_patient')
    medecin = db.relationship('User', foreign_keys=[medecin_id], backref='rendez_vous_medecin')
    creneau = db.relationship('Creneau', backref='rendez_vous')

class FileAttente(db.Model):
    """Modèle pour gérer la file d'attente des patients le jour de leur rendez-vous."""
    id = db.Column(db.Integer, primary_key=True)
    rendez_vous_id = db.Column(db.Integer, db.ForeignKey('rendez_vous.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    medecin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    heure_rendezvous = db.Column(db.Time, nullable=False)
    statut_file = db.Column(db.String(50), default='En Attente')  # En Attente, En Consultation, Terminé, Absent
    ordre = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations pour accéder facilement aux objets liés
    rendez_vous = db.relationship('RendezVous', backref='file_attente')
    patient = db.relationship('User', foreign_keys=[patient_id], backref='files_attente_patient')
    medecin = db.relationship('User', foreign_keys=[medecin_id], backref='files_attente_medecin')

# --- Chargement de l'utilisateur ---
@login_manager.user_loader
def load_user(user_id):
    """Fonction utilisée par Flask-Login pour récupérer un utilisateur à partir de son ID stocké en session."""
    return User.query.get(int(user_id))

# --- Routes de l'application ---

@app.route('/')
def index():
    """Page d'accueil. Redirige vers le tableau de bord si l'utilisateur est connecté."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('layouts/base.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion des utilisateurs."""
    if request.method == 'POST':
        # Récupération des données du formulaire
        username = request.form['username']
        password = request.form['password']
        
        # Recherche de l'utilisateur dans la base de données par email
        user = User.query.filter_by(email=username).first()
        # Vérification du mot de passe et connexion de l'utilisateur
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Identifiants incorrects', 'danger')
    
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    """Déconnexion de l'utilisateur."""
    logout_user()
    return redirect(url_for('login'))

@app.route('/register-patient', methods=['GET', 'POST'])
def register_patient():
    """Page d'inscription pour les nouveaux patients."""
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        email = request.form['email']
        password = request.form['password']
        contact = request.form['contact']
        date_naissance = datetime.strptime(request.form['date_naissance'], '%Y-%m-%d').date()
        
        # Vérifie si l'email n'est pas déjà utilisé
        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé', 'danger')
            return render_template('auth/register_patient.html')
        
        # Création du nouvel utilisateur avec le rôle 'patient'
        user = User(
            nom=nom, prenom=prenom, email=email, 
            contact=contact, date_naissance=date_naissance, role='patient'
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Inscription réussie ! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register_patient.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Affiche le tableau de bord approprié en fonction du rôle de l'utilisateur connecté."""
    if current_user.role == 'patient':
        # --- Dashboard Patient ---
        # Récupère les rendez-vous à venir du patient
        upcoming_appointments = []
        rdvs = RendezVous.query.filter(
            RendezVous.patient_id == current_user.id,
            RendezVous.date >= date.today(),
            RendezVous.statut == 'Confirmé'
        ).order_by(RendezVous.date, RendezVous.heure).all()
        
        for rdv in rdvs:
            medecin = User.query.get(rdv.medecin_id)
            # Crée un objet temporaire pour passer les données au template de manière propre
            appointment_data = type('obj', (object,), {
                'id': rdv.id,
                'date': rdv.date,
                'heure': rdv.heure,
                'statut': rdv.statut,
                'medecin_nom': f"{medecin.nom} {medecin.prenom}",
                'specialite': medecin.specialite or 'Non spécifiée'
            })
            upcoming_appointments.append(appointment_data)
        
        return render_template('patient/dashboard.html', upcoming_appointments=upcoming_appointments)
    
    elif current_user.role == 'medecin':
        # --- Dashboard Médecin ---
        today = date.today()
        
        # Récupère les patients dans la file d'attente pour aujourd'hui
        fa_query = FileAttente.query.filter(
            FileAttente.medecin_id == current_user.id,
            FileAttente.date == today
        ).order_by(FileAttente.heure_rendezvous).all()
        
        today_patients = []
        for fa in fa_query:
            patient = User.query.get(fa.patient_id)
            # Crée un objet temporaire pour le template
            patient_data = type('obj', (object,), {
                'id': fa.id,
                'patient_id': fa.patient_id,
                'patient_nom': f"{patient.prenom} {patient.nom}",
                'heure_rendezvous': fa.heure_rendezvous,
                'statut_file': fa.statut_file
            })
            today_patients.append(patient_data)
        
        # Récupère les futurs créneaux disponibles
        future_slots = Creneau.query.filter(
            Creneau.medecin_id == current_user.id,
            Creneau.date >= today
        ).order_by(Creneau.date, Creneau.heure_debut).all()
        
        # Récupère les 10 derniers rendez-vous passés
        past_rdvs = RendezVous.query.filter(
            RendezVous.medecin_id == current_user.id,
            RendezVous.date < today
        ).order_by(RendezVous.date.desc()).limit(10).all()
        
        past_appointments = []
        for rdv in past_rdvs:
            patient = User.query.get(rdv.patient_id)
            past_data = type('obj', (object,), {
                'date': rdv.date,
                'patient_nom': f"{patient.prenom} {patient.nom}"
            })
            past_appointments.append(past_data)
        
        return render_template('medecin/dashboard.html', 
                             today_patients=today_patients,
                             future_slots=future_slots,
                             past_appointments=past_appointments,
                             date_du_jour=today)
    
    elif current_user.role in ['secretaire', 'admin']:
        # --- Dashboard Secrétaire/Admin ---
        # Affiche le tableau de bord principal avec les liens de gestion
        return render_template('admin_secretariat/dashboard.html')
    
    return redirect(url_for('login'))

# --- Routes pour les Patients ---

@app.route('/book-appointment')
@login_required
def book_appointment():
    """Page de prise de rendez-vous pour les patients."""
    if current_user.role != 'patient':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    
    # 1. Récupère la liste de toutes les spécialités médicales disponibles
    specialities_query = db.session.query(User.specialite).filter(
        User.role == 'medecin',
        User.specialite.isnot(None)
    ).distinct().all()
    specialities = [s[0] for s in specialities]
    
    selected_speciality = request.args.get('speciality')
    selected_doctor_id = request.args.get('doctor_id')
    selected_doctor = None
    doctors_by_speciality = []
    available_slots = []
    
    # 2. Si une spécialité est sélectionnée, récupère les médecins correspondants
    if selected_speciality:
        doctors_by_speciality = User.query.filter_by(role='medecin', specialite=selected_speciality).all()
    
    # 3. Si un médecin est sélectionné, récupère ses créneaux disponibles
    if selected_doctor_id:
        selected_doctor = User.query.get(selected_doctor_id)
        if selected_doctor and selected_doctor.role == 'medecin':
            available_slots = Creneau.query.filter(
                # Le créneau appartient au bon médecin
                Creneau.medecin_id == selected_doctor_id,
                Creneau.date >= date.today(),
                Creneau.disponible == True
            ).order_by(Creneau.date, Creneau.heure_debut).all()
    
    return render_template('patient/appointment_booking.html',
                         specialities=specialities,
                         selected_speciality=selected_speciality,
                         doctors_by_speciality=doctors_by_speciality,
                         selected_doctor=selected_doctor,
                         available_slots=available_slots)

@app.route('/confirm-appointment', methods=['POST'])
@login_required
def confirm_appointment():
    """Confirme un rendez-vous à partir d'un créneau sélectionné."""
    if current_user.role != 'patient':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    
    slot_id = request.form['slot_id']
    slot = Creneau.query.get(slot_id)
    
    # Vérifie si le créneau est toujours valide et disponible
    if not slot or not slot.disponible:
        flash('Ce créneau n\'est plus disponible', 'danger')
        return redirect(url_for('book_appointment'))
    
    # Crée l'enregistrement du rendez-vous
    rv = RendezVous(
        patient_id=current_user.id,
        medecin_id=slot.medecin_id,
        creneau_id=slot.id,
        date=slot.date,
        heure=slot.heure_debut,
        statut='Confirmé'
    )
    
    # Marque le créneau comme non disponible
    slot.disponible = False
    db.session.add(rv)
    db.session.commit()
    
    # Ajoute automatiquement le patient à la file d'attente pour le jour du RDV
    file_attente = FileAttente(
        rendez_vous_id=rv.id,
        patient_id=current_user.id,
        medecin_id=slot.medecin_id,
        date=slot.date,
        heure_rendezvous=slot.heure_debut,
        statut_file='En Attente'
    )
    db.session.add(file_attente)
    db.session.commit()
    
    flash('Rendez-vous confirmé avec succès !', 'success')
    return redirect(url_for('dashboard'))

@app.route('/cancel-appointment/<int:rv_id>', methods=['POST'])
@login_required
def cancel_appointment(rv_id):
    """Permet à un patient d'annuler son propre rendez-vous."""
    rv = RendezVous.query.get(rv_id)
    if rv and rv.patient_id == current_user.id:
        rv.statut = 'Annulé'
        rv.creneau.disponible = True # Libère le créneau pour d'autres patients
        
        # Met également à jour le statut dans la file d'attente
        fa = FileAttente.query.filter_by(rendez_vous_id=rv.id).first()
        if fa:
            fa.statut_file = 'Annulé'
        
        db.session.commit()
        flash('Rendez-vous annulé', 'success')
    
    return redirect(url_for('dashboard'))

@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Permet à un patient de modifier ses informations de profil."""
    if current_user.role != 'patient':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        current_user.nom = request.form['nom']
        current_user.prenom = request.form['prenom']
        current_user.contact = request.form['contact']
        
        if request.form['date_naissance']:
            current_user.date_naissance = datetime.strptime(request.form['date_naissance'], '%Y-%m-%d').date()
        
        db.session.commit()
        flash('Profil mis à jour', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('patient/edit_profile.html')

# --- Routes pour les Médecins ---

@app.route('/add-slot', methods=['GET', 'POST'])
@login_required
def add_slot():
    """Permet à un médecin d'ajouter de nouveaux créneaux de disponibilité."""
    if current_user.role != 'medecin':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        date_slot = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        heure_debut = datetime.strptime(request.form['heure_debut'], '%H:%M').time()
        heure_fin = datetime.strptime(request.form['heure_fin'], '%H:%M').time()
        
        # Vérifie si le nouveau créneau ne chevauche pas un créneau existant
        existing = Creneau.query.filter(
            Creneau.medecin_id == current_user.id,
            Creneau.date == date_slot,
            Creneau.heure_debut < heure_fin,
            Creneau.heure_fin > heure_debut
        ).first()
        
        if existing:
            flash('Conflit avec un créneau existant', 'danger')
        else:
            slot = Creneau(
                medecin_id=current_user.id,
                date=date_slot,
                heure_debut=heure_debut,
                heure_fin=heure_fin,
                disponible=True
            )
            db.session.add(slot)
            db.session.commit()
            flash('Créneau ajouté avec succès', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template('medecin/add_slot.html')

@app.route('/delete-slot/<int:slot_id>')
@login_required
def delete_slot(slot_id):
    """Permet à un médecin de supprimer un créneau (s'il est encore disponible)."""
    slot = Creneau.query.get(slot_id)
    if slot and slot.medecin_id == current_user.id and slot.disponible:
        db.session.delete(slot)
        db.session.commit()
        flash('Créneau supprimé', 'success')
    
    return redirect(url_for('dashboard'))

@app.route('/start-consultation/<int:queue_id>')
@login_required
def start_consultation(queue_id):
    """Permet à un médecin de marquer le début d'une consultation."""
    if current_user.role != 'medecin':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    
    fa = FileAttente.query.get(queue_id)
    if fa and fa.medecin_id == current_user.id:
        fa.statut_file = 'En Consultation'
        db.session.commit()
        flash('Consultation commencée', 'success')
    
    return redirect(url_for('dashboard'))

@app.route('/end-consultation/<int:queue_id>')
@login_required
def end_consultation(queue_id):
    """Permet à un médecin de marquer la fin d'une consultation."""
    if current_user.role != 'medecin':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    
    fa = FileAttente.query.get(queue_id)
    if fa and fa.medecin_id == current_user.id:
        fa.statut_file = 'Terminé'
        fa.rendez_vous.statut = 'Terminé'
        db.session.commit()
        flash('Consultation terminée', 'success')
    
    return redirect(url_for('dashboard'))

# --- Routes pour le Secrétariat et l'Administration ---

@app.route('/queue-management')
@login_required
def queue_management():
    """Affiche la file d'attente du jour, organisée par médecin."""
    if current_user.role not in ['secretaire', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    
    today = date.today()
    
    # 1. Récupère les médecins qui ont des rendez-vous prévus aujourd'hui
    medecins_du_jour = db.session.query(User).filter(
        User.role == 'medecin',
        User.id.in_(
            db.session.query(FileAttente.medecin_id).filter(FileAttente.date == today)
        )
    ).all()
    
    # 2. Organise la file d'attente dans un dictionnaire, avec l'ID du médecin comme clé
    file_attente = {}
    for medecin in medecins_du_jour:
        patients = db.session.query(FileAttente, User).join(
            User, FileAttente.patient_id == User.id
        ).filter(
            FileAttente.medecin_id == medecin.id,
            FileAttente.date == today
        ).order_by(FileAttente.heure_rendezvous).all()
        
        file_attente[medecin.id] = [
            # Crée un dictionnaire propre pour chaque patient dans la file d'attente
            {
                'id': fa.id,
                'patient_id': fa.patient_id,
                'patient_nom': f"{patient.prenom} {patient.nom}",
                'heure_rendezvous': fa.heure_rendezvous.strftime('%H:%M'),
                'statut': fa.statut_file
            }
            for fa, patient in patients
        ]
    
    return render_template('admin_secretariat/queue_management.html',
                         medecins_du_jour=medecins_du_jour,
                         file_attente=file_attente,
                         date_du_jour=today.strftime('%d/%m/%Y'))

@app.route('/call-patient/<int:file_id>')
@login_required
def call_patient(file_id):
    """Permet au secrétariat d'appeler un patient (change son statut à 'En Consultation')."""
    if current_user.role not in ['secretaire', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    
    fa = FileAttente.query.get(file_id)
    if fa:
        fa.statut_file = 'En Consultation'
        db.session.commit()
        flash('Patient appelé', 'success')
    
    return redirect(url_for('queue_management'))

@app.route('/finish-consultation/<int:file_id>')
@login_required
def finish_consultation(file_id):
    """Permet au secrétariat de marquer une consultation comme terminée."""
    if current_user.role not in ['secretaire', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    
    fa = FileAttente.query.get(file_id)
    if fa:
        fa.statut_file = 'Terminé'
        fa.rendez_vous.statut = 'Terminé'
        db.session.commit()
        flash('Consultation marquée comme terminée', 'success')
    
    return redirect(url_for('queue_management'))

@app.route('/mark-absent/<int:file_id>')
@login_required
def mark_absent(file_id):
    """Permet au secrétariat de marquer un patient comme absent."""
    if current_user.role not in ['secretaire', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    
    fa = FileAttente.query.get(file_id)
    if fa:
        fa.statut_file = 'Absent' # Change le statut dans la file d'attente
        # Libérer le créneau
        fa.rendez_vous.creneau.disponible = True
        db.session.commit()
        flash('Patient marqué absent', 'info')
    
    return redirect(url_for('queue_management'))

# --- Routes de Gestion (Admin) ---

@app.route('/manage-personnel')
@login_required
def manage_personnel():
    """Page pour gérer le personnel (médecins, secrétaires, admins). Réservé aux admins."""
    if current_user.role not in ['admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    
    personnel = User.query.filter(User.role.in_(['medecin', 'secretaire', 'admin'])).all()
    return render_template('admin_secretariat/manage_personnel.html', personnel=personnel)

# --- API Endpoints (pour le JavaScript côté client) ---

@app.route('/api/users-for-appointment')
@login_required
def api_users_for_appointment():
    """API pour fournir la liste des patients et médecins, utilisée par la modale d'ajout de RDV."""
    if current_user.role not in ['secretaire', 'admin']:
        return jsonify(error="Accès non autorisé"), 403

    patients = User.query.filter_by(role='patient').order_by(User.nom).all()
    medecins = User.query.filter_by(role='medecin').order_by(User.nom).all()

    patients_data = [{'id': p.id, 'text': f"{p.prenom} {p.nom}"} for p in patients]
    medecins_data = [{'id': m.id, 'text': f"Dr. {m.prenom} {m.nom} ({m.specialite})"} for m in medecins]

    return jsonify(patients=patients_data, medecins=medecins_data)

@app.route('/add-appointment-admin', methods=['POST'])
@login_required
def add_appointment_admin():
    """API pour permettre au secrétariat/admin d'ajouter un rendez-vous manuellement."""
    if current_user.role not in ['secretaire', 'admin']:
        return jsonify(error="Accès non autorisé"), 403

    data = request.get_json()
    patient_id = data.get('patient_id')
    medecin_id = data.get('medecin_id')
    rdv_date_str = data.get('date')
    rdv_heure_str = data.get('heure')

    if not all([patient_id, medecin_id, rdv_date_str, rdv_heure_str]):
        return jsonify(error="Données manquantes"), 400

    rdv_date = datetime.strptime(rdv_date_str, '%Y-%m-%d').date()
    rdv_heure = datetime.strptime(rdv_heure_str, '%H:%M').time()

    # Simplification : on crée un créneau et un rdv directement.
    # Dans une version plus avancée, il faudrait d'abord vérifier la disponibilité du médecin
    # et utiliser un créneau existant si possible.
    creneau = Creneau(
        medecin_id=medecin_id,
        date=rdv_date,
        heure_debut=rdv_heure,
        heure_fin=(datetime.combine(rdv_date, rdv_heure) + timedelta(minutes=30)).time(),
        disponible=False
    )
    db.session.add(creneau)
    db.session.flush() # 'flush' permet d'obtenir l'ID du créneau avant le 'commit' final

    rdv = RendezVous(
        patient_id=patient_id,
        medecin_id=medecin_id,
        creneau_id=creneau.id,
        date=rdv_date,
        heure=rdv_heure,
        statut='Confirmé'
    )
    db.session.add(rdv)
    db.session.commit()

    flash('Rendez-vous ajouté avec succès.', 'success')
    return jsonify(success=True, message="Rendez-vous ajouté")


@app.route('/add-personnel', methods=['GET', 'POST'])
@login_required
def add_personnel():
    """Page et logique pour ajouter un nouveau membre du personnel."""
    if current_user.role != 'admin':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form['email']
        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé.', 'danger')
            return redirect(request.url)

        user = User(
            nom=request.form['nom'],
            prenom=request.form['prenom'],
            email=email,
            role=request.form['role'],
            contact=request.form.get('contact'),
            specialite=request.form.get('specialite') if request.form['role'] == 'medecin' else None,
            salle_id=request.form.get('salle_id') if request.form['role'] == 'medecin' else None
        )
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        flash('Le membre du personnel a été ajouté avec succès.', 'success')
        return redirect(url_for('manage_personnel'))

    salles = Salle.query.all()
    return render_template('admin_secretariat/edit_personnel.html', action='Ajouter', salles=salles)

@app.route('/edit-personnel/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_personnel(user_id):
    """Page et logique pour modifier les informations d'un membre du personnel."""
    if current_user.role != 'admin':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))

    user_to_edit = User.query.get_or_404(user_id)

    if request.method == 'POST':
        # Vérifie si l'email a changé et s'il est déjà pris par un autre utilisateur
        new_email = request.form['email']
        if new_email != user_to_edit.email and User.query.filter_by(email=new_email).first():
            flash('Ce nouvel email est déjà utilisé.', 'danger')
            return redirect(request.url)

        user_to_edit.nom = request.form['nom']
        user_to_edit.prenom = request.form['prenom']
        user_to_edit.email = new_email
        user_to_edit.contact = request.form.get('contact')
        
        # Sécurité : ne pas permettre de changer le rôle d'un admin pour éviter de se bloquer hors du système
        if user_to_edit.role != 'admin':
            user_to_edit.role = request.form['role']

        if user_to_edit.role == 'medecin':
            user_to_edit.specialite = request.form.get('specialite')
            user_to_edit.salle_id = request.form.get('salle_id') if request.form.get('salle_id') else None
        else:
            user_to_edit.specialite = None
            user_to_edit.salle_id = None

        # Met à jour le mot de passe seulement s'il est fourni
        if request.form.get('password'):
            user_to_edit.set_password(request.form['password'])

        db.session.commit()
        flash('Les informations ont été mises à jour.', 'success')
        return redirect(url_for('manage_personnel'))

    salles = Salle.query.all()
    return render_template('admin_secretariat/edit_personnel.html', action='Modifier', user=user_to_edit, salles=salles)

@app.route('/manage-patients')
@login_required
def manage_patients():
    """Page pour afficher et gérer la liste de tous les patients."""
    if current_user.role not in ['secretaire', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    
    patients = User.query.filter_by(role='patient').all()
    return render_template('admin_secretariat/manage_patients.html', patients=patients)

@app.route('/export/patients')
@login_required
def export_patients():
    """Exporte la liste de tous les patients dans un fichier CSV."""
    if current_user.role not in ['secretaire', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))

    patients_query = User.query.filter_by(role='patient').all()
    
    data = []
    for patient in patients_query:
        data.append({
            'ID': patient.id,
            'Nom': patient.nom,
            'Prénom': patient.prenom,
            'Email': patient.email,
            'Téléphone': patient.contact,
            'Date de naissance': patient.date_naissance.strftime('%d/%m/%Y') if patient.date_naissance else '',
            'Âge': patient.age,
            'Inscrit le': patient.created_at.strftime('%d/%m/%Y %H:%M') if patient.created_at else ''
        })

    df = pd.DataFrame(data)
    # Crée un fichier CSV en mémoire
    output = io.StringIO()
    # 'sep=';'' est souvent mieux pour Excel en France
    # 'encoding='utf-8-sig'' assure la compatibilité avec les caractères spéciaux
    df.to_csv(output, index=False, sep=';', encoding='utf-8-sig')
    csv_data = output.getvalue()
    # Renvoie le CSV comme une réponse téléchargeable
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=export_patients_{date.today().isoformat()}.csv"}
    )

@app.route('/export/appointments')
@login_required
def export_appointments():
    """Exporte la liste de tous les rendez-vous dans un fichier CSV."""
    if current_user.role not in ['secretaire', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    # Utilise des alias pour joindre la table User deux fois (pour le patient et le médecin)
    # Utilise la même requête que la page de gestion pour la cohérence
    Patient = aliased(User, name='patient')
    Medecin = aliased(User, name='medecin')
    appointments_query = db.session.query(RendezVous, Patient, Medecin).join(Patient, RendezVous.patient_id == Patient.id).join(Medecin, RendezVous.medecin_id == Medecin.id).order_by(RendezVous.date.desc(), RendezVous.heure.desc()).all()

    data = []
    for rdv, patient, medecin in appointments_query:
        data.append({
            'ID RDV': rdv.id,
            'Date': rdv.date.strftime('%d/%m/%Y'),
            'Heure': rdv.heure.strftime('%H:%M'),
            'Patient': f"{patient.prenom} {patient.nom}",
            'Médecin': f"Dr. {medecin.prenom} {medecin.nom}",
            'Statut': rdv.statut,
            'Créé le': rdv.created_at.strftime('%d/%m/%Y %H:%M') if rdv.created_at else ''
        })
    df = pd.DataFrame(data)
    output = io.StringIO()
    df.to_csv(output, index=False, sep=';', encoding='utf-8-sig')
    csv_data = output.getvalue()
    return Response(csv_data, mimetype="text/csv", headers={"Content-disposition": f"attachment; filename=export_rendezvous_{date.today().isoformat()}.csv"})

@app.route('/add-room', methods=['POST'])
@login_required
def add_room():
    """API pour ajouter une nouvelle salle de consultation."""
    if current_user.role not in ['secretaire', 'admin']:
        return jsonify(error="Accès non autorisé"), 403
    
    data = request.get_json()
    numero = data.get('numero')
    nom = data.get('nom')

    if not numero:
        return jsonify(error="Le numéro de salle est requis."), 400

    if Salle.query.filter_by(numero=numero).first():
        return jsonify(error="Ce numéro de salle existe déjà."), 409

    salle = Salle(numero=numero, nom=nom)
    db.session.add(salle)
    db.session.commit()

    flash('Salle ajoutée avec succès.', 'success')
    return jsonify(success=True, message="Salle ajoutée")

@app.route('/delete-room/<int:room_id>', methods=['POST'])
@login_required
def delete_room(room_id):
    """API pour supprimer une salle de consultation."""
    if current_user.role not in ['secretaire', 'admin']:
        return jsonify(error="Accès non autorisé"), 403

    salle = Salle.query.get_or_404(room_id)

    # Sécurité : on ne peut supprimer une salle que si aucun médecin n'y est assigné
    if salle.medecins:
        return jsonify(error="Impossible de supprimer une salle assignée à un médecin."), 409

    db.session.delete(salle)
    db.session.commit()

    flash('Salle supprimée avec succès.', 'success')
    return jsonify(success=True, message="Salle supprimée")


@app.route('/manage-rooms')
@login_required
def manage_rooms():
    """Page pour afficher et gérer les salles de consultation."""
    if current_user.role not in ['secretaire', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    
    salles = Salle.query.all()
    return render_template('admin_secretariat/manage_rooms.html', salles=salles)

@app.route('/manage-appointments')
@login_required
def manage_appointments():
    """Page pour afficher et gérer tous les rendez-vous du système."""
    if current_user.role not in ['secretaire', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    
    # Crée des alias pour la table User pour pouvoir la joindre deux fois :
    # une fois pour le patient, une fois pour le médecin.
    Patient = aliased(User, name='patient')
    Medecin = aliased(User, name='medecin')
    # Récupérer les rendez-vous avec les informations des patients et médecins
    appointments = db.session.query(
        RendezVous,
        Patient,
        Medecin
    ).join(
        Patient, RendezVous.patient_id == Patient.id
    ).join(
        Medecin, RendezVous.medecin_id == Medecin.id
    ).order_by(RendezVous.date.desc(), RendezVous.heure.desc()).all()
    
    return render_template('admin_secretariat/manage_appointments.html', appointments=appointments)

@app.route('/admin/cancel-appointment/<int:appointment_id>', methods=['POST'])
@login_required
def admin_cancel_appointment(appointment_id):
    """API pour permettre au secrétariat/admin d'annuler n'importe quel rendez-vous."""
    if current_user.role not in ['secretaire', 'admin']:
        return jsonify(error="Accès non autorisé"), 403

    rdv = RendezVous.query.get_or_404(appointment_id)
    rdv.statut = 'Annulé'
    
    # Libérer le créneau
    if rdv.creneau: # Vérifie que le créneau existe
        rdv.creneau.disponible = True

    db.session.commit()
    flash('Le rendez-vous a été annulé.', 'success')
    return jsonify(success=True)


@app.route('/view-patient-dossier/<int:patient_id>')
@login_required
def view_patient_dossier(patient_id):
    """Affiche le dossier d'un patient, y compris son historique de rendez-vous."""
    if current_user.role not in ['medecin', 'secretaire', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    
    patient = User.query.get(patient_id)
    if not patient or patient.role != 'patient':
        flash('Patient non trouvé', 'danger')
        return redirect(url_for('dashboard'))
    
    # Récupère l'historique des rendez-vous du patient avec les informations du médecin
    historique = db.session.query(RendezVous, User).join(
        User, RendezVous.medecin_id == User.id
    ).filter(RendezVous.patient_id == patient_id).order_by(RendezVous.date.desc()).all()
    
    return render_template('medecin/patient_dossier.html', patient=patient, historique=historique)

# --- Bloc d'exécution principal ---
# Ce bloc ne s'exécute que si le script est lancé directement (ex: `python app.py`)
if __name__ == '__main__':
    with app.app_context():
        # Cette commande crée toutes les tables de base de données qui sont définies
        # dans les modèles SQLAlchemy (ex: User, Salle, RendezVous).
        # Elle ne recrée pas les tables si elles existent déjà.
        # C'est utile pour l'initialisation lors du premier lancement direct du fichier app.py.
        # Note : Dans ce projet, le script principal est run.py, qui fait la même chose.
        db.create_all()
        
        # Crée un utilisateur admin par défaut si aucun n'existe
        if User.query.filter_by(role='admin').count() == 0:
            admin = User(
                nom='Admin', prenom='Système', email='admin@hopital.com',
                role='admin', contact='0000000000'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
    
    # Lance le serveur de développement Flask
    app.run(debug=True)
