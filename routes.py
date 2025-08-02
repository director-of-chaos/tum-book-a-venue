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
from datetime import datetime, date as date_type, time
import uuid
import csv, json
import io
from models import db, Venue, BookingRequest, generate_reference_number
from forms import BookingForm, AdminResponseForm
from email_service import send_admin_notification, send_user_notification
from calendar_service import CalendarService

main = Blueprint("main", __name__)


# <<< FIX: The helper function must be defined here, at the module level, before it is used. >>>
def _get_default_start_time():
    """Returns the next available time slot as a string in HH:MM format."""
    now = datetime.now()

    # Define the valid time choices, which should match the form
    valid_times = [
        "09:00",
        "09:30",
        "10:00",
        "10:30",
        "11:00",
        "11:30",
        "12:00",
        "12:30",
        "13:00",
        "13:30",
        "14:00",
        "14:30",
        "15:00",
        "15:30",
        "16:00",
        "16:30",
        "17:00",
        "17:30",
        "18:00",
        "18:30",
        "19:00",
        "19:30",
        "20:00",
        "20:30",
        "21:00",
    ]

    # For today, find the next available time slot (with 30-minute buffer)
    today = now.date()
    current_time_minutes = now.hour * 60 + now.minute + 30  # Add 30-minute buffer

    for time_choice in valid_times:
        hour, minute = map(int, time_choice.split(":"))
        choice_time_minutes = hour * 60 + minute

        if choice_time_minutes > current_time_minutes:
            return time_choice

    # If it's too late in the day, default to the first available time
    return valid_times[0]


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/book", methods=["GET", "POST"])
def book_venue():
    if request.method == "POST":
        form = BookingForm(request.form)
        if form.validate():
            # Convert form times to time objects for comparison
            new_start_time = datetime.strptime(form.start_time.data, "%H:%M").time()
            new_end_time = datetime.strptime(form.end_time.data, "%H:%M").time()

            # Find all approved bookings for the same venue and date
            conflicting_bookings = BookingRequest.query.filter(
                BookingRequest.venue_id == form.venue_id.data,
                BookingRequest.event_date == form.event_date.data,
                BookingRequest.status == "approved",
            ).all()

            # Check for time overlap
            for approved_booking in conflicting_bookings:
                existing_start = datetime.strptime(
                    approved_booking.start_time, "%H:%M"
                ).time()
                existing_end = datetime.strptime(
                    approved_booking.end_time, "%H:%M"
                ).time()

                # Overlap condition: (StartA < EndB) and (StartB < EndA)
                if new_start_time < existing_end and existing_start < new_end_time:
                    flash(
                        f"The selected time slot ({form.start_time.data} - {form.end_time.data}) conflicts with an existing booking. Please choose a different time.",
                        "danger",
                    )

                    # We need to re-render the page with an error, so we need the preselected_venue
                    preselected_venue = Venue.query.get(form.venue_id.data)
                    # We also need to pass the booked slots again for the frontend to display
                    booked_slots = []
                    for b in conflicting_bookings:
                        booked_slots.append({"start": b.start_time, "end": b.end_time})

                    return render_template(
                        "book.html",
                        form=form,
                        preselected_venue=preselected_venue,
                        booked_slots_json=json.dumps(booked_slots),
                    )

            # If no conflicts, proceed to create the booking
            booking_id = str(uuid.uuid4())
            reference_number = generate_reference_number()
            while BookingRequest.query.filter_by(
                reference_number=reference_number
            ).first():
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
            send_admin_notification(booking)
            flash(
                f"Your booking request has been submitted! Your reference number is {reference_number}.",
                "success",
            )
            return redirect(url_for("main.booking_status", reference=reference_number))

    else:  # GET Request
        form = BookingForm()
        form.venue_id.data = request.args.get("venue", type=int)

        date_str = request.args.get("date")
        if date_str:
            form.event_date.data = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            form.event_date.data = date_type.today()

        if form.event_date.data == date_type.today():
            form.start_time.data = _get_default_start_time()
        else:
            form.start_time.data = "09:00"

    # This runs for GET requests and failed POSTs
    preselected_venue = None
    booked_slots = []
    if form.venue_id.data:
        preselected_venue = Venue.query.get(form.venue_id.data)
        if preselected_venue and form.event_date.data:
            bookings = BookingRequest.query.filter_by(
                venue_id=form.venue_id.data,
                event_date=form.event_date.data,
                status="approved",
            ).all()
            for b in bookings:
                booked_slots.append({"start": b.start_time, "end": b.end_time})

    return render_template(
        "book.html",
        form=form,
        preselected_venue=preselected_venue,
        booked_slots_json=json.dumps(booked_slots),
    )


@main.route("/venues")
def view_venues():
    selected_date = request.args.get("date")
    venues = Venue.query.order_by(Venue.name).all()
    today = date_type.today().isoformat()
    booked_venue_ids = set()  # Use a set for efficient lookups

    if selected_date:
        try:
            date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
            # Find IDs of venues that are booked and approved on the selected date
            booked_venue_ids = {
                b.venue_id
                for b in BookingRequest.query.filter_by(
                    event_date=date_obj, status="approved"
                ).all()
            }
        except ValueError:
            flash("Invalid date format provided.", "danger")
            # Fall through to show all venues

    return render_template(
        "venues.html",
        venues=venues,
        selected_date=selected_date,
        today=today,
        booked_venue_ids=booked_venue_ids,  # Pass the set of booked IDs
    )


@main.route("/booking/<reference>")
def booking_status(reference):
    booking = BookingRequest.query.filter_by(reference_number=reference).first_or_404()
    return render_template("booking_status.html", booking=booking)


@main.route("/api/booking-status/<reference>")
def api_booking_status(reference):
    """API endpoint to get the latest booking status."""
    booking = BookingRequest.query.filter_by(reference_number=reference).first_or_404()

    return jsonify(
        {"status": booking.status, "admin_response": booking.admin_response or ""}
    )


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
