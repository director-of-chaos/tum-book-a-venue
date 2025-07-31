#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author: Bill

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random
import string

db = SQLAlchemy()


def generate_reference_number():
    """Generate user-friendly reference number"""
    prefix = "VB"
    suffix = "".join(random.choices(string.digits, k=6))
    return f"{prefix}{suffix}"


class Venue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    capacity = db.Column(db.Integer)
    location = db.Column(db.String(200))
    amenities = db.Column(db.Text)

    def __repr__(self):
        return f"<Venue {self.name}>"

    def to_dict(self):
        """Converts the Venue object to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "capacity": self.capacity,
            "location": self.location,
            "amenities": self.amenities,
        }


class BookingRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.String(36), unique=True, nullable=False)  # Internal UUID
    reference_number = db.Column(
        db.String(20), unique=True, nullable=False
    )  # User-friendly reference
    user_name = db.Column(db.String(100), nullable=False)
    user_email = db.Column(db.String(120), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey("venue.id"), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.String(10), nullable=False)
    end_time = db.Column(db.String(10), nullable=False)
    event_title = db.Column(db.String(200), nullable=False)
    event_description = db.Column(db.Text)
    status = db.Column(db.String(20), default="pending")  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)  # When admin responded
    admin_response = db.Column(db.Text)
    is_processed = db.Column(db.Boolean, default=False)  # Prevent duplicate responses

    venue = db.relationship("Venue", backref=db.backref("bookings", lazy=True))

    def __repr__(self):
        return f"<BookingRequest {self.reference_number}>"
