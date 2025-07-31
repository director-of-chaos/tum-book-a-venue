from models import db, Venue

def init_database(app):
    """Initialize database with sample data"""
    with app.app_context():
        db.create_all()
        
        # Add sample venues if none exist
        if Venue.query.count() == 0:
            venues = [
                Venue(
                    name="Grand Ballroom",
                    description="Elegant ballroom perfect for weddings and formal events",
                    capacity=200,
                    location="123 Main St, Downtown",
                    amenities="Sound system, lighting, catering kitchen, dance floor"
                ),
                Venue(
                    name="Conference Center",
                    description="Modern conference facility with AV equipment",
                    capacity=100,
                    location="456 Business Ave, Corporate District",
                    amenities="Projectors, microphones, WiFi, catering service"
                ),
                Venue(
                    name="Garden Pavilion",
                    description="Beautiful outdoor pavilion surrounded by gardens",
                    capacity=150,
                    location="789 Park Lane, Garden District",
                    amenities="Outdoor seating, gazebo, garden views, parking"
                ),
                Venue(
                    name="Meeting Room A",
                    description="Intimate meeting space for small gatherings",
                    capacity=25,
                    location="321 Office Blvd, Business Center",
                    amenities="Conference table, whiteboard, coffee station"
                )
            ]
            
            for venue in venues:
                db.session.add(venue)
            db.session.commit()