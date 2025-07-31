from flask import current_app, session, request
import json
import os
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

class CalendarService:
    def __init__(self):
        self.client_id = current_app.config['GOOGLE_CLIENT_ID']
        self.client_secret = current_app.config['GOOGLE_CLIENT_SECRET']
        self.redirect_uri = current_app.config['REDIRECT_URI']
        
        # Store OAuth config as a temporary file to fix the OAuth error
        self.client_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": [self.redirect_uri]
            }
        }
    
    def get_authorization_url(self):
        """Get Google OAuth authorization URL"""
        # Write client config to temporary file
        config_file = 'temp_client_secrets.json'
        with open(config_file, 'w') as f:
            json.dump(self.client_config, f)
        
        try:
            flow = Flow.from_client_secrets_file(
                config_file,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            flow.redirect_uri = self.redirect_uri
            
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
            
            session['state'] = state
            return authorization_url
        finally:
            # Clean up temporary file
            if os.path.exists(config_file):
                os.remove(config_file)
    
    def handle_oauth_callback(self):
        """Handle OAuth callback and return credentials"""
        # Write client config to temporary file
        config_file = 'temp_client_secrets.json'
        with open(config_file, 'w') as f:
            json.dump(self.client_config, f)
        
        try:
            flow = Flow.from_client_secrets_file(
                config_file,
                scopes=['https://www.googleapis.com/auth/calendar'],
                state=session.get('state')
            )
            flow.redirect_uri = self.redirect_uri
            
            # Get authorization response
            authorization_response = request.url
            flow.fetch_token(authorization_response=authorization_response)
            
            return flow.credentials
        finally:
            # Clean up temporary file
            if os.path.exists(config_file):
                os.remove(config_file)
    
    def create_calendar_event(self, booking, credentials):
        """Create a calendar event for the booking"""
        try:
            service = build('calendar', 'v3', credentials=credentials)
            
            event = {
                'summary': booking.event_title,
                'description': f"{booking.event_description}\nVenue: {booking.venue.name}\nReference: {booking.reference_number}",
                'start': {
                    'dateTime': f"{booking.event_date}T{booking.start_time}:00",
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': f"{booking.event_date}T{booking.end_time}:00",
                    'timeZone': 'UTC',
                },
                'location': booking.venue.location,
            }
            
            event = service.events().insert(calendarId='primary', body=event).execute()
            return True, "Event added to calendar successfully"
        except Exception as e:
            current_app.logger.error(f"Error creating calendar event: {e}")
            return False, f"Error adding to calendar: {str(e)}"