from datetime import date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from hopital.extensions import db, login_manager


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, index=True)
    contact = db.Column(db.String(20))
    date_naissance = db.Column(db.Date)
    specialite = db.Column(db.String(100))
    salle_id = db.Column(db.Integer, db.ForeignKey('salle.id'))
    compte_web = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=db.func.now())

    profil_patient = db.relationship('PatientProfil', backref='user', uselist=False, cascade='all, delete-orphan')
    
    __table_args__ = (
        db.Index('ix_user_email_role', 'email', 'role'),
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def age(self):
        if self.date_naissance:
            today = date.today()
            return today.year - self.date_naissance.year - (
                (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day)
            )
        return None

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"


class PatientProfil(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    numero_dossier = db.Column(db.String(40), unique=True)
    allergies = db.Column(db.Text)
    antecedents = db.Column(db.Text)
    notes_internes = db.Column(db.Text)


class Salle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), nullable=False, unique=True)
    nom = db.Column(db.String(100))
    disponible = db.Column(db.Boolean, default=True)
    medecins = db.relationship('User', backref='salle_ref')


class Creneau(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medecin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    heure_debut = db.Column(db.Time, nullable=False)
    heure_fin = db.Column(db.Time, nullable=False)
    disponible = db.Column(db.Boolean, default=True, index=True)
    medecin = db.relationship('User', backref='creneaux')
    
    __table_args__ = (
        db.Index('ix_creneau_date_disponible', 'date', 'disponible'),
        db.Index('ix_creneau_medecin_date', 'medecin_id', 'date'),
    )


class RendezVous(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    medecin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    creneau_id = db.Column(db.Integer, db.ForeignKey('creneau.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    heure = db.Column(db.Time, nullable=False)
    statut = db.Column(db.String(50), default='Confirmé', index=True)
    motif = db.Column(db.String(255))
    reminder_j1_sent = db.Column(db.Boolean, default=False)
    reminder_h2_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    patient = db.relationship('User', foreign_keys=[patient_id], backref='rendez_vous_patient')
    medecin = db.relationship('User', foreign_keys=[medecin_id], backref='rendez_vous_medecin')
    creneau = db.relationship('Creneau', backref='rendez_vous')
    note = db.relationship('NoteConsultation', backref='rendez_vous', uselist=False, cascade='all, delete-orphan')
    
    __table_args__ = (
        db.Index('ix_rendez_vous_date_statut', 'date', 'statut'),
        db.Index('ix_rendez_vous_patient_date', 'patient_id', 'date'),
        db.Index('ix_rendez_vous_medecin_date', 'medecin_id', 'date'),
    )


class FileAttente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rendez_vous_id = db.Column(db.Integer, db.ForeignKey('rendez_vous.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    medecin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    heure_rendezvous = db.Column(db.Time, nullable=False)
    statut_file = db.Column(db.String(50), default='Non arrivé', index=True)
    ordre = db.Column(db.Integer, index=True)
    
    __table_args__ = (
        db.Index('ix_file_attente_date_medecin', 'date', 'medecin_id'),
        db.Index('ix_file_attente_medecin_statut', 'medecin_id', 'statut_file'),
    )
    created_at = db.Column(db.DateTime, default=db.func.now())

    rendez_vous = db.relationship('RendezVous', backref='file_attente')
    patient = db.relationship('User', foreign_keys=[patient_id], backref='files_attente_patient')
    medecin = db.relationship('User', foreign_keys=[medecin_id], backref='files_attente_medecin')


class NoteConsultation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rendez_vous_id = db.Column(db.Integer, db.ForeignKey('rendez_vous.id'), unique=True, nullable=False)
    medecin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    motif = db.Column(db.Text)
    diagnostic = db.Column(db.Text)
    ordonnance = db.Column(db.Text)
    notes = db.Column(db.Text)
    document_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.now())


class JournalAcces(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(120), nullable=False)
    details = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.now(), index=True)

    utilisateur = db.relationship('User', foreign_keys=[user_id])
    
    __table_args__ = (
        db.Index('ix_journal_acces_user_created', 'user_id', 'created_at'),
    )


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
