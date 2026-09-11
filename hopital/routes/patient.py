from datetime import datetime, date, time, timedelta
from functools import wraps
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from sqlalchemy import or_
from hopital.extensions import db
from hopital.models import User, Creneau, RendezVous, FileAttente
from hopital.services.patient_service import PatientService
from hopital.services.appointment_service import AppointmentService
from hopital.services.queue_service import QueueService
from hopital.utils import week_dates


def role_required(*roles):
    """Décorateur pour vérifier les rôles utilisateur"""
    def decorator(fn):
        @wraps(fn)
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.role not in roles:
                flash('Accès non autorisé', 'danger')
                return redirect(url_for('dashboard'))
            return fn(*args, **kwargs)
        return wrapped
    return decorator


def _patient_dashboard():
    upcoming = RendezVous.query.options(joinedload(RendezVous.medecin)).filter(
        RendezVous.patient_id == current_user.id,
        RendezVous.date >= date.today(),
        RendezVous.statut == 'Confirmé'
    ).order_by(RendezVous.date, RendezVous.heure).all()
    past = RendezVous.query.options(joinedload(RendezVous.medecin)).filter(
        RendezVous.patient_id == current_user.id,
        or_(RendezVous.date < date.today(), RendezVous.statut.in_(['Terminé', 'Annulé']))
    ).order_by(RendezVous.date.desc()).limit(20).all()
    pos = QueueService.get_patient_position(current_user.id)
    return render_template(
        'patient/dashboard.html',
        upcoming_appointments=upcoming,
        past_appointments=past,
        position=pos
    )


def _booking_page(patient_id, for_staff):
    specialities = [s[0] for s in db.session.query(User.specialite).filter(
        User.role == 'medecin', User.specialite.isnot(None)
    ).distinct().all()]
    selected_speciality = request.args.get('speciality')
    selected_doctor_id = request.args.get('doctor_id', type=int)
    selected_day = request.args.get('day')
    selected_doctor = None
    doctors_by_speciality = []
    slots_by_day = {}
    available_slots = []
    patients = []
    if for_staff:
        q = request.args.get('q', '').strip()
        query = User.query.filter_by(role='patient')
        if q:
            like = f'%{q}%'
            query = query.filter(or_(
                User.nom.ilike(like), User.prenom.ilike(like),
                User.contact.ilike(like), User.email.ilike(like)
            ))
        patients = query.order_by(User.nom).limit(30).all()

    if selected_speciality:
        doctors_by_speciality = User.query.filter_by(
            role='medecin', specialite=selected_speciality
        ).all()
    if selected_doctor_id:
        selected_doctor = db.session.get(User, selected_doctor_id)
        if selected_doctor and selected_doctor.role == 'medecin':
            available_slots = Creneau.query.filter(
                Creneau.medecin_id == selected_doctor_id,
                Creneau.date >= date.today(),
                Creneau.disponible.is_(True)
            ).order_by(Creneau.date, Creneau.heure_debut).all()
            for slot in available_slots:
                slots_by_day.setdefault(slot.date, []).append(slot)
    selected_day_date = None
    day_slots = []
    if selected_day:
        try:
            selected_day_date = datetime.strptime(selected_day, '%Y-%m-%d').date()
            day_slots = slots_by_day.get(selected_day_date, [])
        except ValueError:
            selected_day_date = None
    return render_template(
        'patient/appointment_booking.html',
        specialities=specialities,
        selected_speciality=selected_speciality,
        doctors_by_speciality=doctors_by_speciality,
        selected_doctor=selected_doctor,
        slots_by_day=slots_by_day,
        day_slots=day_slots,
        selected_day=selected_day_date,
        for_staff=for_staff,
        patients=patients,
        selected_patient_id=patient_id,
        confirm_endpoint='confirm_appointment_staff' if for_staff else 'confirm_appointment'
    )


def _confirm_booking(patient_id, back_url):
    slot_id = request.values.get('slot_id', type=int)
    slot = None
    if slot_id:
        slot = Creneau.query.options(
            joinedload(Creneau.medecin).joinedload(User.salle_ref)
        ).filter_by(id=slot_id).first()
    if not slot:
        flash('Créneau introuvable', 'danger')
        return redirect(back_url)
    if request.method == 'POST':
        motif = request.form.get('motif', '').strip()
        rv, err = AppointmentService.book_slot(slot.id, patient_id, motif or None)
        if err:
            flash(err, 'danger')
            return redirect(back_url)
        flash('Rendez-vous confirmé avec succès !', 'success')
        return redirect(url_for('manage_appointments') if current_user.role in ['secretaire', 'admin'] else url_for('dashboard'))
    return render_template(
        'patient/appointment_confirm.html',
        slot=slot,
        patient=db.session.get(User, patient_id),
        back_url=back_url
    )


