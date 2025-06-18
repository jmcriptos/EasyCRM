from datetime import datetime, timedelta
from flask import request, render_template, url_for, redirect
from flask_login import login_required

from app.core.forms import CreateContact, CreateOrganisation
from app.core.models import Contact, Organisation
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
    from app.core.models import Contact
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
    from app.core.models import Organisation
    organisations = Organisation.query.all()
    return render_template('core/list_organisations.html', organisations=organisations)