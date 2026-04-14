import mysql.connector
import json
import random
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



    msg = MIMEText(f"Your OTP is: {otp}")
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


@app.route("/get", methods=["POST"])
def chatbot_response():
    user_message = request.form.get("msg").lower()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ------------------ COURSES (Fees ) ------------------
   
    if "fee" in user_message or "fees" in user_message or "course fee" in user_message:
        cursor.execute("""
            SELECT course_name, fees
            FROM courses
        """)
        results = cursor.fetchall()

        if results:
            response = ""
            for row in results: 
                response += f"{row['course_name']} → Fee: ₹{row['fees']}\n"
                

        else:
            response = "No course data found."

            # SEATS

    elif "seat" in user_message or "total seats" in user_message :
        cursor.execute("""
            SELECT course_name, total_seats
            FROM courses
        """)
        results = cursor.fetchall()

        if results:
            response = ""
            for row in results: 
                response += f"{row['course_name']} →  {row['total_seats']}\n"
                

        else:
            response = "No seats data found."

    # ------------------ HOLIDAYS ------------------
    elif "holiday" in user_message:
        cursor.execute("""
            SELECT holiday_name, holiday_date
            FROM holidays
        """)
        results = cursor.fetchall()

        if results:
            response = "Upcoming Holidays:\n"
            for row in results:
                response += f"{row['holiday_name']} - {row['holiday_date']}\n"
        else:
            response = "No holiday data available."

    # ------------------ CANTEEN ------------------
    elif "canteen" in user_message or "menu" in user_message:
        cursor.execute("""
            SELECT item_name, price
            FROM canteen_menu
        """)
        results = cursor.fetchall()

        if results:
            response = "Canteen Menu:\n"
            for row in results:
                response += f"{row['item_name']} - ₹{row['price']}\n"
        else:
            response = "No canteen data available."

    # ------------------ ROOMS ------------------
    elif "room" in user_message or "principal" in user_message or "exam" in user_message:
        cursor.execute("""
            SELECT room_name, block_name, floor, room_number
            FROM rooms
            JOIN blocks ON rooms.block_id = blocks.id
        """)
        results = cursor.fetchall()

        if results:
            response = ""
            for row in results:
                response += f"{row['room_name']} → {row['block_name']}, {row['floor']}, Room {row['room_number']}\n"
        else:
            response = "No room information found."

    
    else:
        response = "Sorry, I didn’t understand. Please ask about courses, faculty, holidays, rooms, or canteen."

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

        # 🔍 DEBUG
        print("Entered:", password)
        print("DB:", user["password"] if user else "No user")

        # ✅ CORRECT CHECK
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
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db_connection()
        cursor = conn.cursor()
        hashed_password = generate_password_hash(password)
        try:
            cursor.execute(
                "INSERT INTO students (name, email, password, role) VALUES (%s, %s, %s, %s)",
                (name, email, hashed_password, "student")
            )
            conn.commit()
        except:
            return "Email already exists"

        cursor.close()
        conn.close()

        return redirect("/login")

    return render_template("register.html")
@app.route("/verify", methods=["GET", "POST"])
def verify():
    if request.method == "POST":
        user_otp = request.form.get("otp")

        # ⏱ Check expiry (5 minutes)
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
    return render_template("admin_gallery.html", images=images, users=users, notices=notices)

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
    return render_template('admin_gallery.html', images=images, users=users, notices=notices)

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


# 🔷 Delete Image
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

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT id, name, email FROM students WHERE id = %s",
        (session['student_id'],)
    )
    student = cursor.fetchone()

    if not student:
        cursor.close()
        conn.close()
        session.clear()
        return redirect('/login')

    cursor.execute(
        "SELECT course_name, hod_name, fees, total_seats FROM courses"
    )
    courses = cursor.fetchall()

    cursor.close()
    conn.close()
    notices = get_notices(limit=5)

    return render_template(
        'student_dashboard.html',
        student=student,
        courses=courses,
        course_count=len(courses),
        fees_status="Paid",
        notice_count=len(notices),
        notices=notices
    )



if __name__ == "__main__":
    app.run(debug=True)