def register_routes(app):
    """Enregistre les routes patients"""
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        if current_user.role == 'patient':
            return _patient_dashboard()
        if current_user.role == 'medecin':
            return redirect(url_for('medecin.dashboard'))
        if current_user.role in ['secretaire', 'admin']:
            QueueService.sync_file_du_jour()
            from hopital.services.admin_service import AdminService
            return render_template(
                'admin_secretariat/dashboard.html',
                stats=AdminService.get_stats()
            )
        return redirect(url_for('login'))

    @app.route('/book-appointment')
    @role_required('patient')
    def book_appointment():
        return _booking_page(patient_id=current_user.id, for_staff=False)

    @app.route('/confirm-appointment', methods=['GET', 'POST'])
    @role_required('patient')
    def confirm_appointment():
        return _confirm_booking(current_user.id, url_for('book_appointment'))

    @app.route('/cancel-appointment/<int:rv_id>', methods=['POST'])
    @login_required
    def cancel_appointment(rv_id):
        rv = db.session.get(RendezVous, rv_id)
        if not rv:
            flash('Rendez-vous introuvable', 'danger')
            return redirect(url_for('dashboard'))
        allowed = (
            (current_user.role == 'patient' and rv.patient_id == current_user.id)
            or current_user.role in ['secretaire', 'admin']
        )
        if not allowed:
            flash('Accès non autorisé', 'danger')
            return redirect(url_for('dashboard'))
        if rv.statut != 'Confirmé':
            flash('Ce rendez-vous ne peut plus être annulé', 'warning')
            return redirect(url_for('dashboard'))
        from hopital.services.services import liberer_creneau
        liberer_creneau(rv)
        db.session.commit()
        flash('Rendez-vous annulé', 'success')
        if current_user.role in ['secretaire', 'admin']:
            return redirect(url_for('manage_appointments'))
        return redirect(url_for('dashboard'))

    @app.route('/reschedule/<int:rv_id>', methods=['GET', 'POST'])
    @login_required
    def reschedule(rv_id):
        rv = RendezVous.query.options(joinedload(RendezVous.medecin)).filter_by(id=rv_id).first()
        if not rv:
            flash('Rendez-vous introuvable', 'danger')
            return redirect(url_for('dashboard'))
        allowed = (
            (current_user.role == 'patient' and rv.patient_id == current_user.id)
            or current_user.role in ['secretaire', 'admin']
        )
        if not allowed or rv.statut != 'Confirmé':
            flash('Modification impossible', 'danger')
            return redirect(url_for('dashboard'))
        if request.method == 'POST':
            slot_id = request.form.get('slot_id', type=int)
            success, err = AppointmentService.reschedule_appointment(rv.id, slot_id)
            if not success:
                flash(err or 'Erreur lors du reprogrammation', 'danger')
                return redirect(url_for('reschedule', rv_id=rv_id))
            flash('Rendez-vous modifié', 'success')
            return redirect(url_for('dashboard') if current_user.role == 'patient' else url_for('manage_appointments'))
        slots = Creneau.query.filter(
            Creneau.medecin_id == rv.medecin_id,
            Creneau.date >= date.today(),
            Creneau.disponible.is_(True)
        ).order_by(Creneau.date, Creneau.heure_debut).all()
        return render_template('patient/reschedule.html', rv=rv, slots=slots)

    @app.route('/edit-profile', methods=['GET', 'POST'])
    @role_required('patient')
    def edit_profile():
        if request.method == 'POST':
            current_user.nom = request.form['nom']
            current_user.prenom = request.form['prenom']
            current_user.contact = request.form['contact']
            if request.form.get('date_naissance'):
                current_user.date_naissance = datetime.strptime(request.form['date_naissance'], '%Y-%m-%d').date()
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

    @app.route('/ma-file')
    @role_required('patient')
    def ma_file():
        QueueService.sync_file_du_jour()
        pos = QueueService.get_patient_position(current_user.id)
        return render_template('patient/queue_position.html', position=pos)

    @app.route('/check-in/<int:file_id>', methods=['POST'])
    @login_required
    def check_in(file_id):
        fa = db.session.get(FileAttente, file_id)
        if not fa:
            flash('File introuvable', 'danger')
            return redirect(url_for('dashboard'))
        own = current_user.role == 'patient' and fa.patient_id == current_user.id
        staff = current_user.role in ['secretaire', 'admin']
        if not (own or staff):
            flash('Accès non autorisé', 'danger')
            return redirect(url_for('dashboard'))
        success, err = QueueService.check_in_patient(file_id)
        if not success:
            flash(err, 'warning')
            return redirect(url_for('dashboard'))
        flash('Arrivée enregistrée', 'success')
        if staff:
            return redirect(url_for('queue_management'))
        return redirect(url_for('ma_file'))
