from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, TextAreaField, StringField, EmailField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from models import Venue

class BookingForm(FlaskForm):
    user_name = StringField('Your Name', validators=[DataRequired()])
    user_email = EmailField('Your Email', validators=[DataRequired(), Email()])
    event_date = DateField('Event Date', validators=[DataRequired()])
    start_time = SelectField('Start Time', choices=[
        ('09:00', '9:00 AM'), ('10:00', '10:00 AM'), ('11:00', '11:00 AM'),
        ('12:00', '12:00 PM'), ('13:00', '1:00 PM'), ('14:00', '2:00 PM'),
        ('15:00', '3:00 PM'), ('16:00', '4:00 PM'), ('17:00', '5:00 PM'),
        ('18:00', '6:00 PM'), ('19:00', '7:00 PM'), ('20:00', '8:00 PM')
    ], validators=[DataRequired()])
    end_time = SelectField('End Time', choices=[
        ('10:00', '10:00 AM'), ('11:00', '11:00 AM'), ('12:00', '12:00 PM'),
        ('13:00', '1:00 PM'), ('14:00', '2:00 PM'), ('15:00', '3:00 PM'),
        ('16:00', '4:00 PM'), ('17:00', '5:00 PM'), ('18:00', '6:00 PM'),
        ('19:00', '7:00 PM'), ('20:00', '8:00 PM'), ('21:00', '9:00 PM')
    ], validators=[DataRequired()])
    venue_id = SelectField('Select Venue', coerce=int, validators=[DataRequired()])
    event_title = StringField('Event Title', validators=[DataRequired()])
    event_description = TextAreaField('Event Description')
    
    def __init__(self, *args, **kwargs):
        super(BookingForm, self).__init__(*args, **kwargs)
        self.venue_id.choices = [(v.id, v.name) for v in Venue.query.all()]

class AdminResponseForm(FlaskForm):
    admin_comments = TextAreaField('Comments/Reason', 
                                 validators=[Length(max=500)],
                                 render_kw={"placeholder": "Add comments or reason for rejection (optional)"})
    approve = SubmitField('Approve Booking', render_kw={"class": "btn btn-success"})
    reject = SubmitField('Reject Booking', render_kw={"class": "btn btn-danger"})