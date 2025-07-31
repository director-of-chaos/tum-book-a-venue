from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, make_response
from datetime import datetime
import uuid
import csv
import io
from models import db, Venue, BookingRequest, generate_reference_number
from forms import BookingForm, AdminResponseForm
from email_service import send_admin_notification, send_user_notification
from calendar_service import CalendarService

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/book', methods=['GET', 'POST'])
def book_venue():
    form = BookingForm()
    
    if form.validate_on_submit():
        # Generate unique booking ID and reference number
        booking_id = str(uuid.uuid4())
        reference_number = generate_reference_number()
        
        # Ensure reference number is unique
        while BookingRequest.query.filter_by(reference_number=reference_number).first():
            reference_number = generate_reference_number()
        
        # Create booking request
        booking = BookingRequest(
            booking_id=booking_id,
            reference_number=reference_number,
            user_name=form.user_name.data,
            user_email=form.user_email.data,
            venue_id=form.venue_id.data,
            event_date=form.event_date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            event_title=form.event_title.data,
            event_description=form.event_description.data
        )
        
        db.session.add(booking)
        db.session.commit()
        
        # Send email to admin
        if send_admin_notification(booking):
            flash(f'Your booking request has been submitted! Your reference number is {reference_number}. You will receive an email confirmation shortly.', 'success')
        else:
            flash(f'Booking submitted with reference {reference_number}, but email notification failed. Please contact admin directly.', 'warning')
        
        return redirect(url_for('main.booking_status', reference=reference_number))
    
    return render_template('book.html', form=form)

@main.route('/venues')
def view_venues():
    selected_date = request.args.get('date')
    venues = Venue.query.all()
    
    if selected_date:
        try:
            date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
            booked_venues = db.session.query(BookingRequest.venue_id).filter(
                BookingRequest.event_date == date_obj,
                BookingRequest.status == 'approved'
            ).subquery()
            
            available_venues = Venue.query.filter(~Venue.id.in_(booked_venues)).all()
            return render_template('venues.html', venues=available_venues, selected_date=selected_date)
        except ValueError:
            pass
    
    return render_template('venues.html', venues=venues, selected_date=selected_date)

@main.route('/booking/<reference>')
def booking_status(reference):
    booking = BookingRequest.query.filter_by(reference_number=reference).first_or_404()
    return render_template('booking_status.html', booking=booking)

@main.route('/admin/review/<booking_id>', methods=['GET', 'POST'])
def admin_review(booking_id):
    """Admin review page with form for response"""
    booking = BookingRequest.query.filter_by(booking_id=booking_id).first_or_404()
    
    # Check if already processed
    if booking.is_processed:
        return render_template('admin_already_processed.html', booking=booking)
    
    form = AdminResponseForm()
    
    if form.validate_on_submit():
        # Determine action based on which button was clicked
        if form.approve.data:
            booking.status = 'approved'
            action = 'approved'
        elif form.reject.data:
            booking.status = 'rejected'
            action = 'rejected'
        else:
            flash('Invalid action', 'error')
            return redirect(url_for('main.admin_review', booking_id=booking_id))
        
        # Update booking
        booking.admin_response = form.admin_comments.data or f"Request {action} by admin"
        booking.processed_at = datetime.utcnow()
        booking.is_processed = True
        db.session.commit()
        
        # Send notification to user
        if send_user_notification(booking):
            return render_template('admin_success.html', booking=booking, action=action)
        else:
            return render_template('admin_success.html', booking=booking, action=action, email_error=True)
    
    return render_template('admin_review.html', booking=booking, form=form)

@main.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard with statistics"""
    total_bookings = BookingRequest.query.count()
    pending_bookings = BookingRequest.query.filter_by(status='pending').count()
    approved_bookings = BookingRequest.query.filter_by(status='approved').count()
    rejected_bookings = BookingRequest.query.filter_by(status='rejected').count()
    
    # Recent bookings
    recent_bookings = BookingRequest.query.order_by(BookingRequest.created_at.desc()).limit(10).all()
    
    # Popular venues
    venue_stats = db.session.query(
        Venue.name,
        db.func.count(BookingRequest.id).label('booking_count')
    ).join(BookingRequest).group_by(Venue.id, Venue.name).order_by(db.func.count(BookingRequest.id).desc()).all()
    
    stats = {
        'total': total_bookings,
        'pending': pending_bookings,
        'approved': approved_bookings,
        'rejected': rejected_bookings
    }
    
    return render_template('admin_dashboard.html', 
                         stats=stats, 
                         recent_bookings=recent_bookings,
                         venue_stats=venue_stats)

@main.route('/admin/export')
def export_bookings():
    """Export all bookings to CSV"""
    bookings = BookingRequest.query.order_by(BookingRequest.created_at.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Reference Number', 'Customer Name', 'Email', 'Event Title', 
        'Venue', 'Event Date', 'Start Time', 'End Time', 'Status', 
        'Created At', 'Processed At', 'Admin Response'
    ])
    
    # Write data
    for booking in bookings:
        writer.writerow([
            booking.reference_number,
            booking.user_name,
            booking.user_email,
            booking.event_title,
            booking.venue.name,
            booking.event_date,
            booking.start_time,
            booking.end_time,
            booking.status,
            booking.created_at.strftime('%Y-%m-%d %H:%M:%S') if booking.created_at else '',
            booking.processed_at.strftime('%Y-%m-%d %H:%M:%S') if booking.processed_at else '',
            booking.admin_response or ''
        ])
    
    output.seek(0)
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=venue_bookings_{datetime.now().strftime("%Y%m%d")}.csv'
    
    return response

@main.route('/add_to_calendar/<booking_id>')
def add_to_calendar(booking_id):
    """Redirect to Google Calendar OAuth"""
    booking = BookingRequest.query.filter_by(booking_id=booking_id).first_or_404()
    
    if booking.status != 'approved':
        flash('Only approved bookings can be added to calendar.', 'error')
        return redirect(url_for('main.booking_status', reference=booking.reference_number))
    
    # Store booking ID in session
    session['booking_id'] = booking_id
    
    calendar_service = CalendarService()
    try:
        authorization_url = calendar_service.get_authorization_url()
        return redirect(authorization_url)
    except Exception as e:
        flash(f'Error setting up calendar integration: {str(e)}', 'error')
        return redirect(url_for('main.booking_status', reference=booking.reference_number))

@main.route('/oauth2callback')
def oauth2callback():
    """Handle OAuth callback and create calendar event"""
    calendar_service = CalendarService()
    
    try:
        credentials = calendar_service.handle_oauth_callback()
        
        # Get booking details
        booking_id = session.get('booking_id')
        if not booking_id:
            flash('Session expired. Please try again.', 'error')
            return redirect(url_for('main.index'))
            
        booking = BookingRequest.query.filter_by(booking_id=booking_id).first_or_404()
        
        # Create calendar event
        success, message = calendar_service.create_calendar_event(booking, credentials)
        
        if success:
            flash('Event added to your Google Calendar successfully!', 'success')
        else:
            flash(message, 'error')
            
    except Exception as e:
        flash(f'Error processing calendar request: {str(e)}', 'error')
    
    booking_id = session.get('booking_id')
    if booking_id:
        booking = BookingRequest.query.filter_by(booking_id=booking_id).first()
        if booking:
            return redirect(url_for('main.booking_status', reference=booking.reference_number))
    
    return redirect(url_for('main.index'))