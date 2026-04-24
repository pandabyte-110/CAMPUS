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
- Gunicorn
- MySQL (`mysql-connector-python`)
- Flask-SQLAlchemy / SQLAlchemy

## Project Structure
```text
PROJECT CAMPUS/
|- app.py
|- intents.json
|- requirements.txt
|- Procfile
|- runtime.txt
|- templates/
|- static/
```

## Environment Variables
Set these variables locally (in `.env`) and on Render (Environment tab):

```env
FLASK_SECRET_KEY=replace_with_a_long_random_secret

MYSQLHOST=replace_with_mysql_host
MYSQLPORT=3306
MYSQLUSER=replace_with_mysql_user
MYSQLPASSWORD=replace_with_mysql_password
MYSQLDATABASE=replace_with_mysql_database

SMTP_EMAIL=replace_with_gmail_address
SMTP_APP_PASSWORD=replace_with_gmail_app_password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

SQLALCHEMY_DATABASE_URI=sqlite:///campus.db
```

Notes:
- For Railway MySQL, use the exact variable names above (`MYSQLHOST`, `MYSQLPORT`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLDATABASE`).
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

## Deployment on Render
1. Push project to GitHub.
2. Create a new **Web Service** in Render from your repo.
3. Ensure these files exist:
- `Procfile` -> `web: gunicorn app:app`
- `requirements.txt`
- `runtime.txt` -> `python-3.10.0`
4. In Render -> **Environment**, add all variables from the Environment Variables section above.
5. Deploy.

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

## Production Notes
- Do not hardcode credentials in code.
- Keep `.env` out of Git.
- Use Render environment variables for production secrets.

## Troubleshooting
- `Can't connect to MySQL server`:
  - Verify Railway MySQL service is running
  - Re-check Render env variable names and values
  - Confirm DB/network access from Render
- OTP mail not sending:
  - Verify `SMTP_EMAIL` and `SMTP_APP_PASSWORD`
  - Confirm Gmail App Password is active

## License
Add your preferred license here (MIT, Apache-2.0, etc.).
