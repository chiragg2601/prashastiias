import os
import sqlite3
from io import BytesIO
from datetime import datetime
from functools import wraps

from flask import (Flask, render_template, request, redirect, url_for, flash, session, abort,
                    send_from_directory, send_file, g)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
DB_PATH = os.path.join(BASE_DIR, 'prashasti.db')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-secret-key-in-production'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25 MB max upload

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ===================== DATABASE HELPERS =====================

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db_schema():
    db = sqlite3.connect(DB_PATH)
    db.executescript('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            course TEXT,
            batch TEXT,
            address TEXT,
            fees_status TEXT,
            notes TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS study_material (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT,
            material_type TEXT NOT NULL,
            filename TEXT,
            original_filename TEXT,
            link_url TEXT,
            uploaded_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT,
            message TEXT NOT NULL,
            rating INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS enquiry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            course TEXT,
            message TEXT,
            source TEXT,
            created_at TEXT NOT NULL
        );
    ''')

    # Migrate older databases that may be missing the new user columns
    existing_cols = {row[1] for row in db.execute('PRAGMA table_info(user)').fetchall()}
    for col in ('batch', 'address', 'fees_status', 'notes'):
        if col not in existing_cols:
            db.execute(f'ALTER TABLE user ADD COLUMN {col} TEXT')

    db.commit()
    db.close()


def now_str():
    return datetime.utcnow().isoformat(timespec='seconds')


def parse_dt(value):
    """Parse an ISO datetime string back into a datetime object."""
    return datetime.fromisoformat(value)


def build_excel(headers, rows, sheet_title='Data'):
    """Build an in-memory .xlsx file from a list of column headers and row tuples/lists."""
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_title

    header_font = Font(bold=True, color='FFFFFF', name='Arial')
    header_fill = PatternFill('solid', start_color='0F1F3D')
    header_align = Alignment(horizontal='center', vertical='center')

    ws.append(headers)
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align

    for row in rows:
        ws.append(row)

    for col_cells in ws.columns:
        max_len = max((len(str(c.value)) if c.value is not None else 0) for c in col_cells)
        ws.column_dimensions[col_cells[0].column_letter].width = min(max(max_len + 2, 12), 50)

    ws.freeze_panes = 'A2'

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


# ===================== HELPERS =====================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'error')
            return redirect(url_for('login'))
        db = get_db()
        user = db.execute('SELECT * FROM user WHERE id = ?', (session['user_id'],)).fetchone()
        if not user or not user['is_admin']:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@app.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        db = get_db()
        row = db.execute('SELECT * FROM user WHERE id = ?', (session['user_id'],)).fetchone()
        if row:
            user = dict(row)
    return dict(current_user=user)


@app.template_filter('fmtdate')
def fmtdate(value, fmt='%d %b %Y, %I:%M %p'):
    try:
        return parse_dt(value).strftime(fmt)
    except (ValueError, TypeError):
        return value


# ===================== PUBLIC ROUTES =====================

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/enquiry', methods=['POST'])
def submit_enquiry():
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    course = request.form.get('course', '').strip()
    message = request.form.get('message', '').strip()
    source = request.form.get('source', 'website').strip()

    if not name or not phone:
        return {'success': False, 'error': 'Name and phone are required.'}, 400

    db = get_db()
    db.execute(
        'INSERT INTO enquiry (name, phone, email, course, message, source, created_at) '
        'VALUES (?, ?, ?, ?, ?, ?, ?)',
        (name, phone, email, course, message, source, now_str())
    )
    db.commit()

    return {'success': True}


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        course = request.form.get('course', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if not name or not email or not password:
            flash('Please fill all required fields.', 'error')
            return redirect(url_for('register'))

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))

        db = get_db()
        existing = db.execute('SELECT id FROM user WHERE email = ?', (email,)).fetchone()
        if existing:
            flash('An account with this email already exists. Please log in.', 'error')
            return redirect(url_for('login'))

        password_hash = generate_password_hash(password)
        db.execute(
            'INSERT INTO user (name, email, phone, password_hash, is_admin, course, created_at) '
            'VALUES (?, ?, ?, ?, 0, ?, ?)',
            (name, email, phone, password_hash, course, now_str())
        )
        db.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        db = get_db()
        user = db.execute('SELECT * FROM user WHERE email = ?', (email,)).fetchone()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['is_admin'] = bool(user['is_admin'])
            flash(f"Welcome back, {user['name']}!", 'success')
            if user['is_admin']:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))

        flash('Invalid email or password.', 'error')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))


# ===================== STUDENT ROUTES =====================

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    user = db.execute('SELECT * FROM user WHERE id = ?', (session['user_id'],)).fetchone()

    if user['is_admin']:
        return redirect(url_for('admin_dashboard'))

    materials = db.execute('SELECT * FROM study_material ORDER BY uploaded_at DESC').fetchall()
    my_feedbacks = db.execute(
        'SELECT * FROM feedback WHERE user_id = ? ORDER BY created_at DESC', (user['id'],)
    ).fetchall()

    # group materials by category
    categories = {}
    for m in materials:
        cat = m['category'] or 'General'
        categories.setdefault(cat, []).append(m)

    return render_template('dashboard.html', user=user, categories=categories, my_feedbacks=my_feedbacks)


@app.route('/material/download/<int:material_id>')
@login_required
def download_material(material_id):
    db = get_db()
    material = db.execute('SELECT * FROM study_material WHERE id = ?', (material_id,)).fetchone()
    if not material or material['material_type'] != 'file' or not material['filename']:
        abort(404)
    return send_from_directory(app.config['UPLOAD_FOLDER'], material['filename'],
                                 as_attachment=True, download_name=material['original_filename'])


@app.route('/feedback', methods=['POST'])
@login_required
def submit_feedback():
    subject = request.form.get('subject', '').strip()
    message = request.form.get('message', '').strip()
    rating = request.form.get('rating', '0')

    if not message:
        flash('Feedback message cannot be empty.', 'error')
        return redirect(url_for('dashboard'))

    try:
        rating_val = int(rating)
        if rating_val < 1 or rating_val > 5:
            rating_val = None
    except ValueError:
        rating_val = None

    db = get_db()
    db.execute(
        'INSERT INTO feedback (user_id, subject, message, rating, created_at) VALUES (?, ?, ?, ?, ?)',
        (session['user_id'], subject, message, rating_val, now_str())
    )
    db.commit()

    flash('Thank you! Your feedback has been submitted.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    db = get_db()
    user = db.execute('SELECT * FROM user WHERE id = ?', (session['user_id'],)).fetchone()

    if request.method == 'POST':
        name = request.form.get('name', user['name']).strip()
        phone = request.form.get('phone', user['phone'] or '').strip()
        course = request.form.get('course', user['course'] or '').strip()
        new_password = request.form.get('new_password', '').strip()

        if new_password:
            password_hash = generate_password_hash(new_password)
            db.execute(
                'UPDATE user SET name = ?, phone = ?, course = ?, password_hash = ? WHERE id = ?',
                (name, phone, course, password_hash, user['id'])
            )
        else:
            db.execute(
                'UPDATE user SET name = ?, phone = ?, course = ? WHERE id = ?',
                (name, phone, course, user['id'])
            )
        db.commit()
        session['user_name'] = name
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', user=user)


# ===================== ADMIN ROUTES =====================

@app.route('/admin')
@admin_required
def admin_dashboard():
    db = get_db()
    total_students = db.execute('SELECT COUNT(*) FROM user WHERE is_admin = 0').fetchone()[0]
    total_materials = db.execute('SELECT COUNT(*) FROM study_material').fetchone()[0]
    total_feedbacks = db.execute('SELECT COUNT(*) FROM feedback').fetchone()[0]
    total_enquiries = db.execute('SELECT COUNT(*) FROM enquiry').fetchone()[0]

    recent_feedbacks = db.execute('''
        SELECT feedback.*, user.name AS user_name, user.email AS user_email
        FROM feedback
        JOIN user ON feedback.user_id = user.id
        ORDER BY feedback.created_at DESC
        LIMIT 5
    ''').fetchall()

    recent_enquiries = db.execute(
        'SELECT * FROM enquiry ORDER BY created_at DESC LIMIT 5'
    ).fetchall()

    return render_template('admin_dashboard.html',
                            total_students=total_students,
                            total_materials=total_materials,
                            total_feedbacks=total_feedbacks,
                            total_enquiries=total_enquiries,
                            recent_feedbacks=recent_feedbacks,
                            recent_enquiries=recent_enquiries)


@app.route('/admin/materials', methods=['GET', 'POST'])
@admin_required
def admin_materials():
    db = get_db()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip()
        material_type = request.form.get('material_type')  # 'file' or 'link'

        if not title:
            flash('Title is required.', 'error')
            return redirect(url_for('admin_materials'))

        filename = None
        original_filename = None
        link_url = None

        if material_type == 'file':
            file = request.files.get('file')
            if not file or file.filename == '':
                flash('Please select a file to upload.', 'error')
                return redirect(url_for('admin_materials'))
            if not allowed_file(file.filename):
                flash('File type not allowed.', 'error')
                return redirect(url_for('admin_materials'))

            original_filename = secure_filename(file.filename)
            filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{original_filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        elif material_type == 'link':
            link_url = request.form.get('link_url', '').strip()
            if not link_url:
                flash('Please provide a link URL.', 'error')
                return redirect(url_for('admin_materials'))

        else:
            flash('Invalid material type.', 'error')
            return redirect(url_for('admin_materials'))

        db.execute(
            'INSERT INTO study_material '
            '(title, description, category, material_type, filename, original_filename, link_url, uploaded_at) '
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (title, description, category, material_type, filename, original_filename, link_url, now_str())
        )
        db.commit()
        flash('Study material added successfully.', 'success')
        return redirect(url_for('admin_materials'))

    materials = db.execute('SELECT * FROM study_material ORDER BY uploaded_at DESC').fetchall()
    return render_template('admin_materials.html', materials=materials)


@app.route('/admin/materials/delete/<int:material_id>', methods=['POST'])
@admin_required
def delete_material(material_id):
    db = get_db()
    material = db.execute('SELECT * FROM study_material WHERE id = ?', (material_id,)).fetchone()
    if not material:
        abort(404)

    if material['material_type'] == 'file' and material['filename']:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], material['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)

    db.execute('DELETE FROM study_material WHERE id = ?', (material_id,))
    db.commit()
    flash('Study material deleted.', 'success')
    return redirect(url_for('admin_materials'))


@app.route('/admin/feedbacks')
@admin_required
def admin_feedbacks():
    db = get_db()
    feedbacks = db.execute('''
        SELECT feedback.*, user.name AS user_name, user.email AS user_email
        FROM feedback
        JOIN user ON feedback.user_id = user.id
        ORDER BY feedback.created_at DESC
    ''').fetchall()
    return render_template('admin_feedbacks.html', feedbacks=feedbacks)


@app.route('/admin/students')
@admin_required
def admin_students():
    db = get_db()
    students = db.execute(
        'SELECT * FROM user WHERE is_admin = 0 ORDER BY created_at DESC'
    ).fetchall()
    return render_template('admin_students.html', students=students)


@app.route('/admin/students/export')
@admin_required
def export_students():
    db = get_db()
    students = db.execute(
        'SELECT * FROM user WHERE is_admin = 0 ORDER BY created_at DESC'
    ).fetchall()

    headers = ['Name', 'Email', 'Phone', 'Course', 'Batch', 'Fees Status', 'Address', 'Notes', 'Joined On']
    rows = []
    for s in students:
        rows.append([
            s['name'], s['email'], s['phone'] or '', s['course'] or '',
            s['batch'] or '', s['fees_status'] or '', s['address'] or '',
            s['notes'] or '', fmtdate(s['created_at'], '%d %b %Y')
        ])

    buf = build_excel(headers, rows, sheet_title='Students')
    filename = f"students_{datetime.utcnow().strftime('%Y%m%d')}.xlsx"
    return send_file(buf, as_attachment=True, download_name=filename,
                      mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@app.route('/admin/students/edit/<int:student_id>', methods=['GET', 'POST'])
@admin_required
def edit_student(student_id):
    db = get_db()
    student = db.execute('SELECT * FROM user WHERE id = ? AND is_admin = 0', (student_id,)).fetchone()
    if not student:
        abort(404)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        course = request.form.get('course', '').strip()
        batch = request.form.get('batch', '').strip()
        fees_status = request.form.get('fees_status', '').strip()
        address = request.form.get('address', '').strip()
        notes = request.form.get('notes', '').strip()
        new_password = request.form.get('new_password', '').strip()

        if not name:
            flash('Name is required.', 'error')
            return redirect(url_for('edit_student', student_id=student_id))

        if new_password:
            password_hash = generate_password_hash(new_password)
            db.execute(
                'UPDATE user SET name=?, phone=?, course=?, batch=?, fees_status=?, address=?, notes=?, password_hash=? WHERE id=?',
                (name, phone, course, batch, fees_status, address, notes, password_hash, student_id)
            )
        else:
            db.execute(
                'UPDATE user SET name=?, phone=?, course=?, batch=?, fees_status=?, address=?, notes=? WHERE id=?',
                (name, phone, course, batch, fees_status, address, notes, student_id)
            )
        db.commit()
        flash('Student profile updated successfully.', 'success')
        return redirect(url_for('admin_students'))

    return render_template('admin_edit_student.html', student=student)


@app.route('/admin/enquiries')
@admin_required
def admin_enquiries():
    db = get_db()
    enquiries = db.execute('SELECT * FROM enquiry ORDER BY created_at DESC').fetchall()
    return render_template('admin_enquiries.html', enquiries=enquiries)


@app.route('/admin/enquiries/export')
@admin_required
def export_enquiries():
    db = get_db()
    enquiries = db.execute('SELECT * FROM enquiry ORDER BY created_at DESC').fetchall()

    headers = ['Name', 'Phone', 'Email', 'Course', 'Message', 'Source', 'Submitted On']
    rows = []
    for e in enquiries:
        rows.append([
            e['name'], e['phone'], e['email'] or '', e['course'] or '',
            e['message'] or '', e['source'] or '', fmtdate(e['created_at'])
        ])

    buf = build_excel(headers, rows, sheet_title='Enquiries')
    filename = f"enquiries_{datetime.utcnow().strftime('%Y%m%d')}.xlsx"
    return send_file(buf, as_attachment=True, download_name=filename,
                      mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@app.route('/admin/enquiries/delete/<int:enquiry_id>', methods=['POST'])
@admin_required
def delete_enquiry(enquiry_id):
    db = get_db()
    db.execute('DELETE FROM enquiry WHERE id = ?', (enquiry_id,))
    db.commit()
    flash('Enquiry deleted.', 'success')
    return redirect(url_for('admin_enquiries'))


# ===================== ERROR HANDLERS =====================

@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', code=403, message='Access Forbidden'), 403


@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', code=404, message='Page Not Found'), 404


def ensure_db_ready():
    """Create DB schema and default admin if not already present. Safe to call on every startup."""
    if not os.path.exists(DB_PATH):
        init_db_schema()
    else:
        init_db_schema()  # CREATE TABLE IF NOT EXISTS is safe to re-run

    db = sqlite3.connect(DB_PATH)
    admin_email = 'admin@prashastiias.com'
    existing = db.execute('SELECT id FROM user WHERE email = ?', (admin_email,)).fetchone()
    if not existing:
        password_hash = generate_password_hash('admin123')
        db.execute(
            'INSERT INTO user (name, email, phone, password_hash, is_admin, course, created_at) '
            'VALUES (?, ?, ?, ?, 1, ?, ?)',
            ('Admin', admin_email, '', password_hash, 'Admin', now_str())
        )
        db.commit()
    db.close()


# ===================== CLI: CREATE DB & ADMIN =====================

@app.cli.command('init-db')
def init_db_command():
    """Initialize the database and create a default admin user."""
    ensure_db_ready()
    print('Database initialized.')
    print('Admin login -> email: admin@prashastiias.com | password: admin123')
    print('IMPORTANT: Change this password after first login!')


# Ensure DB is ready whenever the module is imported (works with gunicorn too)
ensure_db_ready()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
