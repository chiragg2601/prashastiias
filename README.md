# Prashasti IAS Academy &mdash; Website + Admin Panel

Ek hi Flask application: public marketing website (Home, About, Courses,
Faculty, Results, Testimonials, Gallery, Study Material, Contact) **+**
Admin-only panel for managing content. **Koi student login/registration
nahi hai** &mdash; sirf admin login hota hai, baaki sab public hai.

## Features

### Public Website (`/`)
- Animated hero, marquee, About, Courses, Why Us, Faculty, Results,
  Testimonials, Gallery, Contact form with Google Maps
- **30-second enquiry popup** (Name, Phone, Course) on every visit
- **Public feedback form** (no login needed) with star rating
- **Study Material page** (`/study-material`) &mdash; publicly accessible,
  admin-uploaded PDFs/links shown by category
- Photos (Coaching, Faculty, Students & Results, Gallery) shown dynamically
  wherever admin has uploaded them; falls back to emoji/icon placeholders
  if none uploaded yet

### Admin Panel (login required)
- **Study Material** &mdash; upload (file or external link), delete, organized by category
- **Photos** &mdash; upload/delete photos under 4 categories (Coaching, Faculty,
  Students & Results, Gallery); these automatically appear on the public site
- **Feedback** &mdash; view all public feedback submissions, delete, export to Excel
- **Enquiries** &mdash; view all popup/contact-form submissions, delete, export to Excel
- **Profile** &mdash; change admin name/phone/password
- Dashboard with quick stats (materials, photos, feedback, enquiries)

## Setup Instructions

### 1. Create a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the server

The database, tables, and default admin account are created automatically
on first run &mdash; no separate init command needed.

```bash
python app.py
```

Visit `http://localhost:5000` in your browser.

**Default admin login:**
- Email: `admin@prashastiias.com`
- Password: `admin123`

**Change this password immediately** after logging in (via Profile page,
top nav after login).

## Folder Structure

```
prashasti-ias-backend/
├── app.py                  # Main Flask app (routes, db logic)
├── requirements.txt
├── Procfile                 # For Render/Gunicorn deployment
├── prashasti.db             # SQLite database (auto-created)
├── static/
│   ├── css/
│   │   ├── main.css            # Main website styling (animations, theme)
│   │   ├── portal.css           # Login/Admin panel styling
│   │   └── study_material.css   # Public study material page styling
│   ├── js/
│   │   ├── main.js               # Main website animations/interactions
│   │   └── portal.js              # Admin panel form interactions
│   ├── photos/                     # Admin-uploaded category photos
│   └── uploads/                     # Admin-uploaded study material files
└── templates/
    ├── index.html               # Full marketing homepage
    ├── study_material.html       # Public study material listing page
    ├── base.html                  # Layout for admin panel pages
    ├── login.html                  # Admin login
    ├── profile.html
    ├── admin_dashboard.html
    ├── admin_materials.html        # Upload/manage study material
    ├── admin_photos.html            # Upload/manage category photos
    ├── admin_feedbacks.html
    ├── admin_enquiries.html
    └── error.html
```

## Deploy on Render.com (Free, for Demo)

### 1. Push code to GitHub

```bash
cd prashasti-ias-backend
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/prashasti-ias-portal.git
git push -u origin main
```

### 2. Create a new Web Service on Render

1. Go to [render.com](https://render.com) and sign in (with GitHub).
2. Click **New +** &rarr; **Web Service**.
3. Select your repo.
4. Fill in:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free
5. Click **Create Web Service**.

### 3. Access your demo

After a few minutes, Render gives you a URL like
`https://prashasti-ias-portal.onrender.com`. Admin panel is at `/login`.

### Important Notes for Free Tier

- **Spins down on inactivity**: free services sleep after ~15 mins of no
  traffic; first request after that takes ~30-50 seconds to wake up.
- **File storage is not persistent**: uploaded photos/materials and the
  SQLite database get wiped on every redeploy on the free tier. Fine for a
  demo (the admin account regenerates automatically). For production,
  use a paid plan with a **persistent disk**, or move to a managed DB
  (e.g. Render PostgreSQL) and cloud storage (e.g. S3, Cloudinary).

---

## Security Notes Before Going Live

1. Replace `app.config['SECRET_KEY']` with a strong random value.
2. Change the default admin password (`admin123`) immediately.
3. Remove `debug=True` in production.
4. Use HTTPS (Gunicorn + Nginx or similar).
5. File upload size limit is 25MB (`MAX_CONTENT_LENGTH`); adjust as needed.

## Adding More Admins

Only one default admin is created automatically. To add more, connect to
the SQLite DB (`sqlite3 prashasti.db`) and either insert a new row in
`user` with `is_admin = 1`, or update an existing user's `is_admin` field.

## Photo Categories Explained

- **Coaching** &mdash; shown as the main photo in the About section (use one photo)
- **Faculty** &mdash; each upload becomes a faculty card in the Faculty section
- **Students & Results** &mdash; used in the Results section photo slots
- **Gallery** &mdash; shown in the Gallery grid section
