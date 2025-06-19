from sqlalchemy_utils import EmailType, ChoiceType
from sqlalchemy.exc import IntegrityError
from datetime import date, time, datetime, timedelta

from app.database import db, Base



class Base(db.Model):

    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())


class Contact(Base):

    """User input fields - these fields can be set by user and are included in forms"""
    first_name = db.Column(db.String(60), nullable=False, info={"label": "First Name"})
    last_name = db.Column(db.String(60), nullable=False, info={"label": "Last Name"})
    email = db.Column(EmailType, nullable=False, info={"label": "Email"})
    mobile = db.Column(db.Integer, info={"label": "Mobile"})
    role = db.Column(db.String(60), info={"label": "Role"})
    org_id = db.Column(db.Integer, db.ForeignKey('organisation.id'), info={"label": "Organisation"})
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    order_schedule = db.relationship('OrderSchedule', backref='contact', uselist=False)

    activities = db.relationship('Activity', backref='contact')

    @staticmethod
    def create(**kwargs):
        c = Contact(**kwargs)
        db.session.add(c)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        return c


class Organisation(Base):
    TYPE_CHOICE = [
        ('charity', 'Charity'),
        ('funder', 'Funder'),
        ('other', 'Other')
    ]

    name = db.Column(db.String(100), nullable=False)
    type = db.Column(ChoiceType(TYPE_CHOICE), nullable=False)
    address = db.Column(db.Text(180))

    order_schedule = db.relationship('OrderSchedule', backref='organisation', uselist=False)

    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))

    contacts = db.relationship('Contact', backref='organisation')
    activities = db.relationship('Activity', backref='contact_lookup')

    @staticmethod
    def create(**kwargs):
        o = Organisation(**kwargs)
        db.session.add(o)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        return o


class Project(Base):
    STATUS_CHOICE = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ]

    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(ChoiceType(STATUS_CHOICE), nullable=False)

    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    org_id = db.Column(db.Integer, db.ForeignKey('organisation.id'))
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'))

    activities = db.relationship('Activity', backref='project')
    invoices = db.relationship('Invoice', backref='project')


class Invoice(Base):

    issue_date = db.Column(db.Date)
    amount = db.Column(db.Integer, nullable=False)
    paid = db.Column(db.Boolean, default=False)

    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))


class Activity(Base):

    subject = db.Column(db.String(100), nullable=False)
    detail = db.Column(db.Text)

    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'))
    org_id = db.Column(db.Integer, db.ForeignKey('organisation.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))

class OrderSchedule(Base):
    __tablename__ = 'order_schedule'
    
    # Relaciones
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), nullable=True)
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisation.id'), nullable=True)
    
    # Días de la semana para recepción general (0=Lunes, 6=Domingo)
    monday = db.Column(db.Boolean, default=True)
    tuesday = db.Column(db.Boolean, default=True)
    wednesday = db.Column(db.Boolean, default=True)
    thursday = db.Column(db.Boolean, default=True)
    friday = db.Column(db.Boolean, default=True)
    saturday = db.Column(db.Boolean, default=False)
    sunday = db.Column(db.Boolean, default=False)
    
    # Horarios generales
    start_time = db.Column(db.Time, nullable=False, default=time(9, 0))  # 9:00 AM
    end_time = db.Column(db.Time, nullable=False, default=time(17, 0))   # 5:00 PM
    
    # Configuraciones adicionales
    lunch_break_start = db.Column(db.Time, nullable=True)  # Hora inicio almuerzo
    lunch_break_end = db.Column(db.Time, nullable=True)    # Hora fin almuerzo
    
    # Notas adicionales
    notes = db.Column(db.Text, nullable=True)
    active = db.Column(db.Boolean, default=True)
    
    # Validación: debe estar asociado a contacto O organización, no ambos
    __table_args__ = (
        db.CheckConstraint(
            '(contact_id IS NOT NULL AND organisation_id IS NULL) OR '
            '(contact_id IS NULL AND organisation_id IS NOT NULL)',
            name='schedule_target_check'
        ),
    )
    
    # Relación con visitas programadas
    visit_schedules = db.relationship('VisitSchedule', backref='order_schedule', 
                                    cascade='all, delete-orphan')
    
    @property
    def target(self):
        """Retorna el contacto o organización asociada"""
        return self.contact or self.organisation
    
    def is_available_on_day(self, day_of_week):
        """Verifica si está disponible en un día específico (0=Lunes)"""
        days = [self.monday, self.tuesday, self.wednesday, self.thursday, 
                self.friday, self.saturday, self.sunday]
        return days[day_of_week] if 0 <= day_of_week <= 6 else False
    
    def is_available_at_time(self, time_obj):
        """Verifica si está disponible en una hora específica"""
        if not self.start_time <= time_obj <= self.end_time:
            return False
        
        # Verificar break de almuerzo
        if (self.lunch_break_start and self.lunch_break_end and 
            self.lunch_break_start <= time_obj <= self.lunch_break_end):
            return False
        
        return True
    
    def get_available_days_display(self):
        """Retorna string con días disponibles"""
        days = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
        available = [days[i] for i, available in enumerate([
            self.monday, self.tuesday, self.wednesday, self.thursday,
            self.friday, self.saturday, self.sunday
        ]) if available]
        return ', '.join(available) if available else 'Ningún día'
    
    def get_next_visit_date(self):
        """Retorna la próxima fecha de visita programada"""
        if not self.visit_schedules:
            return None
        
        today = date.today()
        next_visits = []
        
        for visit_schedule in self.visit_schedules:
            next_visit = visit_schedule.get_next_visit_date(from_date=today)
            if next_visit:
                next_visits.append(next_visit)
        
        return min(next_visits) if next_visits else None


