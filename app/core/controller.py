from datetime import datetime, timedelta, date
from flask import request, render_template, url_for, redirect, flash, jsonify
from flask_login import login_required

from app.core.forms import CreateContact, CreateOrganisation, OrderScheduleForm, VisitScheduleForm
from app.core.models import Contact, Organisation, OrderSchedule, VisitSchedule
from app.database import db
from . import core


@core.route('/')
def home():
    # Calcular estadísticas
    stats = {
        'total_contacts': Contact.query.count(),
        'total_organisations': Organisation.query.count(),
        'recent_contacts': Contact.query.filter(Contact.date_created >= datetime.now() - timedelta(days=7)).count(),
        'active_users': 1  # O el cálculo que necesites
    }
    
    # Actividad reciente opcional
    recent_activity = [
        "Nuevo contacto creado: Juan Pérez",
        "Organización actualizada: Tech Corp",
        "3 contactos importados hoy"
    ]
    
    return render_template('core/home.html', stats=stats, recent_activity=recent_activity)


@core.route('/contact/create', methods=['GET', 'POST'])
@login_required
def create_contact():
    form = CreateContact(request.form)
    if request.method == 'POST':
        if form.validate():
            form.org_id.data = form.org_id.data.id
            contact = Contact.create(**form.data)
            return redirect(url_for('core.view_contact', con_id=contact.id))
    return render_template('core/create_contact.html', form=form)


@core.route('/contact/<con_id>')
@login_required
def view_contact(con_id):
    contact = Contact.query.filter_by(id=con_id).first()
    columns = [el.name for el in Contact.__table__.columns]
    return render_template('core/view_contact.html', columns=columns, record=contact)


@core.route('/contacts')
@login_required
def list_contacts():
    contacts = Contact.query.all()
    return render_template('core/list_contacts.html', contacts=contacts)


@core.route('/organisation/create', methods=['GET', 'POST'])
@login_required
def create_organisation():
    form = CreateOrganisation(request.form)
    if request.method == 'POST':
        if form.validate():
            org = Organisation.create(name=form.name.data, type=form.type.data, address=form.address.data)
            return redirect(url_for('core.view_organisation', org_id=org.id))
    return render_template('core/create_organisation.html', form=form)


@core.route('/organisation/<org_id>')
@login_required
def view_organisation(org_id):
    org = Organisation.query.filter_by(id=org_id).first()
    return render_template('core/view_organisation.html', organisation=org)


@core.route('/organisations')
@login_required
def list_organisations():
    organisations = Organisation.query.all()
    return render_template('core/list_organisations.html', organisations=organisations)


# =================== HORARIOS DE RECEPCIÓN ===================

