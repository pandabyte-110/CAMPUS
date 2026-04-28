# CAMPUS - Flask Chatbot for College Information System

CAMPUS is a comprehensive Flask-based web application that combines a **campus information chatbot** with **admin and student management systems**. Students can interact with a chatbot to get answers about campus operations, fees, courses, holidays, locations, and more. Admins can manage galleries, notices, FAQs, users, and course information.

---

## ✨ Features

### Chatbot Engine
- **Natural Language Processing**: Conversational interface for campus-related queries
- **Query Types Supported**:
  - Course information (fees, available seats, strength, HOD details)
  - Holiday and calendar information
  - Campus navigation and directions
  - Notice and announcement retrieval
  - FAQ search with similarity matching
  - Canteen menu queries with pricing and availability
  - College information (principal, mission, vision, address, etc.)
  - General student inquiries
- **Intelligent Matching**: Uses pattern matching, similarity scoring, and fuzzy matching for accurate responses

### Authentication & Authorization
- **Student Registration & Login**: Email-based account creation with password hashing
- **OTP Verification**: Two-factor authentication via Gmail SMTP
- **Admin Dashboard**: Secure admin panel with role-based access control
- **Session Management**: Flask sessions with timeout handling

### Admin Capabilities
- **Gallery Management**: Upload, view, and delete campus event images with metadata
- **Notice Management**: Post announcements with optional PDF attachments
- **FAQ Management**: Create, read, and delete frequently asked questions
- **Course Management**: Add courses with fees and seat information
- **User Management**: View and delete student accounts (with self-protection)

### Student Features
- **Personal Dashboard**: View profile (name, email, subject, roll number, year)
- **Course Information**: View enrolled course details, HOD name, and fees
- **Notice Viewing**: See latest campus notices with categories
- **Chatbot Access**: Full access to campus query chatbot
- **Profile Management**: Auto-populated from registration data

### Database Features
- **SQLAlchemy ORM Models**: Gallery, Notice, FAQ tables with automatic schema creation
- **MySQL Integration**: Full MySQL support for scalable data persistence
- **Schema Management**: Automatic column creation and database initialization
- **Flexible Queries**: Support for both MySQL and SQLite databases

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend Framework** | Flask 3.0.3 |
| **Database** | MySQL / SQLite |
| **ORM** | SQLAlchemy 2.0.36, Flask-SQLAlchemy 3.1.1 |
| **Password Security** | Werkzeug (password hashing) |
| **Environment Config** | python-dotenv |
| **Language** | Python 3.10 |
| **Email Service** | SMTP (Gmail) |
| **Frontend** | HTML/CSS/JavaScript |

---

## 📁 Project Structure

```
PROJECT CAMPUS/
├── app.py                           # Main Flask application with all routes
├── chatbot.py                       # Legacy chatbot engine (similarity-based)
├── intents.json                     # Intent patterns and responses
├── requirements.txt                 # Python dependencies
├── .env                             # Environment configuration (not in git)
├── README.md                        # This file
├── instance/                        # Flask instance folder (SQLite DB location)
│   └── campus.db                    # SQLite database (if used)
├── templates/                       # HTML templates
│   ├── index.html                   # Main chatbot interface
│   ├── login.html                   # Student/admin login page
│   ├── register.html                # Student registration page
│   ├── verify.html                  # OTP verification page
│   ├── admin_gallery.html           # Admin dashboard (gallery, notices, FAQs, users)
│   ├── gallery.html                 # Public gallery view
│   ├── student_dashboard.html       # Student profile + notices
│   └── upload.html                  # File upload interface
└── static/                          # Static assets
    ├── style.css                    # Main stylesheet
    ├── admin.css                    # Admin dashboard styles
    ├── script.js                    # Main JavaScript logic
    ├── admin.js                     # Admin dashboard scripts
    ├── student_dashboard.css        # Student dashboard styles
    ├── student_dashboard.js         # Student dashboard scripts
    ├── student_dashboard.css        # Gallery page styles
    ├── gallery.css                  # Gallery page styles
    ├── notices/                     # Uploaded notice PDFs
    └── uploads/                     # Uploaded gallery images
```

---

## 🗄️ Database Models

### SQLAlchemy Models
```python
Gallery
├── id (Integer, Primary Key)
├── image (String) - Filename
├── title (String) - Event title
├── description (Text)
└── event_date (Date)

Notice
├── id (Integer, Primary Key)
├── title (String) - Notice title
├── message (Text) - Notice content
├── category (String) - Category type
├── pdf_file (String) - Optional PDF attachment
└── created_at (DateTime) - Auto timestamp

FAQ
├── id (Integer, Primary Key)
├── question (String)
├── answer (Text)
└── created_at (DateTime) - Auto timestamp
```

### MySQL Tables (Referenced in Code)
- **students**: User accounts (id, name, email, password, role, subject, roll_no, college_year)
- **courses**: Course info (course_name, fees, total_seats, hod_name)
- **holidays**: Academic calendar (date, name, day, type, year)
- **locations**: Campus places (name, category, description, landmark, directions, image_url)
- **routes**: Navigation paths (start_location, end_location, steps)
- **menu_items**: Canteen menu (name, category, price, availability)
- **college_info**: College metadata (key_name, value)

