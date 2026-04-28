# CAMPUS - Flask Chatbot for College Information

CAMPUS is a Flask-based chatbot web application for college/campus support.
It provides student/admin flows and answers queries like notices, FAQs, holidays, fees, seats, HOD details, and campus navigation.

## Features
- Chatbot endpoint for campus-related questions
- Student registration/login with OTP email verification
- Admin dashboard for:
  - Gallery management
  - Notice management (with optional PDF upload)
  - FAQ management
  - User management
- Student dashboard with profile + notices
- MySQL-backed dynamic data (students, courses, holidays, locations, etc.)
- Flask-SQLAlchemy models used for gallery/notice/faq tables

## Tech Stack
- Python 3.10
- Flask
- MySQL (`mysql-connector-python`)
- Flask-SQLAlchemy / SQLAlchemy

## Project Structure
```text
PROJECT CAMPUS/
|- app.py
|- intents.json
|- requirements.txt
|- templates/
|- static/
```

## Environment Variables
Set these variables locally (in `.env`):

```env
FLASK_SECRET_KEY=replace_with_a_long_random_secret

MYSQLHOST=127.0.0.1
MYSQLPORT=3306
MYSQLUSER=root
MYSQLPASSWORD=
MYSQLDATABASE=campus

SMTP_EMAIL=replace_with_gmail_address
SMTP_APP_PASSWORD=replace_with_gmail_app_password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

SQLALCHEMY_DATABASE_URI=sqlite:///campus.db
```

Notes:
- `SMTP_APP_PASSWORD` must be a Gmail App Password, not your regular Gmail password.

## Local Setup
1. Clone the repo
```bash
git clone <your-repo-url>
cd "PROJECT CAMPUS"
```

2. Create virtual environment and install dependencies
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure environment variables
- Create/update `.env` with the keys listed above.
- Export/set env vars before running if not using a loader.

4. Run app
```bash
python app.py
```

Default local URL: `http://127.0.0.1:5000`

## API Endpoint
- `POST /get`
  - form/json key: `msg`
  - returns chatbot response JSON

Example (JSON):
```json
{
  "msg": "What is the latest notice?"
}
```

## Notes
- Do not hardcode credentials in code.
- Keep `.env` out of Git.

## Troubleshooting
- `Can't connect to MySQL server`:
  - Verify your MySQL service is running
  - Re-check local env variable names and values
  - Confirm DB host/user/password/database are correct
- OTP mail not sending:
  - Verify `SMTP_EMAIL` and `SMTP_APP_PASSWORD`
  - Confirm Gmail App Password is active

## License
Add your preferred license here (MIT, Apache-2.0, etc.).
