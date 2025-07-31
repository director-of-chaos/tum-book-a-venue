from flask import current_app, url_for, render_template_string
from flask_mail import Mail, Message

mail = Mail()

def send_admin_notification(booking):
    """Send HTML email notification to admin about new booking request"""
    try:
        msg = Message(
            subject=f'New Venue Booking Request - {booking.event_title}',
            sender=current_app.config['MAIL_USERNAME'],
            recipients=[current_app.config['ADMIN_EMAIL']]
        )
        
        review_url = url_for('main.admin_review', booking_id=booking.booking_id, _external=True)
        
        # HTML email template
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                .container { max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }
                .content { padding: 30px; }
                .booking-details { background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
                .detail-row { display: flex; justify-content: space-between; margin: 10px 0; }
                .label { font-weight: bold; color: #495057; }
                .value { color: #212529; }
                .action-buttons { text-align: center; margin: 30px 0; }
                .btn { display: inline-block; padding: 12px 30px; margin: 0 10px; text-decoration: none; border-radius: 5px; font-weight: bold; }
                .btn-review { background-color: #007bff; color: white; }
                .footer { background-color: #f8f9fa; padding: 20px; text-align: center; color: #6c757d; font-size: 14px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏢 New Venue Booking Request</h1>
                    <p>A new booking request requires your attention</p>
                </div>
                
                <div class="content">
                    <div class="booking-details">
                        <h3>📋 Booking Details</h3>
                        <div class="detail-row">
                            <span class="label">Reference:</span>
                            <span class="value">{{ booking.reference_number }}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Customer:</span>
                            <span class="value">{{ booking.user_name }}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Email:</span>
                            <span class="value">{{ booking.user_email }}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Event:</span>
                            <span class="value">{{ booking.event_title }}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Venue:</span>
                            <span class="value">{{ booking.venue.name }}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Date:</span>
                            <span class="value">{{ booking.event_date.strftime('%B %d, %Y') }}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Time:</span>
                            <span class="value">{{ booking.start_time }} - {{ booking.end_time }}</span>
                        </div>
                        {% if booking.event_description %}
                        <div class="detail-row">
                            <span class="label">Description:</span>
                            <span class="value">{{ booking.event_description }}</span>
                        </div>
                        {% endif %}
                    </div>
                    
                    <div class="action-buttons">
                        <a href="{{ review_url }}" class="btn btn-review">📝 Review & Respond</a>
                    </div>
                    
                    <p style="text-align: center; color: #6c757d; font-size: 14px;">
                        Click the button above to review the booking and provide your response with optional comments.
                    </p>
                </div>
                
                <div class="footer">
                    <p>Venue Booking System | Automated Notification</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.html = render_template_string(html_template, booking=booking, review_url=review_url)
        
        # Plain text fallback
        msg.body = f"""
New venue booking request received:

Reference: {booking.reference_number}
Customer: {booking.user_name} ({booking.user_email})
Event: {booking.event_title}
Venue: {booking.venue.name}
Date: {booking.event_date}
Time: {booking.start_time} - {booking.end_time}
Description: {booking.event_description}

To review and respond: {review_url}
        """
        
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Error sending admin notification: {e}")
        return False

def send_user_notification(booking):
    """Send HTML email notification to user about booking status"""
    try:
        status_text = "approved" if booking.status == "approved" else "rejected"
        msg = Message(
            subject=f'Venue Booking {status_text.title()} - {booking.event_title}',
            sender=current_app.config['MAIL_USERNAME'],
            recipients=[booking.user_email]
        )
        
        # HTML email template
        if booking.status == "approved":
            calendar_url = url_for('main.add_to_calendar', booking_id=booking.booking_id, _external=True)
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                    .container { max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                    .header { background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 20px; text-align: center; }
                    .content { padding: 30px; }
                    .booking-details { background-color: #d4edda; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #28a745; }
                    .btn-calendar { display: inline-block; background-color: #ffc107; color: #212529; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 20px 0; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>✅ Booking Approved!</h1>
                        <p>Great news! Your venue booking has been confirmed.</p>
                    </div>
                    <div class="content">
                        <p>Hello {{ booking.user_name }},</p>
                        <p>We're excited to confirm that your venue booking has been <strong>approved</strong>!</p>
                        
                        <div class="booking-details">
                            <h3>📋 Your Booking Details</h3>
                            <p><strong>Reference:</strong> {{ booking.reference_number }}</p>
                            <p><strong>Event:</strong> {{ booking.event_title }}</p>
                            <p><strong>Venue:</strong> {{ booking.venue.name }}</p>
                            <p><strong>Date:</strong> {{ booking.event_date.strftime('%B %d, %Y') }}</p>
                            <p><strong>Time:</strong> {{ booking.start_time }} - {{ booking.end_time }}</p>
                        </div>
                        
                        {% if booking.admin_response %}
                        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                            <strong>Additional Comments:</strong><br>
                            {{ booking.admin_response }}
                        </div>
                        {% endif %}
                        
                        <div style="text-align: center;">
                            <a href="{{ calendar_url }}" class="btn-calendar">📅 Add to Google Calendar</a>
                        </div>
                        
                        <p>Thank you for choosing our venue!</p>
                    </div>
                </div>
            </body>
            </html>
            """
            msg.html = render_template_string(html_template, booking=booking, calendar_url=calendar_url)
        else:
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                    .container { max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                    .header { background: linear-gradient(135deg, #dc3545 0%, #e74c3c 100%); color: white; padding: 20px; text-align: center; }
                    .content { padding: 30px; }
                    .booking-details { background-color: #f8d7da; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #dc3545; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>❌ Booking Not Approved</h1>
                        <p>We're sorry, but your venue booking request cannot be approved at this time.</p>
                    </div>
                    <div class="content">
                        <p>Hello {{ booking.user_name }},</p>
                        <p>Unfortunately, we cannot approve your venue booking request.</p>
                        
                        <div class="booking-details">
                            <h3>📋 Your Booking Details</h3>
                            <p><strong>Reference:</strong> {{ booking.reference_number }}</p>
                            <p><strong>Event:</strong> {{ booking.event_title }}</p>
                            <p><strong>Venue:</strong> {{ booking.venue.name }}</p>
                            <p><strong>Date:</strong> {{ booking.event_date.strftime('%B %d, %Y') }}</p>
                            <p><strong>Time:</strong> {{ booking.start_time }} - {{ booking.end_time }}</p>
                        </div>
                        
                        {% if booking.admin_response %}
                        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                            <strong>Reason:</strong><br>
                            {{ booking.admin_response }}
                        </div>
                        {% endif %}
                        
                        <p>Please feel free to submit another request for a different date or venue.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            msg.html = render_template_string(html_template, booking=booking)
        
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Error sending user notification: {e}")
        return False