class VisitSchedule(Base):
    __tablename__ = 'visit_schedule'
    
    # Relación con OrderSchedule
    order_schedule_id = db.Column(db.Integer, db.ForeignKey('order_schedule.id'), nullable=False)
    
    # Configuración de la visita
    visit_type = db.Column(db.String(20), nullable=False, default='order_taking')  # order_taking, delivery, meeting
    
    # Día de la semana (0=Lunes, 6=Domingo)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0-6
    
    # Frecuencia de la visita
    FREQUENCY_CHOICES = [
        ('weekly', 'Semanal'),
        ('biweekly', 'Quincenal'),
        ('monthly', 'Mensual'),
        ('custom', 'Personalizado')
    ]
    frequency = db.Column(ChoiceType(FREQUENCY_CHOICES), nullable=False, default='weekly')
    
    # Para frecuencias personalizadas (en días)
    custom_interval_days = db.Column(db.Integer, nullable=True)
    
    # Fecha de inicio del ciclo
    start_date = db.Column(db.Date, nullable=False, default=date.today)
    
    # Fecha de fin (opcional)
    end_date = db.Column(db.Date, nullable=True)
    
    # Horario específico de la visita
    visit_start_time = db.Column(db.Time, nullable=True)  # Si es None, usar horario general
    visit_end_time = db.Column(db.Time, nullable=True)
    
    # Configuraciones adicionales
    active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text, nullable=True)
    
    def get_interval_days(self):
        """Retorna el intervalo en días según la frecuencia"""
        if self.frequency == 'weekly':
            return 7
        elif self.frequency == 'biweekly':
            return 14
        elif self.frequency == 'monthly':
            return 30  # Aproximado
        elif self.frequency == 'custom':
            return self.custom_interval_days or 7
        return 7
    
    def get_next_visit_date(self, from_date=None):
        """Calcula la próxima fecha de visita desde una fecha dada"""
        if not from_date:
            from_date = date.today()
        
        if not self.active:
            return None
        
        if self.end_date and from_date > self.end_date:
            return None
        
        # Calcular la próxima fecha basada en el ciclo
        interval_days = self.get_interval_days()
        
        if self.frequency == 'monthly':
            # Para mensual, usar dateutil para manejar meses correctamente
            from dateutil.relativedelta import relativedelta
            current = self.start_date
            
            while current <= from_date:
                current += relativedelta(months=1)
                # Ajustar al día de la semana correcto
                while current.weekday() != self.day_of_week:
                    current += timedelta(days=1)
            
            return current if (not self.end_date or current <= self.end_date) else None
        
        else:
            # Para semanal, quincenal y personalizado
            days_since_start = (from_date - self.start_date).days
            
            if days_since_start < 0:
                # La fecha de inicio aún no ha llegado
                next_date = self.start_date
            else:
                # Calcular cuántos ciclos han pasado
                cycles_passed = days_since_start // interval_days
                next_cycle_start = self.start_date + timedelta(days=(cycles_passed + 1) * interval_days)
                
                # Ajustar al día de la semana correcto si es necesario
                days_to_adjust = (self.day_of_week - next_cycle_start.weekday()) % 7
                next_date = next_cycle_start + timedelta(days=days_to_adjust)
            
            return next_date if (not self.end_date or next_date <= self.end_date) else None
    
    def get_frequency_display(self):
        """Retorna descripción legible de la frecuencia"""
        frequency_map = {
            'weekly': 'Cada semana',
            'biweekly': 'Cada 2 semanas', 
            'monthly': 'Mensual',
            'custom': f'Cada {self.custom_interval_days} días' if self.custom_interval_days else 'Personalizado'
        }
        return frequency_map.get(self.frequency, 'Desconocido')
    
    def get_day_name(self):
        """Retorna el nombre del día en español"""
        days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        return days[self.day_of_week] if 0 <= self.day_of_week <= 6 else 'Día inválido'
    
    @staticmethod
    def create(**kwargs):
        visit = VisitSchedule(**kwargs)
        db.session.add(visit)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise
        return visit