#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author: Bill

from models import db, Venue


def init_database(app):
    """Initialize database with TUM-specific venues"""
    with app.app_context():
        db.create_all()

        # Add TUM venues if none exist
        if Venue.query.count() == 0:
            venues = [
                Venue(
                    name="TUM Main Hall",
                    description="Large hall used for university events, orientations, and graduations",
                    capacity=500,
                    location="Main Campus - Tudor",
                    amenities="Stage, projector, PA system, chairs, fans",
                ),
                Venue(
                    name="ICT Boardroom",
                    description="Executive boardroom for IT-related departmental meetings and presentations",
                    capacity=20,
                    location="ICT Building, 2nd Floor",
                    amenities="Conference table, projector, whiteboard, internet",
                ),
                Venue(
                    name="Engineering Seminar Room",
                    description="Seminar room used for workshops and faculty briefings",
                    capacity=60,
                    location="Engineering Block",
                    amenities="Projector, seating, whiteboard, power outlets",
                ),
                Venue(
                    name="Library Auditorium",
                    description="Medium-sized auditorium within the library complex used for academic presentations",
                    capacity=120,
                    location="TUM Library Building",
                    amenities="Projector, microphone, air conditioning, seating",
                ),
            ]

            for venue in venues:
                db.session.add(venue)
            db.session.commit()
