from datetime import datetime, date, time, timedelta
from functools import wraps
from flask import render_template, request, redirect, url_for, flash, current_app, send_from_directory
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from hopital.extensions import db
from hopital.models import User, Creneau, RendezVous, FileAttente, NoteConsultation
from hopital.services.queue_service import QueueService
from hopital.services.medecin_service import MedecinService
from hopital.utils import week_dates
from werkzeug.utils import secure_filename
import os


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
    """Enregistre les routes médecin"""
    
    @app.route('/medecin/dashboard')
    @role_required('medecin')
    def medecin_dashboard():
        data = MedecinService.get_medecin_dashboard_data(current_user.id)
        return render_template(
            'medecin/dashboard.html',
            today_patients=data['today_patients'],
            future_slots=data['future_slots'],
            past_appointments=data['past_appointments'],
            date_du_jour=data['date_du_jour'],
            week_days=data['week_days'],
            week_slots=data['week_slots']
        )

    def _slots_by_day(medecin_id, days):
        slots = Creneau.query.filter(
            Creneau.medecin_id == medecin_id,
            Creneau.date.in_(days)
        ).order_by(Creneau.heure_debut).all()
        grouped = {d: [] for d in days}
        for s in slots:
            grouped.setdefault(s.date, []).append(s)
        return grouped

    @app.route('/add-slot', methods=['GET', 'POST'])
    @role_required('medecin')
    def add_slot():
        if request.method == 'POST':
            date_slot = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            heure_debut = datetime.strptime(request.form['heure_debut'], '%H:%M').time()
            heure_fin = datetime.strptime(request.form['heure_fin'], '%H:%M').time()
            creneau, err = MedecinService.add_slot(current_user.id, date_slot, heure_debut, heure_fin)
            if err:
                flash(err, 'danger')
                return render_template('medecin/add_slot.html')
            flash('Créneau ajouté avec succès', 'success')
            return redirect(url_for('medecin.dashboard'))
        return render_template('medecin/add_slot.html')

    @app.route('/planning-semaine')
    @role_required('medecin')
    def planning_semaine():
        start = request.args.get('start')
        if start:
            try:
                start_date = datetime.strptime(start, '%Y-%m-%d').date()
            except ValueError:
                start_date = date.today()
        else:
            start_date = date.today()
        days = week_dates(start_date)
        return render_template(
            'medecin/week.html',
            week_days=days,
            week_slots=_slots_by_day(current_user.id, days),
            prev_start=days[0] - timedelta(days=7),
            next_start=days[0] + timedelta(days=7)
        )

    @app.route('/delete-slot/<int:slot_id>', methods=['POST'])
    @role_required('medecin')
    def delete_slot(slot_id):
        success, err = MedecinService.delete_slot(slot_id, current_user.id)
        if success:
            flash('Créneau supprimé', 'success')
        else:
            flash(err or 'Impossible de supprimer ce créneau', 'danger')
        return redirect(url_for('medecin.dashboard'))

    @app.route('/start-consultation/<int:queue_id>', methods=['POST'])
    @role_required('medecin')
    def start_consultation(queue_id):
        success, err = QueueService.start_consultation(queue_id, current_user.id)
        if not success:
            flash(err or 'File introuvable', 'danger')
            return redirect(url_for('medecin.dashboard'))
        flash('Consultation commencée', 'success')
        return redirect(url_for('medecin.dashboard'))

    @app.route('/end-consultation/<int:queue_id>', methods=['POST'])
    @role_required('medecin')
    def end_consultation(queue_id):
        success, err = QueueService.end_consultation(queue_id)
        if not success:
            flash(err or 'File introuvable', 'danger')
            return redirect(url_for('medecin.dashboard'))
        fa = db.session.get(FileAttente, queue_id)
        flash('Consultation terminée. Vous pouvez ajouter une note.', 'success')
        return redirect(url_for('consultation_note', rdv_id=fa.rendez_vous_id))

    @app.route('/consultation-note/<int:rdv_id>', methods=['GET', 'POST'])
    @role_required('medecin')
    def consultation_note(rdv_id):
        rdv = RendezVous.query.options(
            joinedload(RendezVous.patient), joinedload(RendezVous.note)
        ).filter_by(id=rdv_id).first()
        if not rdv:
            flash('Rendez-vous introuvable', 'danger')
            return redirect(url_for('medecin.dashboard'))
        if rdv.medecin_id != current_user.id:
            flash('Accès non autorisé', 'danger')
            return redirect(url_for('medecin.dashboard'))
        note = rdv.note or NoteConsultation(rendez_vous_id=rdv.id, medecin_id=current_user.id)
        if request.method == 'POST':
            data = {
                'motif': request.form.get('motif'),
                'diagnostic': request.form.get('diagnostic'),
                'ordonnance': request.form.get('ordonnance'),
                'notes': request.form.get('notes')
            }
            upload = request.files.get('document')
            note, err = MedecinService.save_consultation_note(rdv.id, current_user.id, data, upload)
            if err:
                flash(err, 'danger')
                return render_template('medecin/consultation_note.html', rdv=rdv, note=note)
            flash('Note de consultation enregistrée', 'success')
            return redirect(url_for('view_patient_dossier', patient_id=rdv.patient_id))
        return render_template('medecin/consultation_note.html', rdv=rdv, note=note)

    @app.route('/uploads/<path:filename>')
    @login_required
    def uploaded_file(filename):
        if current_user.role not in ['medecin', 'secretaire', 'admin']:
            flash('Accès non autorisé', 'danger')
            return redirect(url_for('dashboard'))
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

    @app.route('/view-patient-dossier/<int:patient_id>')
    @role_required('medecin', 'secretaire', 'admin')
    def view_patient_dossier(patient_id):
        patient = db.session.get(User, patient_id)
        if not patient or patient.role != 'patient':
            flash('Patient non trouvé', 'danger')
            return redirect(url_for('dashboard'))
        PatientService.ensure_patient_profile(patient)
        from hopital.services.services import log_acces
        log_acces(current_user.id, 'consultation_dossier', patient_id=patient.id)
        from sqlalchemy.orm import aliased
        Medecin = aliased(User)
        historique = db.session.query(RendezVous, Medecin).join(
            Medecin, RendezVous.medecin_id == Medecin.id
        ).options(joinedload(RendezVous.note)).filter(
            RendezVous.patient_id == patient_id
        ).order_by(RendezVous.date.desc()).all()
        return render_template(
            'medecin/patient_dossier.html',
            patient=patient,
            historique=historique
        )
