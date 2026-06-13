# Prashasti IAS Academy &mdash; Unified Website + Student Portal

Ek hi Flask application: public marketing website (Home, About, Courses,
Faculty, Results, Testimonials, Gallery, Contact) **+** Student/Admin login
portal &mdash; same navbar mein "Student Login" / "My Dashboard" / "Admin Panel"
link dynamically dikhta hai login status ke according.

## Features

### Public Website (`/`)
- Animated hero, marquee, About, Courses, Why Us, Faculty, Results,
  Testimonials slider, Gallery, Contact form with Google Maps
- Navbar automatically shows "Student Login" (logged out), "My Dashboard"
  (student), or "Admin Panel" (admin)

### Student Portal
- **Registration & Login** &mdash; secure password hashing
- **Dashboard** &mdash; category-wise study material (PDF download + external links)
- **Feedback System** &mdash; rating + message, history visible
- **Profile** &mdash; update details / change password

### Admin Panel
- Upload study material (file or link), delete material
- View all student feedback
- **View/edit registered students** &mdash; complete profiles (batch, fees
  status, address, admin notes), reset passwords, export to Excel
- **View all website enquiries** (from popup + contact form), delete, export
  to Excel
- Dashboard with quick stats (students, materials, feedback, enquiries)


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

### 3. Initialize the database

This creates the SQLite database and a default admin account.

```bash
export FLASK_APP=app.py        # Windows: set FLASK_APP=app.py
flask init-db
```

This will print:
```
Admin login -> email: admin@prashastiias.com | password: admin123
IMPORTANT: Change this password after first login!
```

**Change this password immediately** after logging in (via Profile page).

### 4. Run the server

```bash
python app.py
```

Visit `http://localhost:5000` in your browser.

## Folder Structure

```
prashasti-ias-backend/
├── app.py                  # Main Flask app (routes, db logic)
├── requirements.txt
├── Procfile                 # For Render/Gunicorn deployment
├── prashasti.db             # SQLite database (auto-created)
├── static/
│   ├── css/
│   │   ├── main.css          # Main website styling (animations, theme)
│   │   └── portal.css        # Login/Dashboard/Admin styling
│   ├── js/
│   │   ├── main.js            # Main website animations/interactions
│   │   └── portal.js          # Portal form interactions
│   ├── img/                   # Add real academy photos here (about-academy.jpg etc.)
│   └── uploads/                # Uploaded study material files
└── templates/
    ├── index.html              # Full marketing homepage (Home/About/Courses/.../Contact)
    ├── base.html                # Layout for portal pages
    ├── login.html
    ├── register.html
    ├── dashboard.html            # Student dashboard
    ├── profile.html
    ├── admin_dashboard.html
    ├── admin_materials.html      # Upload/manage material
    ├── admin_feedbacks.html
    ├── admin_students.html
    └── error.html
```

## Deploy on Render.com (Free, for Demo)

### 1. Push code to GitHub

Create a new GitHub repo (e.g. `prashasti-ias-portal`) and push this folder:

```bash
cd prashasti-ias-backend
git init
git add .
git commit -m "Initial commit - Prashasti IAS Student Portal"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/prashasti-ias-portal.git
git push -u origin main
```

### 2. Create a new Web Service on Render

1. Go to [render.com](https://render.com) and sign in (with GitHub).
2. Click **New +** &rarr; **Web Service**.
3. Select your `prashasti-ias-portal` repo.
4. Fill in:
   - **Name**: `prashasti-ias-portal` (or anything)
   - **Region**: closest to you (e.g. Singapore)
   - **Branch**: `main`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free
5. Click **Create Web Service**.

Render automatically installs dependencies and runs `gunicorn app:app`
(this is also defined in the included `Procfile`). The database and
default admin account are created automatically on first startup
(`ensure_db_ready()` runs when the app loads).

### 3. Access your demo

After 2-5 minutes, Render gives you a URL like:

```
https://prashasti-ias-portal.onrender.com
```

- Visit `/login` to log in.
- Admin: `admin@prashastiias.com` / `admin123` &mdash; **change this password
  immediately** via Profile after logging in.
- Visit `/register` to create a test student account.

### Important Notes for Free Tier

- **Spins down on inactivity**: Free Render services sleep after ~15 mins
  of no traffic; the first request after that takes ~30-50 seconds to wake up.
  Fine for demos.
- **File storage is not persistent**: On Render's free tier, uploaded files
  (in `static/uploads/`) and the SQLite database (`prashasti.db`) are stored
  on an ephemeral filesystem &mdash; they get wiped on every redeploy/restart.
  This is **fine for a demo** (admin account regenerates automatically), but
  for **production** you should:
  - Use a paid Render plan with a **persistent disk** (mount it at e.g.
    `/data` and update `DB_PATH`/`UPLOAD_FOLDER` in `app.py` to point there), or
  - Switch to a managed database (e.g. Render's PostgreSQL) and a cloud
    storage bucket (e.g. AWS S3, Cloudinary) for uploaded files.

---

## Database

SQLite use ho raha hai (`prashasti.db`) &mdash; simple aur zero-config, raw
`sqlite3` module se. Production mein zyada users hone par PostgreSQL mein
switch kiya ja sakta hai by updating the DB helper functions in `app.py`.

## Security Notes Before Going Live

1. `app.config['SECRET_KEY']` ko ek strong random value se replace karein.
2. Default admin password (`admin123`) ko immediately change karein.
3. Production mein `debug=True` hata dein.
4. HTTPS use karein (production deployment ke liye Gunicorn + Nginx ya
   similar setup recommended hai).
5. File upload size limit already 25MB set hai (`MAX_CONTENT_LENGTH`),
   apni zaroorat ke according adjust kar sakte hain.

## Adding More Admins

Currently sirf ek default admin banta hai automatically (`admin@prashastiias.com`).
Aur admins add karne ke liye, database mein directly kisi existing user ka
`is_admin` field `1` set karein (SQLite browser ya `sqlite3 prashasti.db`
se), ya `app.py` mein ek custom CLI command add kar sakte hain.

## Adding Real Photos

`static/img/` folder mein yeh files daal dein, automatically homepage par
dikhne lagengi (abhi placeholder/emoji dikh raha hai):
- `about-academy.jpg` &mdash; About section mein academy ki photo

