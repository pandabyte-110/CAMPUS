import mysql.connector
import json
import random
import difflib
import re
from dotenv import load_dotenv
from dataclasses import dataclass
from flask import Flask , url_for, render_template, request, jsonify ,redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
import socket
import random
import time
from datetime import datetime, date, timedelta
from email.mime.text import MIMEText
from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy import inspect, text
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "campus-dev-secret-key")


app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///campus.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class DatabaseConnectionError(Exception):
    pass

class Gallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(255))
    title = db.Column(db.String(150))
    description = db.Column(db.Text)
    event_date = db.Column(db.Date)

class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default="General")
    pdf_file = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class FAQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

with app.app_context():
    db.create_all()
    inspector = inspect(db.engine)
    notice_columns = {column["name"] for column in inspector.get_columns("notice")} if inspector.has_table("notice") else set()
    if "pdf_file" not in notice_columns:
        db.session.execute(text("ALTER TABLE notice ADD COLUMN pdf_file VARCHAR(255)"))
        db.session.commit()
# Database Connection
def get_db_connection():
    db_host = os.getenv("MYSQL_HOST") or os.getenv("MYSQLHOST", "127.0.0.1")
    db_port = int(os.getenv("MYSQL_PORT") or os.getenv("MYSQLPORT", "3306"))
    db_user = os.getenv("MYSQL_USER") or os.getenv("MYSQLUSER", "root")
    db_password = os.getenv("MYSQL_PASSWORD") or os.getenv("MYSQLPASSWORD", "")
    db_name = os.getenv("MYSQL_DATABASE") or os.getenv("MYSQLDATABASE", "campus")

    try:
        return mysql.connector.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name
        )
    except mysql.connector.Error as exc:
        raise DatabaseConnectionError("Unable to connect to the database. Please try again later.") from exc


@app.errorhandler(DatabaseConnectionError)
def handle_database_connection_error(error):
    if request.path == "/get" or request.path == "/chat":
        return jsonify({"response": str(error)}), 503
    return str(error), 503


def send_otp_email(to_email, otp):
    sender_email = os.getenv("SMTP_EMAIL")
    app_password = os.getenv("SMTP_APP_PASSWORD")
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    if not sender_email or not app_password:
        return False, "Email service is not configured."

    # Common typo guard: smtp.gmail.con -> smtp.gmail.com
    if smtp_host.endswith(".con"):
        smtp_host = f"{smtp_host[:-4]}.com"



    html_body = f"""
    <div style="margin:0;padding:24px;background:#f5f7fb;font-family:Segoe UI,Arial,sans-serif;color:#1f2937;">
        <div style="max-width:620px;margin:0 auto;background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 12px 30px rgba(15,23,42,0.12);">
            <div style="padding:22px 26px;background:linear-gradient(135deg,#12233a,#22456d);color:#fff8ed;">
                <h1 style="margin:0;font-size:24px;letter-spacing:0.03em;">CAMPUS Security Verification</h1>
                <p style="margin:8px 0 0;font-size:14px;color:#d9e7f6;">One-time passcode confirmation</p>
            </div>
            <div style="padding:24px 26px;">
                <p style="margin:0 0 12px;font-size:15px;">Hello,</p>
                <p style="margin:0 0 18px;font-size:15px;line-height:1.6;">
                    We received a request to sign in to your CAMPUS account. Use the verification code below to continue.
                </p>
                <div style="margin:0 0 18px;padding:18px;border-radius:12px;background:#f1f5ff;border:1px solid #dbe7ff;text-align:center;">
                    <span style="font-size:32px;font-weight:700;letter-spacing:0.22em;color:#12233a;">{otp}</span>
                </div>
                <p style="margin:0 0 10px;font-size:14px;line-height:1.6;color:#475569;">
                    This code is valid for <strong>5 minutes</strong>. Please do not share this code with anyone.
                </p>
                <p style="margin:0;font-size:14px;line-height:1.6;color:#475569;">
                    If you did not request this login, you can safely ignore this email.
                </p>
            </div>
            <div style="padding:14px 26px;background:#f8fafc;border-top:1px solid #e2e8f0;color:#64748b;font-size:12px;">
                Sent by CAMPUS Authentication System
            </div>
        </div>
    </div>
    """

    msg = MIMEText(html_body, "html")
    msg["Subject"] = "CAMPUS OTP Verification"
    msg["From"] = sender_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.send_message(msg)
        return True, None
    except (socket.gaierror, TimeoutError, OSError) as exc:
        print(f"OTP email connection error: {exc}")
        return False, "Unable to connect to the email server. Please try again."
    except smtplib.SMTPException as exc:
        print(f"OTP email SMTP error: {exc}")
        return False, "Email authentication/delivery failed. Please try again."

def get_admin_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email, role FROM students ORDER BY id DESC")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return users

def get_notices(limit=None):
    query = Notice.query.order_by(Notice.created_at.desc())
    if limit:
        query = query.limit(limit)
    return query.all()

def get_faqs():
    return FAQ.query.order_by(FAQ.created_at.desc()).all()

def search_faqs(user_query):
    """Search FAQs using similarity matching and return matching answer if found."""
    faqs = FAQ.query.all()
    if not faqs:
        return None
    
    user_query_lower = user_query.lower().strip()
    best_match = None
    best_ratio = 0
    threshold = 0.4  # 40% similarity threshold
    
    for faq in faqs:
        faq_question_lower = faq.question.lower()
        ratio = difflib.SequenceMatcher(None, user_query_lower, faq_question_lower).ratio()
        
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = faq
    
    if best_match and best_ratio >= threshold:
        return best_match.answer
    
    return None

