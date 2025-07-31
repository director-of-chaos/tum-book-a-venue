#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author: Bill

from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    SelectField,
    TextAreaField,
    StringField,
    EmailField,
    SubmitField,
)
# <<< FIX 1: Import the NoneOf validator >>>
from wtforms.validators import DataRequired, Email, Length, NoneOf
from models import Venue

# Helper to generate time choices
def generate_time_choices():
    choices = []
    for hour in range(9, 22): # 9 AM to 9 PM
        choices.append((f"{hour:02d}:00", f"{hour % 12 or 12}:00 {'AM' if hour < 12 else 'PM'}"))
        if hour < 21: # No 9:30 PM end time
             choices.append((f"{hour:02d}:30", f"{hour % 12 or 12}:30 {'AM' if hour < 12 else 'PM'}"))
    return choices


class BookingForm(FlaskForm):
    user_name = StringField("Your Name", validators=[DataRequired(), Length(min=2, max=100)])
    user_email = EmailField("Your Email", validators=[DataRequired(), Email()])
    
    event_date = DateField("Event Date", validators=[DataRequired()], format='%Y-%m-%d')
    
    start_time = SelectField(
        "Start Time",
        choices=generate_time_choices(),
        validators=[DataRequired()],
    )
    end_time = SelectField(
        "End Time",
        choices=generate_time_choices()[1:], # End time can't be the earliest start time
        validators=[DataRequired()],
    )
    
    # <<< FIX 2: Add the NoneOf validator to the list >>>
    venue_id = SelectField(
        "Select Venue", 
        coerce=int, 
        validators=[
            DataRequired(), 
            NoneOf([0], message='Please select a valid venue.')
        ]
    )

    event_title = StringField("Event Title", validators=[DataRequired(), Length(min=5, max=200)])
    event_description = TextAreaField("Event Description")

    def __init__(self, *args, **kwargs):
        super(BookingForm, self).__init__(*args, **kwargs)
        # Populate venue choices dynamically
        self.venue_id.choices = [(v.id, v.name) for v in Venue.query.order_by(Venue.name).all()]
        
        # <<< FIX 3: Change the prompt's value to '0' >>>
        self.venue_id.choices.insert(0, ('0', 'Please select a venue...'))


class AdminResponseForm(FlaskForm):
    admin_comments = TextAreaField(
        "Comments/Reason",
        validators=[Length(max=500)],
        render_kw={"placeholder": "Add comments or reason for rejection (optional)"},
    )
    approve = SubmitField("Approve Booking", render_kw={"class": "btn btn-success"})
    reject = SubmitField("Reject Booking", render_kw={"class": "btn btn-danger"})