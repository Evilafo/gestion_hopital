import csv
import io
from datetime import datetime, date, timedelta
from functools import wraps
from flask import render_template, request, redirect, url_for, flash, Response
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload, aliased
from sqlalchemy import or_
from hopital.extensions import db
from hopital.models import User, PatientProfil, Salle, Creneau, RendezVous, FileAttente
from hopital.services.queue_service import QueueService
from hopital.services.admin_service import AdminService
from hopital.services.patient_service import PatientService
from hopital.services.appointment_service import AppointmentService
from hopital.utils import week_dates, generate_internal_email
from hopital.services.services import log_acces, send_reminders, liberer_creneau


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


def register_routes(app):
    """Enregistre les routes admin/secretariat"""
    
    @app.route('/secretariat/book-appointment')
    @role_required('secretaire', 'admin')
    def secretariat_book_appointment():
        from hopital.routes.patient import _booking_page
        return _booking_page(
            patient_id=request.args.get('patient_id', type=int),
            for_staff=True
        )

    @app.route('/secretariat/confirm-appointment', methods=['GET', 'POST'])
    @role_required('secretaire', 'admin')
    def confirm_appointment_staff():
        from hopital.routes.patient import _confirm_booking
        patient_id = request.values.get('patient_id', type=int)
        if not patient_id:
            flash('Choisissez un patient', 'danger')
            return redirect(url_for('secretariat_book_appointment'))
        return _confirm_booking(patient_id, url_for('secretariat_book_appointment', patient_id=patient_id))

    @app.route('/queue-management')
    @role_required('secretaire', 'admin')
    def queue_management():
        payload = QueueService.get_file_payload()
        return render_template(
            'admin_secretariat/queue_management.html',
            file_data=payload,
            date_du_jour=date.today()
        )

    @app.route('/waiting-room')
    @role_required('secretaire', 'admin', 'medecin')
    def waiting_room():
        return render_template('admin_secretariat/waiting_room.html', date_du_jour=date.today())

    @app.route('/queue-print')
    @role_required('secretaire', 'admin')
    def queue_print():
        return render_template(
            'admin_secretariat/queue_print.html',
            file_data=QueueService.get_file_payload(),
            date_du_jour=date.today()
        )

    @app.route('/call-patient/<int:file_id>', methods=['POST'])
    @role_required('secretaire', 'admin')
    def call_patient(file_id):
        fa = db.session.get(FileAttente, file_id)
        if fa:
            ongoing = QueueService.get_consultation_en_cours(fa.medecin_id)
            if ongoing and ongoing.id != fa.id:
                flash('Une consultation est déjà en cours pour ce médecin.', 'warning')
                return redirect(url_for('queue_management'))
            success, err = QueueService.start_consultation(file_id, fa.medecin_id)
            if success:
                flash('Patient appelé', 'success')
            else:
                flash(err or 'Erreur', 'danger')
        return redirect(url_for('queue_management'))

    @app.route('/next-patient/<int:medecin_id>', methods=['POST'])
    @role_required('secretaire', 'admin')
    def next_patient(medecin_id):
        ongoing = QueueService.get_consultation_en_cours(medecin_id)
        if ongoing:
            flash('Terminez d\'abord la consultation en cours.', 'warning')
            return redirect(url_for('queue_management'))
        nxt = FileAttente.query.filter_by(
            medecin_id=medecin_id, date=date.today(), statut_file='En Attente'
        ).order_by(FileAttente.ordre).first()
        if not nxt:
            flash('Aucun patient en attente', 'info')
        else:
            success, err = QueueService.start_consultation(nxt.id, medecin_id)
            if success:
                flash(f'{nxt.patient.nom_complet} appelé', 'success')
            else:
                flash(err or 'Erreur', 'danger')
        return redirect(url_for('queue_management'))

    @app.route('/finish-consultation/<int:file_id>', methods=['POST'])
    @role_required('secretaire', 'admin')
    def finish_consultation(file_id):
        success, err = QueueService.end_consultation(file_id)
        if success:
            flash('Consultation marquée comme terminée', 'success')
        else:
            flash(err or 'Erreur', 'danger')
        return redirect(url_for('queue_management'))

    @app.route('/mark-absent/<int:file_id>', methods=['POST'])
    @role_required('secretaire', 'admin')
    def mark_absent(file_id):
        success, err = QueueService.mark_patient_absent(file_id)
        if success:
            flash('Patient marqué absent', 'info')
        else:
            flash(err or 'Erreur', 'danger')
        return redirect(url_for('queue_management'))

    @app.route('/delay-patient/<int:file_id>', methods=['POST'])
    @role_required('secretaire', 'admin')
    def delay_patient(file_id):
        minutes = request.form.get('minutes', type=int) or 15
        success, err = QueueService.delay_patient(file_id, minutes)
        if success:
            flash(f'Retard de {minutes} min enregistré', 'info')
        else:
            flash(err or 'Erreur', 'danger')
        return redirect(url_for('queue_management'))

    @app.route('/move-queue/<int:file_id>/<direction>', methods=['POST'])
    @role_required('secretaire', 'admin')
    def move_queue(file_id, direction):
        success, err = QueueService.move_patient_in_queue(file_id, direction)
        if not success:
            flash(err or 'Erreur', 'danger')
        return redirect(url_for('queue_management'))

    @app.route('/manage-personnel')
    @role_required('admin')
    def manage_personnel():
        personnel = AdminService.get_personnel()
        return render_template('admin_secretariat/manage_personnel.html', personnel=personnel)

    @app.route('/add-personnel', methods=['GET', 'POST'])
    @role_required('admin')
    def add_personnel():
        if request.method == 'POST':
            data = {
                'nom': request.form['nom'],
                'prenom': request.form['prenom'],
                'email': request.form['email'],
                'role': request.form['role'],
                'contact': request.form.get('contact'),
                'specialite': request.form.get('specialite') if request.form['role'] == 'medecin' else None,
                'salle_id': (request.form.get('salle_id') or None) if request.form['role'] == 'medecin' else None,
                'password': request.form['password']
            }
            user, err = AdminService.add_personnel(data)
            if err:
                flash(err, 'danger')
                return redirect(request.url)
            flash('Le membre du personnel a été ajouté avec succès.', 'success')
            return redirect(url_for('manage_personnel'))
        salles = AdminService.get_salles()
        return render_template('admin_secretariat/edit_personnel.html', action='Ajouter', salles=salles)

    @app.route('/edit-personnel/<int:user_id>', methods=['GET', 'POST'])
    @role_required('admin')
    def edit_personnel(user_id):
        user_to_edit = User.query.get_or_404(user_id)
        if request.method == 'POST':
            data = {
                'nom': request.form['nom'],
                'prenom': request.form['prenom'],
                'email': request.form['email'],
                'role': request.form['role'],
                'contact': request.form.get('contact'),
                'specialite': request.form.get('specialite'),
                'salle_id': request.form.get('salle_id'),
                'password': request.form.get('password')
            }
            success, err = AdminService.update_personnel(user_id, data)
            if not success:
                flash(err, 'danger')
                return redirect(request.url)
            flash('Les informations ont été mises à jour.', 'success')
            return redirect(url_for('manage_personnel'))
        salles = AdminService.get_salles()
        return render_template(
            'admin_secretariat/edit_personnel.html',
            action='Modifier', user=user_to_edit, salles=salles
        )

    @app.route('/delete-personnel/<int:user_id>', methods=['POST'])
    @role_required('admin')
    def delete_personnel(user_id):
        success, err = AdminService.delete_personnel(user_id, current_user.id)
        if success:
            flash('Le membre du personnel a été supprimé avec succès.', 'success')
        else:
            flash(err, 'danger')
        return redirect(url_for('manage_personnel'))

    @app.route('/manage-patients')
    @role_required('secretaire', 'admin')
    def manage_patients():
        q = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        pagination = PatientService.search_patients(q, page, 12)
        return render_template(
            'admin_secretariat/manage_patients.html',
            patients=pagination.items,
            pagination=pagination,
            q=q
        )

    @app.route('/add-patient', methods=['GET', 'POST'])
    @role_required('secretaire', 'admin')
    def add_patient():
        if request.method == 'POST':
            email = request.form.get('email', '').strip()
            compte_web = bool(email)
            if not email:
                email = generate_internal_email()
            if User.query.filter_by(email=email).first():
                flash('Cet email est déjà utilisé', 'danger')
                return render_template('admin_secretariat/edit_patient.html', patient=None, action='Ajouter')
            user = User(
                nom=request.form['nom'],
                prenom=request.form['prenom'],
                email=email,
                contact=request.form.get('contact'),
                role='patient',
                compte_web=compte_web
            )
            if request.form.get('date_naissance'):
                user.date_naissance = datetime.strptime(request.form['date_naissance'], '%Y-%m-%d').date()
            password = request.form.get('password') or 'temp-' + generate_internal_email()[:8]
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            PatientService.ensure_patient_profile(user)
            profil = user.profil_patient
            profil.allergies = request.form.get('allergies')
            profil.antecedents = request.form.get('antecedents')
            db.session.commit()
            flash('Patient créé', 'success')
            return redirect(url_for('manage_patients'))
        return render_template('admin_secretariat/edit_patient.html', patient=None, action='Ajouter')

    @app.route('/edit-patient/<int:patient_id>', methods=['GET', 'POST'])
    @role_required('secretaire', 'admin')
    def edit_patient(patient_id):
        patient = User.query.get_or_404(patient_id)
        if patient.role != 'patient':
            flash('Utilisateur non valide.', 'danger')
            return redirect(url_for('manage_patients'))
        PatientService.ensure_patient_profile(patient)
        if request.method == 'POST':
            data = {
                'nom': request.form['nom'],
                'prenom': request.form['prenom'],
                'contact': request.form['contact'],
                'date_naissance': request.form.get('date_naissance'),
                'password': request.form.get('password'),
                'password_confirm': request.form.get('password_confirm'),
                'allergies': request.form.get('allergies'),
                'antecedents': request.form.get('antecedents'),
                'notes_internes': request.form.get('notes_internes')
            }
            success, err = PatientService.update_patient_profile(patient, data)
            if not success:
                flash(err, 'danger')
                return redirect(request.url)
            flash('Les informations du patient ont été mises à jour.', 'success')
            return redirect(url_for('manage_patients'))
        return render_template('admin_secretariat/edit_patient.html', patient=patient, action='Modifier')

    @app.route('/export-patients')
    @role_required('secretaire', 'admin')
    def export_patients():
        csv_content = AdminService.export_patients()
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=patients.csv'}
        )

    @app.route('/manage-rooms')
    @role_required('secretaire', 'admin')
    def manage_rooms():
        salles = AdminService.get_salles()
        return render_template('admin_secretariat/manage_rooms.html', salles=salles)

    @app.route('/add-room', methods=['POST'])
    @role_required('secretaire', 'admin')
    def add_room():
        data = {
            'numero': request.form['numero'],
            'nom': request.form.get('nom')
        }
        salle, err = AdminService.add_salle(data)
        if err:
            flash(err, 'danger')
            return redirect(url_for('manage_rooms'))
        flash('Salle ajoutée', 'success')
        return redirect(url_for('manage_rooms'))

    @app.route('/edit-room/<int:salle_id>', methods=['POST'])
    @role_required('secretaire', 'admin')
    def edit_room(salle_id):
        data = {
            'numero': request.form['numero'],
            'nom': request.form.get('nom')
        }
        success, err = AdminService.update_salle(salle_id, data)
        if not success:
            flash(err, 'danger')
            return redirect(url_for('manage_rooms'))
        flash('Salle mise à jour', 'success')
        return redirect(url_for('manage_rooms'))

    @app.route('/delete-room/<int:salle_id>', methods=['POST'])
    @role_required('secretaire', 'admin')
    def delete_room(salle_id):
        success, err = AdminService.delete_salle(salle_id)
        if success:
            flash('Salle supprimée', 'success')
        else:
            flash(err, 'danger')
        return redirect(url_for('manage_rooms'))

    @app.route('/manage-appointments')
    @role_required('secretaire', 'admin')
    def manage_appointments():
        page = request.args.get('page', 1, type=int)
        statut = request.args.get('statut', '')
        date_filter = request.args.get('date', '')
        pagination = AdminService.get_appointments(page, 15, statut, date_filter)
        return render_template(
            'admin_secretariat/manage_appointments.html',
            appointments=pagination.items,
            pagination=pagination,
            statut=statut,
            date_filter=date_filter
        )

    @app.route('/export-appointments')
    @role_required('secretaire', 'admin')
    def export_appointments():
        csv_content = AdminService.export_appointments()
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=rendez_vous.csv'}
        )

    @app.route('/stats')
    @role_required('secretaire', 'admin')
    def stats():
        return render_template('admin_secretariat/stats.html', stats=AdminService.get_stats())

    @app.route('/send-reminders', methods=['POST'])
    @role_required('secretaire', 'admin')
    def send_reminders_route():
        from flask import current_app
        sent, errors = send_reminders()
        if errors:
            flash(f'{sent} rappel(s) traités, erreurs SMTP : {errors[0]}', 'warning')
        elif not current_app.config.get('MAIL_SERVER'):
            flash(f'{sent} rappel(s) marqués (aucun serveur SMTP configuré, e-mails non envoyés).', 'info')
        else:
            flash(f'{sent} rappel(s) envoyés', 'success')
        return redirect(url_for('dashboard'))