def get_latest_notice():
    """Get the most recent notice posted by admin."""
    notice = Notice.query.order_by(Notice.created_at.desc()).first()
    return notice

def is_notice_query(user_input):
    """Check if user is asking about notices."""
    lowered = user_input.lower()
    notice_keywords = {"notice", "notices", "new notice", "latest notice", "recent notice", "announcement", "announcements"}
    return any(keyword in lowered for keyword in notice_keywords)

def format_notice_response(notice):
    """Format notice for chatbot display."""
    if not notice:
        return "No notices have been posted yet."
    
    response = f"📌 **{notice.title}**\n\n{notice.message}"
    if notice.category:
        response += f"\n\n📂 Category: {notice.category}"
    return response

VALID_COLLEGE_YEARS = ["1st Year", "2nd Year", "3rd Year", "4th Year"]

def ensure_student_profile_columns():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SHOW COLUMNS FROM students")
    existing_columns = {row[0] for row in cursor.fetchall()}

    alter_statements = []
    if "subject" not in existing_columns:
        alter_statements.append("ALTER TABLE students ADD COLUMN subject VARCHAR(150)")
    if "roll_no" not in existing_columns:
        alter_statements.append("ALTER TABLE students ADD COLUMN roll_no VARCHAR(50)")
    if "college_year" not in existing_columns:
        alter_statements.append("ALTER TABLE students ADD COLUMN college_year VARCHAR(20)")

    for statement in alter_statements:
        cursor.execute(statement)

    if alter_statements:
        conn.commit()

    cursor.close()
    conn.close()
# Load intents file
intents_path = os.path.join(BASE_DIR, "intents.json")
with open(intents_path, encoding="utf-8") as file:
    intents = json.load(file)

@app.route("/")
def home():
    return render_template("index.html")

def get_response(user_message):
    user_message = user_message.lower()

    for intent in intents["intents"]:
        for pattern in intent["patterns"]:
            if pattern in user_message:
                return random.choice(intent["responses"])

    return "Sorry, I don't understand."

INTENTS = {
    "price_query": ["price", "cost", "rate", "how much"],
    "availability_query": ["available", "availability", "is there"],
    "menu_query": ["menu", "items", "food"],
}

# Navigation keywords and synonym mapping for campus places.
NAVIGATION_KEYWORDS = [
    "where is",
    "how to go to",
    "how do i reach",
    "how can i reach",
    "how to reach",
    "directions to",
    "route to",
    "i am at",
    "im at",
    "i m at",
]

LOCATION_SYNONYMS = {
    "principal room": "Principal Office",
    "fees office": "Account Section",
    "exam cell": "Exam Section",
    "lab": "Computer Lab",
    "hostel boys": "Boys Hostel",
    "hostel girls": "Girls Hostel",
}

COLLEGE_INFO_MAP = {
    "principal": "principal_name",
    "principal name": "principal_name",
    "established": "established_year",
    "year of establishment": "established_year",
    "history": "college_history",
    "anthem": "college_anthem",
    "motto": "college_motto",
    "vision": "college_vision",
    "mission": "college_mission",
    "address": "college_address",
}

COLLEGE_INFO_TRIGGERS = [
    "principal",
    "established",
    "establishment",
    "history",
    "anthem",
    "motto",
    "vision",
    "mission",
    "address",
    "college info",
    "college information",
]


def _tokenize_words(text):
    return re.findall(r"\b[a-z0-9]+\b", text.lower())


def _contains_keyword(text, tokens, keyword):
    if " " in keyword:
        return keyword in text
    return keyword in tokens


def detect_intent(user_message):
    text = user_message.lower()
    tokens = _tokenize_words(text)

    for intent, keywords in INTENTS.items():
        for word in keywords:
            if _contains_keyword(text, tokens, word):
                return intent

    if any(_contains_keyword(text, tokens, word) for word in ["hello", "hi", "hey", "good morning", "good evening"]):
        return "greeting"
    if any(_contains_keyword(text, tokens, word) for word in ["fee", "fees", "tuition"]):
        return "get_fee"
    if _contains_keyword(text, tokens, "hod") or _contains_keyword(text, tokens, "head of department"):
        return "get_hod"
    if any(_contains_keyword(text, tokens, word) for word in ["category", "in category", "items in", "show", "list", "menu in"]):
        return "category_query"
    return "unknown"

