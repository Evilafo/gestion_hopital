from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, time, timedelta
from sqlalchemy.orm import aliased # Import aliased for complex joins
import os
from config import config # Import the configuration object

app = Flask(__name__, template_folder='hopital/templates', static_folder='static')

# Configuration de l'application
# Load configuration based on FLASK_ENV or default to development
app_env = os.environ.get('FLASK_ENV', 'default')
app.config.from_object(config[app_env])

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Modèles de base de données
class User(UserMixin, db.Model):
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

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def age(self):
        if self.date_naissance:
            today = date.today()
            return today.year - self.date_naissance.year - ((today.month, today.day) < (self.date_naissance.month, self.date_naissance.day))
        return None

class Salle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), nullable=False, unique=True)
    nom = db.Column(db.String(100))
    disponible = db.Column(db.Boolean, default=True)
    medecins = db.relationship('User', backref='salle_ref')

class Creneau(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medecin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    heure_debut = db.Column(db.Time, nullable=False)
    heure_fin = db.Column(db.Time, nullable=False)
    disponible = db.Column(db.Boolean, default=True)
    medecin = db.relationship('User', backref='creneaux')

class RendezVous(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    medecin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creneau_id = db.Column(db.Integer, db.ForeignKey('creneau.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    heure = db.Column(db.Time, nullable=False)
    statut = db.Column(db.String(50), default='Confirmé')  # Confirmé, Annulé, Terminé
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    patient = db.relationship('User', foreign_keys=[patient_id], backref='rendez_vous_patient')
    medecin = db.relationship('User', foreign_keys=[medecin_id], backref='rendez_vous_medecin')
    creneau = db.relationship('Creneau', backref='rendez_vous')

class FileAttente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rendez_vous_id = db.Column(db.Integer, db.ForeignKey('rendez_vous.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    medecin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    heure_rendezvous = db.Column(db.Time, nullable=False)
    statut_file = db.Column(db.String(50), default='En Attente')  # En Attente, En Consultation, Terminé, Absent
    ordre = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    rendez_vous = db.relationship('RendezVous', backref='file_attente')
    patient = db.relationship('User', foreign_keys=[patient_id], backref='files_attente_patient')
    medecin = db.relationship('User', foreign_keys=[medecin_id], backref='files_attente_medecin')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes principales
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('layouts/base.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(email=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Identifiants incorrects', 'danger')
    
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register-patient', methods=['GET', 'POST'])
def register_patient():
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        email = request.form['email']
        password = request.form['password']
        contact = request.form['contact']
        date_naissance = datetime.strptime(request.form['date_naissance'], '%Y-%m-%d').date()
        
        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé', 'danger')
            return render_template('auth/register_patient.html')
        
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
    if current_user.role == 'patient':
        # Récupérer les rendez-vous avec les informations du médecin
        upcoming_appointments = []
        rdvs = RendezVous.query.filter(
            RendezVous.patient_id == current_user.id,
            RendezVous.date >= date.today(),
            RendezVous.statut == 'Confirmé'
        ).order_by(RendezVous.date, RendezVous.heure).all()
        
        for rdv in rdvs:
            medecin = User.query.get(rdv.medecin_id)
            # Créer un objet temporaire avec les bonnes propriétés
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
        today = date.today()
        
        # Récupérer les patients du jour
        fa_query = FileAttente.query.filter(
            FileAttente.medecin_id == current_user.id,
            FileAttente.date == today
        ).order_by(FileAttente.heure_rendezvous).all()
        
        today_patients = []
        for fa in fa_query:
            patient = User.query.get(fa.patient_id)
            patient_data = type('obj', (object,), {
                'id': fa.id,
                'patient_id': fa.patient_id,
                'patient_nom': f"{patient.prenom} {patient.nom}",
                'heure_rendezvous': fa.heure_rendezvous,
                'statut_file': fa.statut_file
            })
            today_patients.append(patient_data)
        
        future_slots = Creneau.query.filter(
            Creneau.medecin_id == current_user.id,
            Creneau.date >= today
        ).order_by(Creneau.date, Creneau.heure_debut).all()
        
        # Récupérer les rendez-vous passés
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
        # Statistiques pour le secrétariat
        return render_template('admin_secretariat/dashboard.html')
    
    return redirect(url_for('login'))

# Routes pour la gestion des patients
@app.route('/book-appointment')
@login_required
def book_appointment():
    if current_user.role != 'patient':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    
    specialities = db.session.query(User.specialite).filter(
        User.role == 'medecin',
        User.specialite.isnot(None)
    ).distinct().all()
    specialities = [s[0] for s in specialities]
    
    selected_speciality = request.args.get('speciality')
    selected_doctor_id = request.args.get('doctor_id')
    selected_doctor = None
    doctors_by_speciality = []
    available_slots = []
    
    if selected_speciality:
        doctors_by_speciality = User.query.filter_by(role='medecin', specialite=selected_speciality).all()
    
    if selected_doctor_id:
        selected_doctor = User.query.get(selected_doctor_id)
        if selected_doctor and selected_doctor.role == 'medecin':
            # Récupérer les créneaux disponibles
            available_slots = Creneau.query.filter(
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
    if current_user.role != 'patient':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    
    slot_id = request.form['slot_id']
    slot = Creneau.query.get(slot_id)
    
    if not slot or not slot.disponible:
        flash('Ce créneau n\'est plus disponible', 'danger')
        return redirect(url_for('book_appointment'))
    
    # Créer le rendez-vous
    rv = RendezVous(
        patient_id=current_user.id,
        medecin_id=slot.medecin_id,
        creneau_id=slot.id,
        date=slot.date,
        heure=slot.heure_debut,
        statut='Confirmé'
    )
    
    slot.disponible = False
    db.session.add(rv)
    db.session.commit()
    
    # Ajouter à la file d'attente
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
    rv = RendezVous.query.get(rv_id)
    if rv and rv.patient_id == current_user.id:
        rv.statut = 'Annulé'
        rv.creneau.disponible = True
        
        # Mettre à jour la file d'attente
        fa = FileAttente.query.filter_by(rendez_vous_id=rv_id).first()
        if fa:
            fa.statut_file = 'Annulé'
        
        db.session.commit()
        flash('Rendez-vous annulé', 'success')
    
    return redirect(url_for('dashboard'))

@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if current_user.role != 'patient':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        current_user.nom = request.form['nom']
        current_user.prenom = request.form['prenom']
        current_user.contact = request.form['contact']
        
        if request.form['date_naissance']:
            current_user.date_naissance = datetime.strptime(request.form['date_naissance'], '%Y-%m-%d').date()
        
        # Gérer le changement de mot de passe
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        if password:
            if password != password_confirm:
                flash('Les mots de passe ne correspondent pas.', 'danger')
                return redirect(url_for('edit_profile'))
            current_user.set_password(password)

        db.session.commit()
        flash('Profil mis à jour', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('patient/edit_profile.html')

# Routes pour les médecins
@app.route('/add-slot', methods=['GET', 'POST'])
@login_required
def add_slot():
    if current_user.role != 'medecin':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        date_slot = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        heure_debut = datetime.strptime(request.form['heure_debut'], '%H:%M').time()
        heure_fin = datetime.strptime(request.form['heure_fin'], '%H:%M').time()
        
        # Vérifier les conflits
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
    slot = Creneau.query.get(slot_id)
    if slot and slot.medecin_id == current_user.id and slot.disponible:
        db.session.delete(slot)
        db.session.commit()
        flash('Créneau supprimé', 'success')
    
    return redirect(url_for('dashboard'))

@app.route('/start-consultation/<int:queue_id>')
@login_required
def start_consultation(queue_id):
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

# Routes pour le secrétariat
@app.route('/queue-management')
@login_required
def queue_management():
    if current_user.role not in ['secretaire', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    
    today = date.today()
    
    # Récupérer les médecins qui ont des patients aujourd'hui
    medecins_du_jour = db.session.query(User).filter(
        User.role == 'medecin',
        User.id.in_(
            db.session.query(FileAttente.medecin_id).filter(FileAttente.date == today)
        )
    ).all()
    
    # Organiser la file d'attente par médecin
    file_attente = {}
    for medecin in medecins_du_jour:
        patients = db.session.query(FileAttente, User).join(
            User, FileAttente.patient_id == User.id
        ).filter(
            FileAttente.medecin_id == medecin.id,
            FileAttente.date == today
        ).order_by(FileAttente.heure_rendezvous).all()
        
        file_attente[medecin.id] = [
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
    if current_user.role not in ['secretaire', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    
    fa = FileAttente.query.get(file_id)
    if fa:
        fa.statut_file = 'Absent'
        # Libérer le créneau
        fa.rendez_vous.creneau.disponible = True
        db.session.commit()
        flash('Patient marqué absent', 'info')
    
    return redirect(url_for('queue_management'))

# Routes pour la gestion du personnel (placeholders)
@app.route('/manage-personnel')
@login_required
def manage_personnel():
    if current_user.role not in ['admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    
    personnel = User.query.filter(User.role.in_(['medecin', 'secretaire', 'admin'])).all()
    return render_template('admin_secretariat/manage_personnel.html', personnel=personnel)

@app.route('/add-personnel', methods=['GET', 'POST'])
@login_required
def add_personnel():
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
    if current_user.role != 'admin':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))

    user_to_edit = User.query.get_or_404(user_id)

    if request.method == 'POST':
        # Vérifier si l'email a changé et s'il est unique
        new_email = request.form['email']
        if new_email != user_to_edit.email and User.query.filter_by(email=new_email).first():
            flash('Ce nouvel email est déjà utilisé.', 'danger')
            return redirect(request.url)

        user_to_edit.nom = request.form['nom']
        user_to_edit.prenom = request.form['prenom']
        user_to_edit.email = new_email
        user_to_edit.contact = request.form.get('contact')
        
        # Ne pas permettre de changer le rôle d'un admin pour éviter de se bloquer
        if user_to_edit.role != 'admin':
            user_to_edit.role = request.form['role']

        if user_to_edit.role == 'medecin':
            user_to_edit.specialite = request.form.get('specialite')
            user_to_edit.salle_id = request.form.get('salle_id') if request.form.get('salle_id') else None
        else:
            user_to_edit.specialite = None
            user_to_edit.salle_id = None

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
    if current_user.role not in ['secretaire', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    
    patients = User.query.filter_by(role='patient').all()
    return render_template('admin_secretariat/manage_patients.html', patients=patients)

@app.route('/edit-patient/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def edit_patient(patient_id):
    if current_user.role not in ['secretaire', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))

    patient = User.query.get_or_404(patient_id)
    if patient.role != 'patient':
        flash('Utilisateur non valide.', 'danger')
        return redirect(url_for('manage_patients'))

    if request.method == 'POST':
        patient.nom = request.form['nom']
        patient.prenom = request.form['prenom']
        patient.contact = request.form['contact']
        if request.form['date_naissance']:
            patient.date_naissance = datetime.strptime(request.form['date_naissance'], '%Y-%m-%d').date()
        
        if request.form.get('password'):
            patient.set_password(request.form['password'])

        db.session.commit()
        flash('Les informations du patient ont été mises à jour.', 'success')
        return redirect(url_for('manage_patients'))

    return render_template('admin_secretariat/edit_patient.html', patient=patient)

@app.route('/manage-rooms')
@login_required
def manage_rooms():
    if current_user.role not in ['secretaire', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    
    salles = Salle.query.all()
    return render_template('admin_secretariat/manage_rooms.html', salles=salles)

@app.route('/manage-appointments')
@login_required
def manage_appointments():
    if current_user.role not in ['secretaire', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    
    Patient = aliased(User)
    Medecin = aliased(User)

    # Récupérer les rendez-vous avec les informations des patients et médecins
    appointments = db.session.query(
        RendezVous,
        db.func.concat(Patient.prenom, ' ', Patient.nom).label('patient_nom'),
        db.func.concat(Medecin.prenom, ' ', Medecin.nom).label('medecin_nom')
    ).join(Patient, RendezVous.patient_id == Patient.id
    ).join(Medecin, RendezVous.medecin_id == Medecin.id
    ).order_by(RendezVous.date.desc(), RendezVous.heure.desc()).all()
    
    return render_template('admin_secretariat/manage_appointments.html', appointments=appointments)

@app.route('/view-patient-dossier/<int:patient_id>')
@login_required
def view_patient_dossier(patient_id):
    if current_user.role not in ['medecin', 'secretaire', 'admin']:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    
    patient = User.query.get(patient_id)
    if not patient or patient.role != 'patient':
        flash('Patient non trouvé', 'danger')
        return redirect(url_for('dashboard'))
    
    # Récupérer l'historique des rendez-vous
    Medecin = aliased(User)
    historique = db.session.query(RendezVous, Medecin).join(
        Medecin, RendezVous.medecin_id == Medecin.id
    ).filter(RendezVous.patient_id == patient_id
    ).order_by(RendezVous.date.desc()).all()
    
    return render_template('medecin/patient_dossier.html', patient=patient, historique=historique)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Créer quelques données de test si nécessaire
        if User.query.filter_by(role='admin').count() == 0:
            admin = User(
                nom='Admin', prenom='Système', email='admin@hopital.com',
                role='admin', contact='0000000000'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
    
    app.run(debug=True)
