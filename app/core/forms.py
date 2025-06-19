from wtforms_alchemy import ModelForm
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_wtf import FlaskForm
from wtforms import BooleanField, TimeField, TextAreaField, SelectField, IntegerField, DateField 
from wtforms.validators import DataRequired, Optional, NumberRange
from datetime import date, time

from app.core.models import Contact, Organisation


def available_organisations():
    return Organisation.query.all()


class CreateOrganisation(ModelForm):
    class Meta:
        model = Organisation


class CreateContact(ModelForm):
    class Meta:
        model = Contact

    org_id = QuerySelectField('Organisation', query_factory=available_organisations, get_label='name')


class OrderScheduleForm(FlaskForm):
    # Días de la semana para recepción general
    monday = BooleanField('Lunes')
    tuesday = BooleanField('Martes') 
    wednesday = BooleanField('Miércoles')
    thursday = BooleanField('Jueves')
    friday = BooleanField('Viernes')
    saturday = BooleanField('Sábado')
    sunday = BooleanField('Domingo')
    
    # Horarios generales
    start_time = TimeField(
        'Hora de Inicio',
        validators=[DataRequired()],
        default=time(9, 0)
    )
    end_time = TimeField(
        'Hora de Fin', 
        validators=[DataRequired()],
        default=time(17, 0)
    )
    
    # Break de almuerzo (opcional)
    lunch_break_start = TimeField(
        'Inicio Almuerzo',
        validators=[Optional()]
    )
    lunch_break_end = TimeField(
        'Fin Almuerzo',
        validators=[Optional()]
    )
    
    # Notas
    notes = TextAreaField(
        'Notas Adicionales',
        validators=[Optional()],
        description='Información adicional sobre horarios de recepción'
    )
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
        
        # Validar que hora inicio < hora fin
        if self.start_time.data >= self.end_time.data:
            self.end_time.errors.append('La hora de fin debe ser posterior a la hora de inicio')
            return False
        
        # Validar break de almuerzo
        if self.lunch_break_start.data and self.lunch_break_end.data:
            if self.lunch_break_start.data >= self.lunch_break_end.data:
                self.lunch_break_end.errors.append('Fin de almuerzo debe ser posterior al inicio')
                return False
            
            # Break debe estar dentro del horario de trabajo
            if (self.lunch_break_start.data < self.start_time.data or 
                self.lunch_break_end.data > self.end_time.data):
                self.lunch_break_start.errors.append('El break debe estar dentro del horario laboral')
                return False
        
        # Al menos un día debe estar seleccionado
        days_selected = any([
            self.monday.data, self.tuesday.data, self.wednesday.data,
            self.thursday.data, self.friday.data, self.saturday.data, self.sunday.data
        ])
        if not days_selected:
            self.monday.errors.append('Debe seleccionar al menos un día de la semana')
            return False
        
        return True


class VisitScheduleForm(FlaskForm):
    # Tipo de visita
    visit_type = SelectField(
        'Tipo de Visita',
        choices=[
            ('order_taking', 'Toma de Pedidos'),
            ('delivery', 'Entrega'),
            ('meeting', 'Reunión Comercial')
        ],
        default='order_taking'
    )
    
    # Día de la semana
    day_of_week = SelectField(
        'Día de la Semana',
        choices=[
            (0, 'Lunes'),
            (1, 'Martes'),
            (2, 'Miércoles'),
            (3, 'Jueves'),
            (4, 'Viernes'),
            (5, 'Sábado'),
            (6, 'Domingo')
        ],
        coerce=int,
        validators=[DataRequired()]
    )
    
    # Frecuencia
    frequency = SelectField(
        'Frecuencia',
        choices=[
            ('weekly', 'Semanal'),
            ('biweekly', 'Quincenal'),
            ('monthly', 'Mensual'),
            ('custom', 'Personalizado')
        ],
        default='weekly'
    )
    
    # Intervalo personalizado (solo si frequency = custom)
    custom_interval_days = IntegerField(
        'Intervalo en Días',
        validators=[Optional(), NumberRange(min=1, max=365)],
        description='Solo para frecuencia personalizada'
    )
    
    # Fechas
    start_date = DateField(
        'Fecha de Inicio',
        validators=[DataRequired()],
        default=date.today
    )
    
    end_date = DateField(
        'Fecha de Fin',
        validators=[Optional()],
        description='Opcional - dejar vacío para indefinido'
    )
    
    # Horarios específicos (opcional)
    visit_start_time = TimeField(
        'Hora de Inicio Visita',
        validators=[Optional()],
        description='Si se deja vacío, usará el horario general'
    )
    
    visit_end_time = TimeField(
        'Hora de Fin Visita',
        validators=[Optional()]
    )
    
    # Notas
    notes = TextAreaField(
        'Notas de la Visita',
        validators=[Optional()],
        description='Detalles específicos de esta visita programada'
    )
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
        
        # Si frequency es custom, custom_interval_days es requerido
        if self.frequency.data == 'custom' and not self.custom_interval_days.data:
            self.custom_interval_days.errors.append('Especifica el intervalo en días para frecuencia personalizada')
            return False
        
        # Validar fechas
        if self.end_date.data and self.end_date.data <= self.start_date.data:
            self.end_date.errors.append('La fecha de fin debe ser posterior a la fecha de inicio')
            return False
        
        # Validar horarios de visita si están especificados
        if self.visit_start_time.data and self.visit_end_time.data:
            if self.visit_start_time.data >= self.visit_end_time.data:
                self.visit_end_time.errors.append('Hora de fin debe ser posterior a hora de inicio')
                return False
        elif self.visit_start_time.data and not self.visit_end_time.data:
            self.visit_end_time.errors.append('Especifica hora de fin si defines hora de inicio')
            return False
        elif not self.visit_start_time.data and self.visit_end_time.data:
            self.visit_start_time.errors.append('Especifica hora de inicio si defines hora de fin')
            return False
        
        return True