---

## 🔌 API Endpoints

### Public Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | Homepage (chatbot interface) |
| POST | `/get` | Chatbot query endpoint |
| GET | `/gallery` | Public gallery view |

### Authentication Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET/POST | `/login` | Student/Admin login |
| GET/POST | `/register` | Student registration |
| GET/POST | `/verify` | OTP verification |
| GET | `/resend_otp` | Resend OTP email |
| GET | `/logout` | Clear session |

### Student Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET/POST | `/chat` | Chatbot interface (authenticated) |
| GET | `/student_dashboard` | Student profile & notices |

### Admin Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/admin` | Admin dashboard |
| POST | `/add_course` | Create new course |
| GET/POST | `/admin/gallery` | Manage gallery images |
| POST | `/admin/notice` | Create notice |
| POST | `/admin/faq` | Create FAQ |
| GET | `/admin/delete/<id>` | Delete gallery image |
| GET | `/admin/delete_faq/<faq_id>` | Delete FAQ |
| GET | `/admin/delete_user/<user_id>` | Delete user |
| GET | `/admin/delete_notice/<notice_id>` | Delete notice |

---

## 💬 Chatbot Query Examples

The chatbot handles intelligent queries like:

```
User: "What are the fees for Computer Science?"
Bot: "The fee for Computer Science is ₹50000 per year."

User: "How many seats are available in BCA?"
Bot: "📌 **BCA**
     • Total Seats: 60
     • Enrolled Students: 45
     • 🟢 Available Seats: 15"

User: "Is today a holiday?"
Bot: "Yes, today (2025-04-30) is National Holiday, a national holiday."

User: "Directions from Library to Cafeteria"
Bot: "[Navigational response with landmark and directions]"

User: "Tell me about the college mission"
Bot: "[College mission statement]"

User: "Is pizza available in canteen?"
Bot: "Yes, Pizza is available."

User: "Latest notice?"
Bot: "📌 **Notice Title**
     Notice message content...
     📂 Category: Academic"
```

---

## 🔐 Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Flask Configuration
FLASK_SECRET_KEY=your-super-secret-key-here-min-32-chars

# Database - MySQL (Primary)
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=campus

# Alternative Database - SQLite (Optional)
SQLALCHEMY_DATABASE_URI=sqlite:///campus.db

# Email Service (Gmail SMTP)
SMTP_EMAIL=your-email@gmail.com
SMTP_APP_PASSWORD=your-gmail-app-password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

# Server Port (Optional)
PORT=5000
```

### Important Notes:
- **`FLASK_SECRET_KEY`**: Must be a long, random string for session security. Generate with:
  ```python
  import secrets
  secrets.token_hex(32)
  ```
- **`SMTP_APP_PASSWORD`**: Must be a **Gmail App Password**, NOT your regular Gmail password
  - Enable 2FA on Gmail account
  - Generate app-specific password at https://myaccount.google.com/apppasswords
- **Database Selection**: 
  - If both MySQL and SQLite are configured, MySQL takes priority
  - SQLite is used for SQLAlchemy models (Gallery, Notice, FAQ)
  - MySQL is used for legacy queries (students, courses, etc.)

---

## 📦 Installation & Setup

### Prerequisites
- Python 3.10+
- MySQL Server (recommended) or SQLite
- pip (Python package manager)
- Gmail account with app password (for OTP emails)

### Step 1: Clone Repository
```bash
git clone <your-repo-url>
cd "PROJECT CAMPUS"
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment
1. Copy environment template:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` with your actual values:
   - Database credentials
   - Gmail app password
   - Flask secret key

### Step 5: Initialize Database
```bash
# First run will auto-create tables
python app.py
```

### Step 6: Run Application
```bash
python app.py
```

Application will start at: **http://127.0.0.1:5000**

### Step 7: Create Admin Account
1. Register a student account at `/register`
2. Connect to database and update user role:
   ```sql
   UPDATE students SET role='admin' WHERE email='your-admin-email@example.com';
   ```
3. Login with admin role to access `/admin`

---

## 🎮 Using the Application

### For Students
1. **Register**: Go to `/register`, create account with course and year
2. **Login**: Email + password → OTP verification → Chat access
3. **Chat**: Ask questions about fees, holidays, directions, menu, etc.
4. **Dashboard**: View profile, enrolled course, and recent notices
5. **Gallery**: Browse campus event photos

### For Admins
1. **Login**: Admin credentials → Dashboard
2. **Manage Gallery**: Upload event images with dates
3. **Post Notices**: Create announcements with optional PDF
4. **Manage FAQs**: Add/delete frequently asked questions
5. **Manage Users**: View all students, delete accounts
6. **Add Courses**: Create course entries with HOD names and fees

---

## 🔍 Chatbot Intent Detection System

The chatbot uses multiple strategies to understand queries:

1. **Pattern Matching** (intents.json): Direct keyword/phrase matching
2. **Navigation Queries**: "from X to Y", "where is", "how to reach"
3. **College Info Queries**: Principal, mission, vision, established year, etc.
4. **Menu Queries**: Canteen items, prices, availability with fuzzy matching
5. **Fee Queries**: Course-specific and all fees listing
6. **Seat Queries**: Available seats and enrollment strength
7. **Holiday Queries**: Today/tomorrow/upcoming holidays, search by name
8. **Notice Queries**: Latest notice with category
9. **FAQ Search**: Semantic similarity matching against stored FAQs
10. **Fallback**: Generic response or FAQ semantic search

---

## ⚙️ Configuration & Customization

### Add New Course
1. Go to Admin Dashboard → Add Course
2. Enter: Course Name, Fees (annual), Total Seats
3. Course becomes available for registration

### Add FAQ
1. Go to Admin Dashboard → FAQ section
2. Enter Question and Answer
3. Chatbot will search FAQs using semantic similarity

### Customize Intents
Edit `intents.json` to add/modify chatbot patterns and responses:
```json
{
  "intents": [
    {
      "tag": "example",
      "patterns": ["pattern1", "pattern2"],
      "responses": ["response1", "response2"]
    }
  ]
}
```

### Add Campus Locations
Insert into `locations` MySQL table:
```sql
INSERT INTO locations 
(name, category, description, landmark, directions, image_url) 
VALUES 
('Library', 'Academic', 'Main library building', 'Near main gate', 'First building on left', 'https://...');
```

---

## 🐛 Troubleshooting

### Common Issues & Solutions

#### 1. Database Connection Error
**Error**: `Can't connect to MySQL server`