@core.route('/contact/<int:contact_id>/schedule', methods=['GET', 'POST'])
@login_required
def manage_contact_schedule(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    schedule = contact.order_schedule
    
    form = OrderScheduleForm(obj=schedule)
    
    if form.validate_on_submit():
        if not schedule:
            schedule = OrderSchedule(contact_id=contact_id)
            db.session.add(schedule)
        
        form.populate_obj(schedule)
        db.session.commit()
        
        flash('Horarios de recepción actualizados correctamente', 'success')
        return redirect(url_for('core.view_contact', con_id=contact_id))
    
    return render_template('core/manage_schedule.html', 
                         form=form, contact=contact, schedule=schedule)


@core.route('/organisation/<int:org_id>/schedule', methods=['GET', 'POST'])
@login_required  
def manage_organisation_schedule(org_id):
    organisation = Organisation.query.get_or_404(org_id)
    schedule = organisation.order_schedule
    
    form = OrderScheduleForm(obj=schedule)
    
    if form.validate_on_submit():
        if not schedule:
            schedule = OrderSchedule(organisation_id=org_id)
            db.session.add(schedule)
        
        form.populate_obj(schedule)
        db.session.commit()
        
        flash('Horarios de recepción actualizados correctamente', 'success')
        return redirect(url_for('core.view_organisation', org_id=org_id))
    
    return render_template('core/manage_schedule.html', 
                         form=form, organisation=organisation, schedule=schedule)


# =================== VISITAS PROGRAMADAS ===================

@core.route('/schedule/<int:schedule_id>/visits')
@login_required
def list_visit_schedules(schedule_id):
    """Lista todas las visitas programadas para un horario"""
    schedule = OrderSchedule.query.get_or_404(schedule_id)
    visits = VisitSchedule.query.filter_by(order_schedule_id=schedule_id).all()
    
    # Calcular próximas fechas de visita
    visit_data = []
    for visit in visits:
        next_date = visit.get_next_visit_date()
        visit_data.append({
            'visit': visit,
            'next_date': next_date,
            'days_until': (next_date - date.today()).days if next_date else None
        })
    
    # Ordenar por próxima fecha
    visit_data.sort(key=lambda x: x['next_date'] or date(2999, 12, 31))
    
    return render_template('core/list_visit_schedules.html', 
                         schedule=schedule, visit_data=visit_data)


@core.route('/schedule/<int:schedule_id>/visit/create', methods=['GET', 'POST'])
@login_required
def create_visit_schedule(schedule_id):
    """Crear nueva visita programada"""
    schedule = OrderSchedule.query.get_or_404(schedule_id)
    form = VisitScheduleForm()
    
    if form.validate_on_submit():
        visit = VisitSchedule(order_schedule_id=schedule_id)
        form.populate_obj(visit)
        
        db.session.add(visit)
        db.session.commit()
        
        flash(f'Visita programada creada: {visit.get_frequency_display()} los {visit.get_day_name()}', 'success')
        return redirect(url_for('core.list_visit_schedules', schedule_id=schedule_id))
    
    return render_template('core/create_visit_schedule.html', 
                         form=form, schedule=schedule)


@core.route('/visit/<int:visit_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_visit_schedule(visit_id):
    """Editar visita programada existente"""
    visit = VisitSchedule.query.get_or_404(visit_id)
    form = VisitScheduleForm(obj=visit)
    
    if form.validate_on_submit():
        form.populate_obj(visit)
        db.session.commit()
        
        flash('Visita programada actualizada correctamente', 'success')
        return redirect(url_for('core.list_visit_schedules', schedule_id=visit.order_schedule_id))
    
    return render_template('core/edit_visit_schedule.html', 
                         form=form, visit=visit)


@core.route('/visit/<int:visit_id>/delete', methods=['POST'])
@login_required
def delete_visit_schedule(visit_id):
    """Eliminar visita programada"""
    visit = VisitSchedule.query.get_or_404(visit_id)
    schedule_id = visit.order_schedule_id
    
    db.session.delete(visit)
    db.session.commit()
    
    flash('Visita programada eliminada', 'info')
    return redirect(url_for('core.list_visit_schedules', schedule_id=schedule_id))


# =================== API Y VERIFICACIONES ===================

@core.route('/schedule/check', methods=['POST'])
@login_required
def check_availability():
    """API endpoint para verificar disponibilidad en tiempo real"""
    data = request.get_json()
    
    target_type = data.get('type')  # 'contact' or 'organisation'
    target_id = data.get('id')
    check_datetime = datetime.fromisoformat(data.get('datetime'))
    
    if target_type == 'contact':
        schedule = OrderSchedule.query.filter_by(contact_id=target_id).first()
    else:
        schedule = OrderSchedule.query.filter_by(organisation_id=target_id).first()
    
    if not schedule:
        return jsonify({'available': True, 'message': 'No hay restricciones de horario'})
    
    day_available = schedule.is_available_on_day(check_datetime.weekday())
    time_available = schedule.is_available_at_time(check_datetime.time())
    
    # Verificar si hay visita programada para esa fecha
    visit_scheduled = False
    next_visit = schedule.get_next_visit_date()
    if next_visit and next_visit == check_datetime.date():
        visit_scheduled = True
    
    available = day_available and time_available
    
    message = ''
    if not day_available:
        message = f'No recibe pedidos los {["lunes", "martes", "miércoles", "jueves", "viernes", "sábados", "domingos"][check_datetime.weekday()]}'
    elif not time_available:
        message = f'No recibe pedidos a las {check_datetime.strftime("%H:%M")}'
    elif visit_scheduled:
        message = f'Visita comercial programada para este día'
    
    return jsonify({
        'available': available,
        'visit_scheduled': visit_scheduled,
        'message': message,
        'schedule': {
            'days': schedule.get_available_days_display(),
            'hours': f'{schedule.start_time.strftime("%H:%M")} - {schedule.end_time.strftime("%H:%M")}',
            'next_visit': next_visit.strftime("%d/%m/%Y") if next_visit else None
        }
    })


# =================== DASHBOARDS ===================

@core.route('/dashboard/visits')
@login_required
def upcoming_visits_dashboard():
    """Dashboard de próximas visitas"""
    today = date.today()
    next_week = today + timedelta(days=7)
    
    # Obtener todas las visitas programadas
    all_visits = VisitSchedule.query.filter_by(active=True).all()
    
    upcoming_visits = []
    for visit in all_visits:
        next_date = visit.get_next_visit_date()
        if next_date and today <= next_date <= next_week:
            upcoming_visits.append({
                'visit': visit,
                'date': next_date,
                'target': visit.order_schedule.target,
                'days_until': (next_date - today).days
            })
    
    # Ordenar por fecha
    upcoming_visits.sort(key=lambda x: x['date'])
    
    return render_template('core/upcoming_visits_dashboard.html', 
                         upcoming_visits=upcoming_visits, today=today)


@core.route('/visits/calendar')
@login_required
def visits_calendar():
    """Vista de calendario con todas las visitas"""
    # Obtener mes actual o el especificado
    year = request.args.get('year', default=date.today().year, type=int)
    month = request.args.get('month', default=date.today().month, type=int)
    
    # Calcular visitas para el mes
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    all_visits = VisitSchedule.query.filter_by(active=True).all()
    
    calendar_data = {}
    current_date = start_date
    
    while current_date <= end_date:
        calendar_data[current_date] = []
        
        for visit in all_visits:
            next_visit = visit.get_next_visit_date(from_date=current_date - timedelta(days=1))
            if next_visit == current_date:
                calendar_data[current_date].append({
                    'visit': visit,
                    'target': visit.order_schedule.target
                })
        
        current_date += timedelta(days=1)
    
    return render_template('core/visits_calendar.html', 
                         calendar_data=calendar_data, 
                         year=year, month=month)