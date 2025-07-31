# TUM Book a Venue

Just another "book a venue" system.

[!CAUTION]
> It's a prototype created within 30 minutes and in no way ready for prod. It's just meant to show the basic idea and to be used as a starting point for a real system.

## 🌟 Features

- **User-Friendly Booking Interface**
  - Simple form for submitting venue booking requests
  - Real-time availability checking
  - Email notifications for booking status updates

- **Admin Dashboard**
  - Review and manage booking requests
  - Approve or reject bookings with custom messages
  - Export booking data to CSV

- **Calendar Integration**
  - Google Calendar integration for approved bookings
  - Automated event creation
  - Email notifications with calendar invites

- **Reference System**
  - Unique reference number for each booking
  - Status tracking for all requests
  - Email notifications at each status change

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Google Cloud Platform account (for OAuth)
- SMTP server (for email notifications). Just a gmail account is fine for now.
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/indeqs/tum-book-a-venue.git
   cd tum-book-a-venue
   ```

2. **Create a virtual environment**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ```

3. **Install dependencies**
   ```bash
   uv pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory with the following variables:

   ```bash
   SECRET_KEY="your-secret-key" # Generate a random secret key, e.g `openssl rand -hex 32`
   DATABASE_URL="sqlite:///venue_booking.db"
   MAIL_SERVER="smtp.gmail.com"
   MAIL_PORT=587
   MAIL_USE_TLS=True

   # Get your email password [here](https://myaccount.google.com/apppasswords). Enable 2FA to use this.
   MAIL_USERNAME="youremail@gmail.com"
   MAIL_PASSWORD="your-email-password"

   # Get your Google Client ID and Secret [here](https://console.cloud.google.com/). Create a new project and enable the Google Calendar API.
   GOOGLE_CLIENT_ID="your-google-client-id"
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   ```

5. **Run the application**
   ```bash
   python3 app.py
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


---

<div align="center">
  Made with ❤️ by Bill
</div>