def ensure_menu_items_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS menu_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(150) NOT NULL,
            category VARCHAR(80),
            price DECIMAL(10,2) NOT NULL,
            availability VARCHAR(20) DEFAULT 'available'
        )
        """
    )

def _normalize_text(value):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", value.lower())).strip()

def _normalize_navigation_text(user_text):
    # Normalize user text and apply location synonyms before extracting places.
    normalized = _normalize_text(user_text)
    for alias, canonical in LOCATION_SYNONYMS.items():
        alias_norm = _normalize_text(alias)
        canonical_norm = _normalize_text(canonical)
        normalized = re.sub(rf"\b{re.escape(alias_norm)}\b", canonical_norm, normalized)
    return re.sub(r"\s+", " ", normalized).strip()

def _normalize_college_info_text(user_text):
    return _normalize_text(user_text)

def is_college_info_query(user_text):
    text = _normalize_college_info_text(user_text)
    return any(trigger in text for trigger in COLLEGE_INFO_TRIGGERS)

def detect_college_info_key(user_text):
    # Match longest phrases first so "principal name" wins over "principal".
    text = _normalize_college_info_text(user_text)
    sorted_keys = sorted(COLLEGE_INFO_MAP.keys(), key=len, reverse=True)
    for phrase in sorted_keys:
        if phrase in text:
            return COLLEGE_INFO_MAP[phrase]
    return None

def get_college_info(key_name, cursor):
    # Fetch exactly one college info value for the mapped key.
    try:
        cursor.execute(
            """
            SELECT value
            FROM college_info
            WHERE key_name = %s
            LIMIT 1
            """,
            (key_name,)
        )
        return cursor.fetchone()
    except mysql.connector.Error:
        return None

def handle_college_info_query(user_input, cursor):
    if not is_college_info_query(user_input):
        return None

    key_name = detect_college_info_key(user_input)
    if not key_name:
        return "Sorry, I couldn't find that information. Please try asking differently."

    info_row = get_college_info(key_name, cursor)
    if not info_row or not info_row.get("value"):
        return "Sorry, I couldn't find that information. Please try asking differently."

    return str(info_row["value"]).strip()

def is_navigation_query(user_text):
    text = _normalize_navigation_text(user_text)
    return any(keyword in text for keyword in NAVIGATION_KEYWORDS) or bool(
        re.search(r"\bfrom\s+[a-z0-9\s]+?\s+to\s+[a-z0-9\s]+\b", text)
    )

def _clean_place_candidate(value):
    value = re.sub(r"\b(please|kindly|me|the|a|an)\b", " ", value or "")
    value = re.sub(r"\s+", " ", value).strip(" ,.?")
    return value

def extract_navigation_places(user_text):
    text = _normalize_navigation_text(user_text)
    start_place = None
    destination = None

    # Pattern: "from <start> to <end>"
    from_to_match = re.search(r"\bfrom\s+([a-z0-9\s]+?)\s+to\s+([a-z0-9\s]+)\b", text)
    if from_to_match:
        start_place = _clean_place_candidate(from_to_match.group(1))
        destination = _clean_place_candidate(from_to_match.group(2))
        return start_place, destination

    # Pattern: "i am at <start> ... how to reach/go to <end>"
    start_match = re.search(r"\b(?:i am at|im at|i m at)\s+([a-z0-9\s]+?)(?=\s+(?:how|directions|where|can)\b|$)", text)
    if start_match:
        start_place = _clean_place_candidate(start_match.group(1))

    destination_patterns = [
        r"\bwhere is\s+([a-z0-9\s]+)$",
        r"\bdirections to\s+([a-z0-9\s]+)$",
        r"\bhow to go to\s+([a-z0-9\s]+)$",
        r"\bhow to reach\s+([a-z0-9\s]+)$",
        r"\bhow do i reach\s+([a-z0-9\s]+)$",
        r"\bhow can i reach\s+([a-z0-9\s]+)$",
        r"\bgo to\s+([a-z0-9\s]+)$",
        r"\breach\s+([a-z0-9\s]+)$",
        r"\bto\s+([a-z0-9\s]+)$",
    ]
    for pattern in destination_patterns:
        matched = re.search(pattern, text)
        if matched:
            destination = _clean_place_candidate(matched.group(1))
            break

    return start_place, destination

def get_location(place, cursor):
    # Always fetch one matching location record; never return raw full table output.
    try:
        cursor.execute(
            """
            SELECT name, category, description, landmark, directions, image_url
            FROM locations
            WHERE LOWER(name) LIKE LOWER(%s)
            ORDER BY name ASC
            LIMIT 1
            """,
            (f"%{place}%",)
        )
        return cursor.fetchone()
    except mysql.connector.Error:
        return None

def get_route(start, end, cursor):
    # Fetch route instructions between start and destination.
    try:
        cursor.execute(
            """
            SELECT start_location, end_location, steps
            FROM routes
            WHERE LOWER(start_location) LIKE LOWER(%s)
              AND LOWER(end_location) LIKE LOWER(%s)
            ORDER BY id ASC
            LIMIT 1
            """,
            (f"%{start}%", f"%{end}%")
        )
        return cursor.fetchone()
    except mysql.connector.Error:
        return None

def _guess_location_from_text(user_text, cursor, exclude_name=None):
    # Fallback guess using known location names from DB when direct extraction fails.
    try:
        cursor.execute(
            """
            SELECT name
            FROM locations
            WHERE name IS NOT NULL AND name <> ''
            ORDER BY CHAR_LENGTH(name) DESC
            """
        )
        rows = cursor.fetchall()
    except mysql.connector.Error:
        return None

    normalized_text = _normalize_navigation_text(user_text)
    exclude_norm = _normalize_text(exclude_name or "")

    for row in rows:
        db_name = (row.get("name") or "").strip()
        if not db_name:
            continue
        db_name_norm = _normalize_text(db_name)
        if exclude_norm and db_name_norm == exclude_norm:
            continue
        if db_name_norm and db_name_norm in normalized_text:
            return db_name
    return None

def _append_location_image(response_text, location_row):
    image_url = (location_row or {}).get("image_url")
    if image_url:
        return f"{response_text}\nYou can also view it here: {image_url}"
    return response_text

def format_location_response(location_row):
    name = (location_row.get("name") or "This location").strip()
    description = (location_row.get("description") or "").strip()
    landmark = (location_row.get("landmark") or "").strip()
    directions = (location_row.get("directions") or "").strip()

    if landmark:
        first_line = f"{name} is located near {landmark}."
    elif description:
        first_line = f"{name}: {description}"
    else:
        first_line = f"{name} location details:"

    response_parts = [first_line]
    if description and landmark:
        response_parts.append(description)
    if directions:
        response_parts.append(f"Directions: {directions}")

    return _append_location_image("\n".join(response_parts), location_row)

def handle_navigation_query(user_input, cursor):
    if not is_navigation_query(user_input):
        return None

    start_place, destination = extract_navigation_places(user_input)
    if not destination:
        destination = _guess_location_from_text(user_input, cursor)

    if not destination:
        return "Please tell me the destination place."

    destination_row = get_location(destination, cursor)
    if not destination_row:
        return "Sorry, I couldn't find that location. Please try another place."

    if start_place:
        start_row = get_location(start_place, cursor)
        if not start_row:
            guessed_start = _guess_location_from_text(
                user_input,
                cursor,
                exclude_name=destination_row.get("name")
            )
            if guessed_start:
                start_row = get_location(guessed_start, cursor)

        start_name = start_row["name"] if start_row else start_place.title()
        route_row = (
            get_route(start_name, destination_row["name"], cursor)
            or get_route(start_place, destination_row["name"], cursor)
            or get_route(start_name, destination, cursor)
        )

        if route_row and route_row.get("steps"):
            route_text = (
                f"From {start_name} to {destination_row['name']}:\n"
                f"{route_row['steps']}"
            )
            return _append_location_image(route_text, destination_row)

        fallback = (
            f"Sorry, I couldn't find a route from {start_name} to {destination_row['name']}.\n"
            f"{format_location_response(destination_row)}"
        )
        return fallback

    return format_location_response(destination_row)

def _fetch_menu_items(cursor):
    cursor.execute("SELECT id, name, category, price, availability FROM menu_items")
    return cursor.fetchall()

def extract_item_name(user_input):
    cleaned = _normalize_text(user_input)
    for phrase in [
        "price of", "cost of", "rate of", "how much is", "how much",
        "is there", "is", "available", "availability", "menu", "items", "food"
    ]:
        cleaned = cleaned.replace(phrase, " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned

def is_single_word(user_input):
    return len(user_input.strip().split()) == 1


def _is_item_available(value):
    return str(value or "").strip().lower() in {"yes", "y", "1", "true", "available", "in stock"}


def get_full_menu(cursor):
    cursor.execute(
        """
        SELECT name, category, price, availability
        FROM menu_items
        ORDER BY category ASC, name ASC
        """
    )
    items = cursor.fetchall()

    if not items:
        return "Menu is not available right now."

    response_lines = ["Canteen Menu:"]
    current_category = None

    for item in items:
        category = item.get("category") or "Uncategorized"
        if category != current_category:
            current_category = category
            response_lines.append(f"\n{current_category}:")

        availability = "Yes" if _is_item_available(item.get("availability")) else "No"
        response_lines.append(
            f"- {item.get('name')} - {format_currency(item.get('price'))} | Available: {availability}"
        )

    return "\n".join(response_lines)


def search_menu_items(keyword, cursor):
    cursor.execute(
        """
        SELECT name, category, price, availability
        FROM menu_items
        WHERE LOWER(name) LIKE LOWER(%s)
        ORDER BY category ASC, name ASC
        """,
        (f"%{keyword}%",)
    )
    items = cursor.fetchall()

    if not items:
        return None

    response_lines = [f"Items related to '{keyword}':"]
    for item in items:
        availability = "Yes" if _is_item_available(item.get("availability")) else "No"
        response_lines.append(
            f"- {item.get('name')} - {format_currency(item.get('price'))} | Available: {availability}"
        )
    return "\n".join(response_lines)


def get_all_fees(cursor):
    cursor.execute(
        """
        SELECT course_name, fees
        FROM courses
        ORDER BY course_name ASC
        """
    )
    courses = cursor.fetchall()
    if not courses:
        return "No fee records found."

    response_lines = ["Fee Structure:"]
    for course in courses:
        response_lines.append(
            f"- {course.get('course_name')} - {format_inr(course.get('fees'))} per year"
        )
    return "\n".join(response_lines)


def handle_fees_query(user_input, cursor):
    department = extract_department(user_input, cursor)
    if not department:
        return get_all_fees(cursor)

    cursor.execute(
        """
        SELECT course_name, fees
        FROM courses
        WHERE LOWER(course_name) = %s
        LIMIT 1
        """,
        (department.lower(),)
    )
    row = cursor.fetchone()
    if row:
        return f"The fee for {row['course_name']} is {format_inr(row['fees'])} per year."
    return f"I could not find fee details for {format_department_name(department)}."

def get_course_seats(course_name, cursor):
    """Get available seats for a specific course."""
    cursor.execute(
        """
        SELECT course_name, total_seats
        FROM courses
        WHERE LOWER(course_name) = %s
        LIMIT 1
        """,
        (course_name.lower(),)
    )
    row = cursor.fetchone()
    if row:
        # Get enrolled students count
        cursor.execute(
            "SELECT COUNT(*) as enrolled FROM students WHERE LOWER(subject) = %s",
            (course_name.lower(),)
        )
        enrolled_result = cursor.fetchone()
        enrolled = enrolled_result.get("enrolled", 0) if enrolled_result else 0
        total_seats = row.get("total_seats", 0)
        available_seats = max(0, total_seats - enrolled)
        
        return {
            "course_name": row["course_name"],
            "total_seats": total_seats,
            "enrolled": enrolled,
            "available_seats": available_seats
        }
    return None

def get_all_course_strength(cursor):
    """Get all courses with their enrollment strength."""
    cursor.execute("SELECT id, course_name, total_seats FROM courses ORDER BY course_name ASC")
    courses = cursor.fetchall()
    
    if not courses:
        return "No course records found."
    
    response_lines = ["📚 **Course Strength & Availability:**\n"]
    for course in courses:
        course_name = course.get("course_name")
        total_seats = course.get("total_seats", 0)
        
        # Get enrolled students count
        cursor.execute(
            "SELECT COUNT(*) as enrolled FROM students WHERE LOWER(subject) = %s",
            (course_name.lower(),)
        )
        enrolled_result = cursor.fetchone()
        enrolled = enrolled_result.get("enrolled", 0) if enrolled_result else 0
        available_seats = max(0, total_seats - enrolled)
        
        response_lines.append(
            f"• **{course_name}**: {enrolled}/{total_seats} enrolled | "
            f"🔵 {available_seats} seats available"
        )
    
    return "\n".join(response_lines)

def handle_seats_query(user_input, cursor):
    """Handle queries about course seats and strength."""
    lowered_input = user_input.lower()
    
    # Check if user is asking for a specific course
    department = extract_department(user_input, cursor)
    if department:
        course_info = get_course_seats(department, cursor)
        if course_info:
            return (
                f"📌 **{course_info['course_name']}**\n"
                f"• Total Seats: {course_info['total_seats']}\n"
                f"• Enrolled Students: {course_info['enrolled']}\n"
                f"• 🟢 Available Seats: {course_info['available_seats']}"
            )
        return f"I could not find course details for {format_department_name(department)}."
    
    # If no specific course, return all courses' strength
    return get_all_course_strength(cursor)

def extract_menu_item_matches(user_message, cursor):
    text = _normalize_text(user_message)
    menu_items = _fetch_menu_items(cursor)

    if not menu_items:
        return []

    direct_matches = []
    for item in menu_items:
        item_name = (item.get("name") or "").strip()
        item_norm = _normalize_text(item_name)
        if item_norm and item_norm in text:
            direct_matches.append(item)

    if direct_matches:
        return direct_matches

    stop_words = {
        "what", "is", "the", "price", "cost", "rate", "of", "for", "item",
        "available", "availability", "show", "list", "menu", "in", "category",
        "do", "you", "have", "tell", "me", "please"
    }
    filtered_tokens = [token for token in text.split() if token not in stop_words]
    candidate_text = " ".join(filtered_tokens).strip() or text

    names_map = {_normalize_text(item["name"]): item for item in menu_items if item.get("name")}
    close_names = difflib.get_close_matches(candidate_text, list(names_map.keys()), n=3, cutoff=0.5)
    fuzzy_matches = [names_map[name] for name in close_names]

    if fuzzy_matches:
        return fuzzy_matches

    token_fuzzy_matches = []
    for token in filtered_tokens:
        close_token_names = difflib.get_close_matches(token, list(names_map.keys()), n=2, cutoff=0.8)
        for matched in close_token_names:
            token_fuzzy_matches.append(names_map[matched])

    unique_by_id = {}
    for item in token_fuzzy_matches:
        unique_by_id[item["id"]] = item
    return list(unique_by_id.values())

def extract_menu_category(user_message, cursor):
    text = _normalize_text(user_message)
    cursor.execute("SELECT DISTINCT category FROM menu_items WHERE category IS NOT NULL AND category <> ''")
    categories = [row["category"] for row in cursor.fetchall() if row.get("category")]

    if not categories:
        return None

    for category in categories:
        if _normalize_text(category) in text:
            return category

    normalized_map = {_normalize_text(category): category for category in categories}
    fuzzy = difflib.get_close_matches(text, list(normalized_map.keys()), n=1, cutoff=0.55)
    if fuzzy:
        return normalized_map[fuzzy[0]]
    return None

def format_currency(value):
    try:
        return f"\u20B9{float(value):,.0f}"
    except (ValueError, TypeError):
        return f"\u20B9{value}"

def handle_menu_query(user_message, cursor):
    lowered = user_message.lower()

    extracted_name = extract_item_name(user_message)
    item_matches = []

    if extracted_name:
        cursor.execute(
            """
            SELECT id, name, category, price, availability
            FROM menu_items
            WHERE LOWER(name) LIKE LOWER(%s)
            ORDER BY name ASC
            """,
            (f"%{extracted_name}%",)
        )
        item_matches = cursor.fetchall()

    if not item_matches:
        item_matches = extract_menu_item_matches(user_message, cursor)

    if not item_matches:
        return "Please specify the item name."

    if len(item_matches) > 1:
        options = " or ".join(item["name"] for item in item_matches[:2])
        return f"Did you mean {options}?"

    item = item_matches[0]
    item_name = item["name"]

    if any(word in lowered for word in ["price", "cost", "rate"]) or "how much" in lowered:
        return f"The price of {item_name} is {format_currency(item['price'])}."

    if any(word in lowered for word in ["available", "availability"]) or "is there" in lowered:
        if _is_item_available(item.get("availability")):
            return f"Yes, {item_name} is available."
        return f"Sorry, {item_name} is not available."

    return f"{item_name} costs {format_currency(item['price'])} and availability is {'Yes' if _is_item_available(item.get('availability')) else 'No'}."

def extract_department(user_message, cursor):
    text = _normalize_text(user_message)
    cursor.execute("SELECT course_name FROM courses")
    courses = cursor.fetchall()

    normalized_courses = []
    for row in courses:
        course_name = (row.get("course_name") or "").strip()
        if not course_name:
            continue
        normalized_courses.append((course_name, _normalize_text(course_name)))

    # Prefer more specific department names first:
    # "teacher education" should be checked before "education".
    normalized_courses.sort(key=lambda item: len(item[1]), reverse=True)

    for course_name, course_norm in normalized_courses:
        if not course_norm:
            continue

        if re.search(rf"\b{re.escape(course_norm)}\b", text):
            return course_name

        tokens = [token for token in course_norm.split() if token]
        if tokens and all(re.search(rf"\b{re.escape(token)}\b", text) for token in tokens):
            return course_name
    return None

def format_department_name(department):
    return " ".join(word.capitalize() for word in department.split())

def format_inr(value):
    try:
        return f"\u20B9{int(value):,}"
    except (ValueError, TypeError):
        return f"\u20B9{value}"


@dataclass
class Holiday:
    id: int
    name: str
    date: date
    day: str
    type: str
    year: int


def _row_to_holiday(row):
    if not row:
        return None
    return Holiday(
        id=row.get("id"),
        name=row.get("name"),
        date=row.get("date"),
        day=row.get("day"),
        type=row.get("type"),
        year=row.get("year"),
    )


def _fetch_one_holiday(query, params):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params)
        row = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    return _row_to_holiday(row)


def get_today_holiday():
    today = date.today()
    return _fetch_one_holiday(
        """
        SELECT id, name, date, day, type, year
        FROM holidays
        WHERE date = %s
        LIMIT 1
        """,
        (today,),
    )


def get_tomorrow_holiday():
    tomorrow = date.today() + timedelta(days=1)
    return _fetch_one_holiday(
        """
        SELECT id, name, date, day, type, year
        FROM holidays
        WHERE date = %s
        LIMIT 1
        """,
        (tomorrow,),
    )


def get_next_holiday():
    today = date.today()
    return _fetch_one_holiday(
        """
        SELECT id, name, date, day, type, year
        FROM holidays
        WHERE date > %s
        ORDER BY date ASC
        LIMIT 1
        """,
        (today,),
    )


def get_holiday_by_name(name):
    if not name:
        return None
    return _fetch_one_holiday(
        """
        SELECT id, name, date, day, type, year
        FROM holidays
        WHERE LOWER(name) LIKE LOWER(%s)
        ORDER BY date ASC
        LIMIT 1
        """,
        (f"%{name}%",),
    )


def fetch_all_holidays():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT id, name, date, day, type, year
            FROM holidays
            ORDER BY date ASC
            """
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return [_row_to_holiday(row) for row in rows]


