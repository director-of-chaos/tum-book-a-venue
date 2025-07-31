#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author: Bill

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
    make_response,
)
from datetime import datetime, date as date_type, timedelta
import uuid
import csv
import io
from models import db, Venue, BookingRequest, generate_reference_number
from forms import BookingForm, AdminResponseForm
from email_service import send_admin_notification, send_user_notification
from calendar_service import CalendarService

main = Blueprint("main", __name__)


# <<< FIX: The helper function must be defined here, at the module level, before it is used. >>>
def _get_default_start_time():
    """Returns the next full hour as a string in HH:00 format."""
    now = datetime.now()
    # If it's 15:30, next hour is 16:00. If 15:59, next hour is 16:00.
    next_hour_dt = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    
    # Define the valid time choices, which should match the form
    valid_times = [
        "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30", 
        "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", 
        "17:00", "17:30", "18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00"
    ]

    # Find the closest valid time that is in the future
    for time_choice in valid_times:
        hour, minute = map(int, time_choice.split(':'))
        choice_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if choice_dt > now:
            return time_choice
            
    # If it's too late in the day, default to the first available time on the next day
    return valid_times[0]


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/book", methods=["GET", "POST"])
def book_venue():
    # <<< FIX 1: Instantiate the form once. It will auto-populate from request.form on POST. >>>
    form = BookingForm()
    
    # <<< FIX 2: The validate_on_submit() method now works on the correct data. >>>
    if form.validate_on_submit():
        # This block is now correctly reached on a successful POST.
        booking_id = str(uuid.uuid4())
        reference_number = generate_reference_number()

        while BookingRequest.query.filter_by(reference_number=reference_number).first():
            reference_number = generate_reference_number()

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
            event_description=form.event_description.data,
        )

        db.session.add(booking)
        db.session.commit()

        if send_admin_notification(booking):
            flash(f"Your booking request has been submitted! Your reference number is {reference_number}. You will receive an email confirmation shortly.", "success")
        else:
            flash(f"Booking submitted with reference {reference_number}, but email notification failed. Please contact admin directly.", "warning")

        return redirect(url_for("main.booking_status", reference=reference_number))

    # <<< FIX 3: This part of the code now runs on a GET request OR a failed POST. >>>
    # On a GET request, we manually populate the form with our defaults.
    # On a failed POST, WTForms automatically keeps the user's invalid data, so we don't touch it.
    if request.method == "GET":
        # Pre-populate venue
        venue_id = request.args.get('venue', type=int)
        if venue_id:
            form.venue_id.data = venue_id

        # Pre-populate date
        date_str = request.args.get('date')
        if date_str:
            try:
                form.event_date.data = datetime.strptime(date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                form.event_date.data = date_type.today()
        else:
            form.event_date.data = date_type.today()
        
        # Pre-populate time
        form.start_time.data = _get_default_start_time()

    # We need the preselected_venue object for template display logic
    # This must be determined *after* the form is populated (either by GET or by failed POST)
    preselected_venue = None
    if form.venue_id.data and form.venue_id.data > 0:
        preselected_venue = Venue.query.get(form.venue_id.data)
        
    return render_template("book.html", form=form, preselected_venue=preselected_venue)


@main.route("/venues")
def view_venues():
    selected_date = request.args.get("date")
    venues = Venue.query.order_by(Venue.name).all()
    today = date_type.today().isoformat() # Pass today's date to template for min attribute

    if selected_date:
        try:
            date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
            # Find IDs of venues that are booked and approved on the selected date
            booked_venue_ids = {
                b.venue_id for b in BookingRequest.query.filter_by(
                    event_date=date_obj, status='approved'
                ).all()
            }
            
            # Filter out the booked venues
            available_venues = [v for v in venues if v.id not in booked_venue_ids]

            return render_template(
                "venues.html", venues=available_venues, selected_date=selected_date, today=today
            )
        except ValueError:
            flash("Invalid date format provided.", "danger")
            # Fall through to show all venues if date is invalid

    return render_template("venues.html", venues=venues, selected_date=selected_date, today=today)


# (The rest of your routes.py file remains unchanged...)

@main.route("/booking/<reference>")
def booking_status(reference):
    booking = BookingRequest.query.filter_by(reference_number=reference).first_or_404()
    return render_template("booking_status.html", booking=booking)


@main.route("/admin/review/<booking_id>", methods=["GET", "POST"])
def admin_review(booking_id):
    """Admin review page with form for response"""
    booking = BookingRequest.query.filter_by(booking_id=booking_id).first_or_404()

    # Check if already processed
    if booking.is_processed:
        return render_template("admin/admin_already_processed.html", booking=booking)

    form = AdminResponseForm()

    if form.validate_on_submit():
        # Determine action based on which button was clicked
        if form.approve.data:
            booking.status = "approved"
            action = "approved"
        elif form.reject.data:
            booking.status = "rejected"
            action = "rejected"
        else:
            flash("Invalid action", "error")
            return redirect(url_for("main.admin_review", booking_id=booking_id))

        # Update booking
        booking.admin_response = (
            form.admin_comments.data or f"Request {action} by admin"
        )
        booking.processed_at = datetime.utcnow()
        booking.is_processed = True
        db.session.commit()

        # Send notification to user
        if send_user_notification(booking):
            return render_template(
                "admin/admin_success.html", booking=booking, action=action
            )
        else:
            return render_template(
                "admin/admin_success.html",
                booking=booking,
                action=action,
                email_error=True,
            )

    return render_template("admin/admin_review.html", booking=booking, form=form)


@main.route("/admin/dashboard")
def admin_dashboard():
    """Admin dashboard with statistics"""
    total_bookings = BookingRequest.query.count()
    pending_bookings = BookingRequest.query.filter_by(status="pending").count()
    approved_bookings = BookingRequest.query.filter_by(status="approved").count()
    rejected_bookings = BookingRequest.query.filter_by(status="rejected").count()

    # Recent bookings
    recent_bookings = (
        BookingRequest.query.order_by(BookingRequest.created_at.desc()).limit(10).all()
    )

    # Popular venues
    venue_stats = (
        db.session.query(
            Venue.name, db.func.count(BookingRequest.id).label("booking_count")
        )
        .join(BookingRequest)
        .group_by(Venue.id, Venue.name)
        .order_by(db.func.count(BookingRequest.id).desc())
        .all()
    )

    stats = {
        "total": total_bookings,
        "pending": pending_bookings,
        "approved": approved_bookings,
        "rejected": rejected_bookings,
    }

    return render_template(
        "admin/admin_dashboard.html",
        stats=stats,
        recent_bookings=recent_bookings,
        venue_stats=venue_stats,
    )


@main.route("/admin/export")
def export_bookings():
    """Export all bookings to CSV"""
    bookings = BookingRequest.query.order_by(BookingRequest.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(
        [
            "Reference Number",
            "Customer Name",
            "Email",
            "Event Title",
            "Venue",
            "Event Date",
            "Start Time",
            "End Time",
            "Status",
            "Created At",
            "Processed At",
            "Admin Response",
        ]
    )

    # Write data
    for booking in bookings:
        writer.writerow(
            [
                booking.reference_number,
                booking.user_name,
                booking.user_email,
                booking.event_title,
                booking.venue.name,
                booking.event_date,
                booking.start_time,
                booking.end_time,
                booking.status,
                booking.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if booking.created_at
                else "",
                booking.processed_at.strftime("%Y-%m-%d %H:%M:%S")
                if booking.processed_at
                else "",
                booking.admin_response or "",
            ]
        )

    output.seek(0)

    # Create response
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = (
        f"attachment; filename=venue_bookings_{datetime.now().strftime('%Y%m%d')}.csv"
    )

    return response


@main.route("/add_to_calendar/<booking_id>")
def add_to_calendar(booking_id):
    """Redirect to Google Calendar OAuth"""
    booking = BookingRequest.query.filter_by(booking_id=booking_id).first_or_404()

    if booking.status != "approved":
        flash("Only approved bookings can be added to calendar.", "error")
        return redirect(
            url_for("main.booking_status", reference=booking.reference_number)
        )

    # Store booking ID in session
    session["booking_id"] = booking_id

    calendar_service = CalendarService()
    try:
        authorization_url = calendar_service.get_authorization_url()
        return redirect(authorization_url)
    except Exception as e:
        flash(f"Error setting up calendar integration: {str(e)}", "error")
        return redirect(
            url_for("main.booking_status", reference=booking.reference_number)
        )


@main.route("/oauth2callback")
def oauth2callback():
    """Handle OAuth callback and create calendar event"""
    calendar_service = CalendarService()

    try:
        credentials = calendar_service.handle_oauth_callback()

        # Get booking details
        booking_id = session.get("booking_id")
        if not booking_id:
            flash("Session expired. Please try again.", "error")
            return redirect(url_for("main.index"))

        booking = BookingRequest.query.filter_by(booking_id=booking_id).first_or_404()

        # Create calendar event
        success, message = calendar_service.create_calendar_event(booking, credentials)

        if success:
            flash("Event added to your Google Calendar successfully!", "success")
        else:
            flash(message, "error")

    except Exception as e:
        flash(f"Error processing calendar request: {str(e)}", "error")

    booking_id = session.get("booking_id")
    if booking_id:
        booking = BookingRequest.query.filter_by(booking_id=booking_id).first()
        if booking:
            return redirect(
                url_for("main.booking_status", reference=booking.reference_number)
            )

    return redirect(url_for("main.index"))