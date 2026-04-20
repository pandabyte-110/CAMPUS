import mysql.connector
import json
import random
import difflib
import re
from flask import Flask , url_for, render_template, request, jsonify ,redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
import random
import time
from datetime import datetime
from email.mime.text import MIMEText
from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy import inspect, text
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///campus.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="PasswarD",
        database="campus_db"
    )


def send_otp_email(to_email, otp):
    sender_email = "pandadeepankar96@gmail.com"
    app_password = "fxpq vusf zqcm edtk"



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

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, app_password)
    server.send_message(msg)
    server.quit()

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
with open("intents.json") as file:
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

def detect_intent(user_message):
    text = user_message.lower()

    if any(word in text for word in ["hello", "hi", "hey", "good morning", "good evening"]):
        return "greeting"
    if any(word in text for word in ["fee", "fees", "tuition"]):
        return "get_fee"
    if "hod" in text or "head of department" in text:
        return "get_hod"
    if any(word in text for word in ["available", "availability", "in stock"]):
        return "availability"
    if any(word in text for word in ["category", "in category", "items in", "show", "list", "menu in"]):
        return "category_query"
    if any(word in text for word in ["price", "cost", "rate", "how much"]):
        return "price_query"
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

def _fetch_menu_items(cursor):
    cursor.execute("SELECT id, name, category, price, availability FROM menu_items")
    return cursor.fetchall()

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

def handle_menu_query(user_message, intent, cursor):
    if intent == "category_query":
        category = extract_menu_category(user_message, cursor)
        if not category:
            return "Please specify the category."

        cursor.execute(
            """
            SELECT name FROM menu_items
            WHERE LOWER(category) = LOWER(%s)
            ORDER BY name ASC
            """,
            (category,)
        )
        rows = cursor.fetchall()
        if not rows:
            return f"I couldn't find items in the {category} category."

        item_names = ", ".join(row["name"] for row in rows)
        return f"Items in {category}: {item_names}."

    item_matches = extract_menu_item_matches(user_message, cursor)
    if not item_matches:
        return "Please specify the item name."

    if len(item_matches) > 1:
        options = " or ".join(item["name"] for item in item_matches[:2])
        return f"Did you mean {options}?"

    item_name = item_matches[0]["name"]

    if intent == "price_query":
        cursor.execute(
            "SELECT price FROM menu_items WHERE name LIKE %s LIMIT 1",
            (f"%{item_name}%",)
        )
        row = cursor.fetchone()
        if not row:
            return f"I couldn't find the price for {item_name}."
        return f"The price of {item_name.lower()} is {format_currency(row['price'])}."

    if intent == "availability":
        cursor.execute(
            "SELECT availability FROM menu_items WHERE name LIKE %s LIMIT 1",
            (f"%{item_name}%",)
        )
        row = cursor.fetchone()
        if not row:
            return f"I couldn't find availability details for {item_name}."

        availability = str(row.get("availability", "")).strip().lower()
        if availability in {"yes", "y", "1", "true", "available", "in stock"}:
            return f"Yes, {item_name.lower()} is available."
        return f"No, {item_name.lower()} is currently unavailable."

    return None

def extract_department(user_message, cursor):
    text = user_message.lower()
    cursor.execute("SELECT course_name FROM courses")
    courses = cursor.fetchall()

    for row in courses:
        course_name = (row.get("course_name") or "").strip()
        if not course_name:
            continue

        course_lower = course_name.lower()
        if course_lower in text:
            return course_name

        tokens = [token for token in course_lower.replace("&", " ").replace("-", " ").split() if token]
        if tokens and all(token in text for token in tokens):
            return course_name
    return None

def format_department_name(department):
    return " ".join(word.capitalize() for word in department.split())

def format_inr(value):
    try:
        return f"\u20B9{int(value):,}"
    except (ValueError, TypeError):
        return f"\u20B9{value}"


@app.route("/get", methods=["POST"])
def chatbot_response():
    user_message = request.form.get("msg", "").strip()
    lowered_message = user_message.lower()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_menu_items_table(cursor)
    intent = detect_intent(user_message)
    department = extract_department(user_message, cursor)

    if intent == "greeting":
        response = "Hello! You can ask me about fees or HOD details department-wise."
    elif intent in ["get_fee", "get_hod"] and not department:
        if any(phrase in lowered_message for phrase in ["what is the fee", "fee?", "fees?"]):
            response = "Could you tell me which department?"
        else:
            response = "Please specify the department."
    elif intent == "get_fee":
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
            response = f"The fee for {row['course_name']} is {format_inr(row['fees'])} per year."
        else:
            response = f"I could not find fee details for {format_department_name(department)}."
    elif intent == "get_hod":
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
            response = f"The HOD of {row['course_name']} is {row['hod_name']}."
        elif row:
            response = f"HOD details for {row['course_name']} are not available right now."
        else:
            response = f"I could not find HOD details for {format_department_name(department)}."
    elif intent in ["price_query", "availability", "category_query"]:
        response = handle_menu_query(user_message, intent, cursor)
    else:
        response = "Sorry, I didn't understand. You can ask about fees, HOD, canteen prices, availability, or categories."

    cursor.close()
    conn.close()

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

        # DEBUG
        print("Entered:", password)
        print("DB:", user["password"] if user else "No user")

        # CORRECT CHECK
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


            send_otp_email(email, otp)

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

    send_otp_email(email, otp)

    return "OTP resent successfully!"
@app.route("/chat")
def chat():
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

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
NOTICE_UPLOAD_FOLDER = 'static/notices'
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
    app.run(debug=True)
