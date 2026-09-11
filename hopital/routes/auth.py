from datetime import datetime
from urllib.parse import quote
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, login_required, logout_user, current_user
from hopital.extensions import db, limiter
from hopital.models import User
from hopital.services.patient_service import PatientService
from hopital.middleware import rate_limit_login, rate_limit_register
from hopital.security import PasswordValidator


def register_routes(app):
    """Enregistre les routes d'authentification"""
    
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        specialites = db.session.query(User.specialite).filter(
            User.role == 'medecin', User.specialite.isnot(None)
        ).distinct().all()
        return render_template('layouts/home.html', specialites=[s[0] for s in specialites])

    @app.route('/login', methods=['GET', 'POST'])
    @rate_limit_login
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            user = User.query.filter_by(email=username).first()
            if user and user.compte_web and user.check_password(password):
                login_user(user)
                return redirect(url_for('dashboard'))
            flash('Identifiants incorrects', 'danger')
        return render_template('auth/login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route('/register-patient', methods=['GET', 'POST'])
    @rate_limit_register
    def register_patient():
        if request.method == 'POST':
            nom = request.form['nom'].strip()
            prenom = request.form['prenom'].strip()
            email = request.form['email'].strip()
            password = request.form['password']
            contact = request.form['contact'].strip()
            
            # Valider le mot de passe
            is_valid, error_msg = PasswordValidator.validate(password)
            if not is_valid:
                flash(error_msg, 'danger')
                return render_template('auth/register_patient.html')
            
            try:
                date_naissance = datetime.strptime(request.form['date_naissance'], '%Y-%m-%d').date()
            except ValueError:
                flash('Date de naissance invalide', 'danger')
                return render_template('auth/register_patient.html')

            if User.query.filter_by(email=email).first():
                flash('Cet email est déjà utilisé', 'danger')
                return render_template('auth/register_patient.html')

            user = User(
                nom=nom, prenom=prenom, email=email,
                contact=contact, date_naissance=date_naissance,
                role='patient', compte_web=True
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            PatientService.ensure_patient_profile(user)

            # Générer le lien WhatsApp avec les identifiants
            whatsapp_link = None
            if contact:
                # Nettoyer le numéro de téléphone (enlever espaces, tirets, etc.)
                clean_phone = contact.replace(' ', '').replace('-', '').replace('.', '')
                # S'assurer que le numéro commence par + pour le format international
                if not clean_phone.startswith('+'):
                    clean_phone = '+33' + clean_phone.lstrip('0')  # Format français par défaut
                # Créer le message avec les identifiants
                message = f"Bonjour {prenom}, votre compte a été créé avec succès.\n\nEmail: {email}\nMot de passe: {password}\n\nVous pouvez vous connecter sur: {request.host_url}"
                encoded_message = quote(message)
                whatsapp_link = f"https://wa.me/{clean_phone}?text={encoded_message}"

            flash('Inscription réussie ! Vous pouvez maintenant vous connecter.', 'success')
            return render_template('auth/register_patient.html', whatsapp_link=whatsapp_link, new_user_email=email, new_user_password=password)
        return render_template('auth/register_patient.html')