def _format_holiday_date(holiday_date):
    if isinstance(holiday_date, date):
        return holiday_date.strftime("%Y-%m-%d")
    return str(holiday_date)


def format_holiday_response(holiday, day_type):
    if holiday:
        return (
            f"Yes, {day_type} ({_format_holiday_date(holiday.date)}) is "
            f"{holiday.name}, a {holiday.type} holiday."
        )
    return f"No, {day_type} is not a holiday."


def get_all_holidays():
    holidays = fetch_all_holidays()
    if not holidays:
        return "No holidays found."

    response_lines = ["Holiday List:"]
    for holiday in holidays:
        response_lines.append(
            f"- {holiday.name} ({_format_holiday_date(holiday.date)}) - {holiday.day}"
        )
    return "\n".join(response_lines)


def search_holiday(keyword):
    holiday = get_holiday_by_name(keyword)
    if not holiday:
        return None
    return f"{holiday.name} is on {_format_holiday_date(holiday.date)} ({holiday.day})."


def handle_query(user_input):
    user_input = user_input.strip()
    if not user_input:
        return "Please type your question."

    lowered_input = user_input.lower()
    tokens = set(_tokenize_words(lowered_input))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_menu_items_table(cursor)

    try:
        navigation_response = handle_navigation_query(lowered_input, cursor)
        if navigation_response:
            return navigation_response

        college_info_response = handle_college_info_query(lowered_input, cursor)
        if college_info_response:
            return college_info_response

        if is_single_word(lowered_input):
            if lowered_input == "menu":
                return get_full_menu(cursor)
            if lowered_input == "holidays":
                return get_all_holidays()
            if lowered_input == "fees":
                return get_all_fees(cursor)
            if lowered_input == "seats" or lowered_input == "strength":
                return get_all_course_strength(cursor)

            menu_result = search_menu_items(lowered_input, cursor)
            if menu_result:
                return menu_result

            holiday_result = search_holiday(lowered_input)
            if holiday_result:
                return holiday_result

        if (
            any(word in tokens for word in {"price", "cost", "rate", "available", "availability"})
            or "how much" in lowered_input
            or "is there" in lowered_input
        ):
            menu_response = handle_menu_query(lowered_input, cursor)
            if menu_response:
                return menu_response

        if "today" in tokens and "holiday" in tokens:
            holiday = get_today_holiday()
            return format_holiday_response(holiday, "today")

        if "tomorrow" in tokens and "holiday" in tokens:
            holiday = get_tomorrow_holiday()
            return format_holiday_response(holiday, "tomorrow")

        if "next holiday" in lowered_input:
            holiday = get_next_holiday()
            if holiday:
                return (
                    f"The next holiday is {holiday.name} on "
                    f"{_format_holiday_date(holiday.date)} ({holiday.day})."
                )
            return "No upcoming holidays found."

        if "when is" in lowered_input:
            keyword = lowered_input.split("when is", 1)[1].strip(" ?.!")
            if not keyword:
                return "Please tell me the holiday name."
            holiday_result = search_holiday(keyword)
            if holiday_result:
                return holiday_result
            return f"No holiday found for {keyword}."

        if "holiday" in tokens or "holidays" in tokens:
            return get_all_holidays()

        if "fee" in tokens or "fees" in tokens or "tuition" in tokens:
            return handle_fees_query(lowered_input, cursor)

        if "seat" in tokens or "seats" in tokens or "strength" in tokens or "enrollment" in tokens:
            return handle_seats_query(lowered_input, cursor)

        if is_notice_query(user_input):
            notice = get_latest_notice()
            return format_notice_response(notice)

        if "hod" in tokens or "head of department" in lowered_input:
            department = extract_department(lowered_input, cursor)
            if not department:
                return "Please specify the department."

            cursor.execute(
                """
                SELECT course_name, hod_name
                FROM courses
                WHERE LOWER(course_name) = %s
                LIMIT 1
                """,
                (department.lower(),)
            )
            row = cursor.fetchone()
            if row and row.get("hod_name"):
                return f"The HOD of {row['course_name']} is {row['hod_name']}."
            if row:
                return f"HOD details for {row['course_name']} are not available right now."
            return f"I could not find HOD details for {format_department_name(department)}."

        if any(word in tokens for word in {"hello", "hi", "hey"}):
            return "Hello! Ask me about menu, holidays, or fees."

        faq_answer = search_faqs(user_input)
        if faq_answer:
            return faq_answer

        return "Sorry, I didn't understand your request."
    finally:
        cursor.close()
        conn.close()