**Solutions**:
- Verify MySQL is running: `mysql -u root -p`
- Check `.env` credentials match MySQL setup
- Ensure database `campus` exists: `CREATE DATABASE campus;`
- Verify port 3306 is open and accessible

#### 2. OTP Email Not Sending
**Error**: `Email service is not configured` or timeout

**Solutions**:
- Verify Gmail credentials in `.env`
- Check `SMTP_APP_PASSWORD` is a Gmail app password (not account password)
- Enable 2FA on Gmail: https://myaccount.google.com/security
- Generate new app password
- Check firewall/antivirus blocking SMTP port 587
- Test SMTP connection:
  ```python
  import smtplib
  with smtplib.SMTP("smtp.gmail.com", 587) as server:
      server.starttls()
      server.login("your-email@gmail.com", "app-password")
  ```

#### 3. Session/Login Issues
**Error**: `Redirects to login after successful verification`

**Solutions**:
- Check `FLASK_SECRET_KEY` is set and consistent
- Ensure `session` is properly initialized in routes
- Clear browser cookies and try again
- Check server logs for session errors

#### 4. Static Files Not Loading
**Error**: CSS/JS files return 404

**Solutions**:
- Verify `static/` folder exists with all files
- Check Flask app initialization: `static_folder="static"`
- Restart Flask development server
- Clear browser cache

#### 5. Image Upload Fails
**Error**: `Permission denied` or upload folder issues

**Solutions**:
- Ensure `static/uploads/` and `static/notices/` folders exist
- Check folder write permissions: `chmod 755 static/uploads/`
- Restart Flask after folder creation
- Verify file size isn't exceeding server limits

#### 6. Chatbot Gives Generic Responses
**Error**: Chatbot doesn't understand specific queries

**Solutions**:
- Check database tables (courses, locations, holidays) have data
- Add more patterns to `intents.json`
- Verify `handle_query()` logic for specific intent
- Check cursor queries execute without errors
- Look at server logs for SQL errors

---

## 📝 Development Notes

### Code Organization
- **`app.py`**: Main application (~1900 lines)
  - Database models and initialization
  - Utility functions for queries
  - Intent detection and handling
  - Flask routes and error handlers
- **`chatbot.py`**: Standalone chatbot engine (legacy, similarity-based)
- **`intents.json`**: Intent patterns (extensible)

### Database Connection Management
- Uses `mysql.connector` for MySQL queries
- SQLAlchemy handles Gallery/Notice/FAQ models
- Always close cursor/connection after use
- Context manager approach in some functions

### Security Measures
- Password hashing with Werkzeug
- OTP-based 2FA
- SQL parameterized queries (injection prevention)
- Session-based auth with role checks
- File upload validation (secure_filename)
- HTTPS recommended for production

### Performance Considerations
- Similarity matching (difflib) may be slow with large FAQ databases
- Menu queries use fuzzy matching with cutoff thresholds
- Consider caching frequently accessed data (courses, holidays)
- Database indexes recommended on frequently queried columns

### Future Enhancements
- Implement caching (Redis) for chatbot responses
- Add more NLP features (NLTK, spaCy)
- Multi-language support
- Mobile app/API rate limiting
- Advanced admin analytics
- Student-to-teacher messaging
- Assignment submission portal
- Attendance tracking
- Payment gateway integration

---

## 📄 License
Add your preferred license here (MIT, Apache-2.0, GPL-3.0, etc.)

---

## 👥 Support & Contribution
For issues, questions, or contributions, please contact the development team or submit a pull request.

---

**Last Updated**: April 2026  
**Version**: 1.0  
**Status**: Active Development
