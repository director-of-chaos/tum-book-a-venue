from models import db, Venue


def init_database(app):
    with app.app_context():
        db.create_all()

        # Add venues if none exist
        if Venue.query.count() == 0:
            venues = [
                Venue(
                    name="TUM Main Hall",
                    description="Large hall used for university events, orientations, and graduations",
                    capacity=500,
                    location="Main Campus - Tudor",
                    amenities="Podium, Projector, PA System, Chairs, Tables, Fans, WiFi Access Point",
                ),
                Venue(
                    name="ICT Boardroom",
                    description="Executive boardroom for IT-related departmental meetings and presentations",
                    capacity=20,
                    location="ICT Building, 2nd Floor",
                    amenities="Conference Table, Projector, Whiteboard, Air Conditioning",
                ),
                Venue(
                    name="Engineering Seminar Room",
                    description="Seminar room used for workshops and faculty briefings",
                    capacity=60,
                    location="Engineering Block",
                    amenities="Projector, Chairs, Blackboard, WiFi Access Point",
                ),
                Venue(
                    name="Library Auditorium",
                    description="Medium-sized auditorium within the library complex used for academic presentations",
                    capacity=120,
                    location="TUM Library Building",
                    amenities="Projector, Chairs, Blackboard, Tables",
                ),
            ]

            for venue in venues:
                db.session.add(venue)
            db.session.commit()