@app.route("/get", methods=["POST"])
def chatbot_response():
    user_message = request.form.get("msg", "").strip()
    if not user_message and request.is_json:
        user_message = (request.get_json(silent=True) or {}).get("msg", "").strip()
    try:
        response = handle_query(user_message)
    except DatabaseConnectionError:
        response = "Sorry, the database service is temporarily unavailable. Please try again shortly."
    return jsonify({"response": response})

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM students WHERE email=%s", (email,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["student_id"] = user["id"]

            import random
            otp = str(random.randint(100000, 999999))

            session["otp"] = otp
            session["otp_time"] = time.time()
            session["email"] = email
            session["role"] = user["role"]
            session["user"] = user["name"]
            session["student_id"] = user["id"]


            sent, error_message = send_otp_email(email, otp)
            if not sent:
                session.pop("otp", None)
                session.pop("otp_time", None)
                return f"OTP could not be sent. {error_message}"

            return redirect("/verify")


        else:
            return "Invalid email or password"

    return render_template("login.html")
@app.route("/register", methods=["GET", "POST"])
def register():
    ensure_student_profile_columns()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT course_name FROM courses ORDER BY course_name ASC")
    subjects = cursor.fetchall()
    cursor.close()
    conn.close()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        subject = request.form.get("subject", "").strip()
        roll_no = request.form.get("roll_no", "").strip()
        college_year = request.form.get("college_year", "").strip()

        if not name or not email or not password or not subject or not roll_no or not college_year:
            return "Please fill all registration fields."

        if college_year not in VALID_COLLEGE_YEARS:
            return "Please select a valid college year."

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        hashed_password = generate_password_hash(password)

        cursor.execute(
            "SELECT course_name FROM courses WHERE course_name = %s LIMIT 1",
            (subject,)
        )
        selected_subject = cursor.fetchone()
        if not selected_subject:
            cursor.close()
            conn.close()
            return "Please select a valid subject from the list."

        try:
            cursor.execute(
                """
                INSERT INTO students (name, email, password, role, subject, roll_no, college_year)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (name, email, hashed_password, "student", subject, roll_no, college_year)
            )
            conn.commit()
        except:
            cursor.close()
            conn.close()
            return "Email already exists"

        cursor.close()
        conn.close()

        return redirect("/login")

    return render_template("register.html", subjects=subjects, valid_years=VALID_COLLEGE_YEARS)
@app.route("/verify", methods=["GET", "POST"])
def verify():
    if request.method == "POST":
        user_otp = request.form.get("otp")

        # Check expiry (5 minutes)
        if time.time() - session.get("otp_time", 0) > 300:
            return "OTP expired. Please request again."

        if user_otp == session.get("otp"):
            if session.get("role") == "admin":
                return redirect("/admin")
            else:
                return redirect("/chat")
        else:
            return "Invalid OTP"

    return render_template("verify.html")
@app.route("/resend_otp")
def resend_otp():
    email = session.get("email")

    if not email:
        return redirect("/login")

    otp = str(random.randint(100000, 999999))

    session["otp"] = otp
    session["otp_time"] = time.time()

    sent, error_message = send_otp_email(email, otp)
    if not sent:
        session.pop("otp", None)
        session.pop("otp_time", None)
        return f"OTP could not be resent. {error_message}"

    return "OTP resent successfully!"
@app.route("/chat", methods=["GET", "POST"])
def chat():
    if request.method == "POST":
        user_message = request.form.get("msg", "").strip()
        if not user_message and request.is_json:
            user_message = (request.get_json(silent=True) or {}).get("msg", "").strip()
        try:
            response = handle_query(user_message)
        except DatabaseConnectionError:
            response = "Sorry, the database service is temporarily unavailable. Please try again shortly."
        return jsonify({"response": response})

    if "user" not in session:
        return redirect("/login")
    return render_template("index.html")
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/admin")
def admin():
    if "user" not in session or session["role"] != "admin":
        return redirect("/login")
    users = get_admin_users()
    images = Gallery.query.all()
    notices = get_notices()
    faqs = get_faqs()
    return render_template("admin_gallery.html", images=images, users=users, notices=notices, faqs=faqs)

@app.route("/add_course", methods=["POST"])
def add_course():
    if "role" not in session or session["role"] != "admin":
        return redirect("/login")

    name = request.form.get("course_name")
    fees = request.form.get("fees")
    seats = request.form.get("seats")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO courses (course_name, fees, total_seats) VALUES (%s, %s, %s)",
        (name, fees, seats)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/admin")

@app.route('/gallery')
def gallery_page():
    images = Gallery.query.order_by(Gallery.event_date.desc()).all()
    return render_template('gallery.html', images=images)

UPLOAD_FOLDER = os.path.join(app.static_folder, "uploads")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
NOTICE_UPLOAD_FOLDER = os.path.join(app.static_folder, "notices")
app.config['NOTICE_UPLOAD_FOLDER'] = NOTICE_UPLOAD_FOLDER


@app.route('/admin/gallery', methods=['GET', 'POST'])
def admin_gallery():
    if "user" not in session or session.get("role") != "admin":
        return redirect("/login")

    if request.method == 'POST':
        file = request.files.get('image')
        title = request.form.get('title')
        description = request.form.get('description')
        event_date_raw = request.form.get('event_date')

        if not file or not file.filename:
            return "Please choose an image to upload."

        if not event_date_raw:
            return "Please select an event date."

        event_date = datetime.strptime(event_date_raw, "%Y-%m-%d").date()

        filename = secure_filename(file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_img = Gallery(
            image=filename,
            title=title,
            description=description,
            event_date=event_date
        )

        db.session.add(new_img)
        db.session.commit()

        return redirect('/admin/gallery')
       


    users = get_admin_users()
    images = Gallery.query.all()
    notices = get_notices()
    faqs = get_faqs()
    return render_template('admin_gallery.html', images=images, users=users, notices=notices, faqs=faqs)

@app.route('/admin/notice', methods=['POST'])
def add_notice():
    if "user" not in session or session.get("role") != "admin":
        return redirect("/login")

    title = request.form.get('title', '').strip()
    message = request.form.get('message', '').strip()
    category = request.form.get('category', 'General').strip() or "General"
    pdf_file = request.files.get('notice_pdf')

    if not title or not message:
        return "Notice title and message are required."

    pdf_filename = None
    if pdf_file and pdf_file.filename:
        pdf_filename = secure_filename(pdf_file.filename)
        if not pdf_filename.lower().endswith(".pdf"):
            return "Only PDF files are allowed for notice attachments."

        os.makedirs(app.config['NOTICE_UPLOAD_FOLDER'], exist_ok=True)
        pdf_file.save(os.path.join(app.config['NOTICE_UPLOAD_FOLDER'], pdf_filename))

    notice = Notice(title=title, message=message, category=category, pdf_file=pdf_filename)
    db.session.add(notice)
    db.session.commit()
    return redirect('/admin/gallery')

@app.route('/admin/faq', methods=['POST'])
def add_faq():
    if "user" not in session or session.get("role") != "admin":
        return redirect("/login")

    question = request.form.get("question", "").strip()
    answer = request.form.get("answer", "").strip()

    if not question or not answer:
        return "FAQ question and answer are required."

    faq = FAQ(question=question, answer=answer)
    db.session.add(faq)
    db.session.commit()
    return redirect('/admin/gallery')

@app.route('/admin/delete_faq/<int:faq_id>')
def delete_faq(faq_id):
    if "user" not in session or session.get("role") != "admin":
        return redirect("/login")

    faq = FAQ.query.get(faq_id)
    if faq:
        db.session.delete(faq)
        db.session.commit()

    return redirect('/admin/gallery')


# Delete Image
@app.route('/admin/delete/<int:id>')
  
def delete_image(id):
    if "user" not in session or session.get("role") != "admin":
      return redirect("/login")

    img = Gallery.query.get(id)

    if img:
        # delete file from folder
        path = os.path.join(app.config['UPLOAD_FOLDER'], img.image)
        if os.path.exists(path):
            os.remove(path)

        db.session.delete(img)
        db.session.commit()

    return redirect('/admin/gallery')

@app.route('/admin/delete_user/<int:user_id>')
def delete_user(user_id):
    if "user" not in session or session.get("role") != "admin":
        return redirect("/login")

    if session.get("student_id") == user_id:
        return "You cannot delete your own admin account."

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect('/admin/gallery')

@app.route('/admin/delete_notice/<int:notice_id>')
def delete_notice(notice_id):
    if "user" not in session or session.get("role") != "admin":
        return redirect("/login")

    notice = Notice.query.get(notice_id)
    if notice:
        if notice.pdf_file:
            pdf_path = os.path.join(app.config['NOTICE_UPLOAD_FOLDER'], notice.pdf_file)
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
        db.session.delete(notice)
        db.session.commit()

    return redirect('/admin/gallery')

@app.route('/student_dashboard')
def student_dashboard():
    if 'student_id' not in session:
        return redirect('/login')

    ensure_student_profile_columns()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT id, name, email, subject, roll_no, college_year FROM students WHERE id = %s",
        (session['student_id'],)
    )
    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()
        session.clear()
        return redirect('/login')

    selected_course = None
    if student.get("subject"):
        cursor.execute(
            """
            SELECT course_name, hod_name, fees, total_seats
            FROM courses
            WHERE course_name = %s
            LIMIT 1
            """,
            (student["subject"],)
        )
        selected_course = cursor.fetchone()

    cursor.close()
    conn.close()
    notices = get_notices(limit=5)

    return render_template(
        'student_dashboard.html',
        student=student,
        selected_course=selected_course,
        course_count=1 if student.get("subject") else 0,
        fees_status=selected_course["fees"] if selected_course else "N/A",
        notice_count=len(notices),
        notices=notices
    )



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
