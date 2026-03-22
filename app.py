from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import pymysql
import pymysql.cursors
from db.School_db import init_db, get_db_connection
import os
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24) # បង្កើត Secret Key សុវត្ថិភាព

# ==========================================
# Helper functions for class management
# ==========================================
def _class_payload(data):
    """Prepare class payload to match current DB fields."""
    return {
        'class_name': data.get('class_name'),
        'department_id': data.get('department_id'),
        'session_type': data.get('session_type'),
        'room_id': data.get('room_id'),
        'academic_year_id': data.get('academic_year_id') or data.get('year_id'),
        'id': data.get('id'),
        # Keep for old schema that still stores room_name in classes.
        'room_name': data.get('room_name'),
    }


def _validate_class_payload(payload, require_id=False):
    """Validate class payload and return error message or None."""
    if require_id and not payload.get('id'):
        return 'សូមបងាញលេខសម្គាល់ថ្នាក់រៀន!'
    if not payload.get('class_name'):
        return 'សូមបញ្ចូលឈ្មោះថ្នាក់រៀន!'
    if not payload.get('department_id'):
        return 'សូមជ្រើសរើសដេប៉ាតឺម៉ង់!'
    return None


def _get_class_schema(cursor):
    """Detect class table schema and return column info."""
    schema = {
        'has_academic_year_id': False,
        'has_room_id': False,
        'has_room_name': False,
        'has_buildings': False,
        'has_room_building_id': False,
        'room_table': None,
    }
    
    cursor.execute("SHOW COLUMNS FROM classes LIKE 'academic_year_id'")
    schema['has_academic_year_id'] = cursor.fetchone() is not None
    
    cursor.execute("SHOW COLUMNS FROM classes LIKE 'room_id'")
    schema['has_room_id'] = cursor.fetchone() is not None
    
    cursor.execute("SHOW COLUMNS FROM classes LIKE 'room_name'")
    schema['has_room_name'] = cursor.fetchone() is not None
    
    cursor.execute("SHOW TABLES LIKE 'rooms'")
    has_rooms = cursor.fetchone() is not None
    schema['room_table'] = 'rooms' if has_rooms else 'room'
    
    cursor.execute("SHOW TABLES LIKE 'buildings'")
    schema['has_buildings'] = cursor.fetchone() is not None
    
    if schema['has_buildings'] and schema['room_table']:
        cursor.execute(f"SHOW COLUMNS FROM {schema['room_table']} LIKE 'building_id'")
        schema['has_room_building_id'] = cursor.fetchone() is not None
    
    return schema


def _build_class_insert_sql(cursor, payload, schema):
    """Build INSERT SQL for class with detected schema."""
    columns = ['class_name', 'session_type', 'department_id']
    values = [payload['class_name'], payload.get('session_type'), payload['department_id']]
    
    if schema['has_academic_year_id']:
        columns.append('academic_year_id')
        values.append(payload.get('academic_year_id'))
    
    if schema['has_room_id']:
        columns.append('room_id')
        values.append(payload.get('room_id'))
    
    if schema['has_room_name']:
        columns.append('room_name')
        values.append(payload.get('room_name'))
    
    placeholders = ', '.join(['%s'] * len(columns))
    sql = f"INSERT INTO classes ({', '.join(columns)}) VALUES ({placeholders})"
    
    return sql, tuple(values)


def _build_class_update_sql(cursor, payload, schema):
    """Build UPDATE SQL for class with detected schema."""
    set_parts = ['class_name = %s', 'session_type = %s', 'department_id = %s']
    params = [payload['class_name'], payload.get('session_type'), payload['department_id']]
    
    if schema['has_academic_year_id']:
        set_parts.append('academic_year_id = %s')
        params.append(payload.get('academic_year_id'))
    
    if schema['has_room_id']:
        set_parts.append('room_id = %s')
        params.append(payload.get('room_id'))
    
    if schema['has_room_name']:
        set_parts.append('room_name = %s')
        params.append(payload.get('room_name'))
    
    sql = f"UPDATE classes SET {', '.join(set_parts)} WHERE id = %s"
    params.append(payload['id'])
    
    return sql, tuple(params)


def _class_integrity_response(error, include_fk=False):
    """Handle integrity errors for class operations."""
    error_msg = str(error).lower()
    if 'duplicate entry' in error_msg:
        return jsonify({'status': 'error', 'message': 'ឈ្មោះថ្នាក់រៀននេះមានរួចហើយ!'}), 400
    if include_fk and 'foreign key constraint fails' in error_msg:
        return jsonify({'status': 'error', 'message': 'មិនអាចលុបបានទេ ព្រោះមានទិន្នន័យជាប់ទាក់ទងនឹងថ្នាក់រៀននេះ!'}), 400
    return jsonify({'status': 'error', 'message': f'បញ្ហាទិន្នន័យ: {str(error)}'}), 400


def _normalize_dob(value):
    """Convert various DOB formats to YYYY-MM-DD for MySQL DATE."""
    if not value:
        return None

    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d')

    value = str(value).strip()
    if not value:
        return None

    # Accept plain ISO date first.
    try:
        return datetime.strptime(value, '%Y-%m-%d').strftime('%Y-%m-%d')
    except ValueError:
        pass

    # Accept common JS/browser date string, e.g. "Mon, 12 Feb 2007 00:00:00 GMT".
    for fmt in (
        '%a, %d %b %Y %H:%M:%S GMT',
        '%a %b %d %Y %H:%M:%S GMT%z',
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%d %H:%M:%S',
    ):
        try:
            return datetime.strptime(value, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue

    # Last fallback: take date portion if ISO-like datetime comes in.
    if len(value) >= 10:
        head = value[:10]
        try:
            return datetime.strptime(head, '%Y-%m-%d').strftime('%Y-%m-%d')
        except ValueError:
            pass

    return None


def _get_report_sql(report_type, cursor):
    """Generate SQL for report requests."""
    if report_type == 'students':
        return """
            SELECT
                u.name,
                COALESCE(s.subject_name, 'មិនទាន់កំណត់') AS subject_display
            FROM users u
            LEFT JOIN user_profiles up ON u.id = up.user_id
            LEFT JOIN subjects s ON up.department_id = s.department_id
            WHERE u.role = 'Student'
        """
    elif report_type == 'teachers':
        return """
            SELECT u.id, u.name, u.email, u.role, u.status,
                   p.id_number, p.phone, p.address
            FROM users u
            LEFT JOIN user_profiles p ON u.id = p.user_id
            WHERE LOWER(u.role) = 'teacher'
            ORDER BY u.name
        """
    elif report_type == 'classes':
        return """
            SELECT id, class_name, session_type, department_id
            FROM classes
            ORDER BY class_name
        """
    elif report_type == 'subjects':
        return """
            SELECT s.id, s.subject_name, s.credits, s.semester,
                   d.department_name, a.year_name
            FROM subjects s
            LEFT JOIN department d ON s.department_id = d.id
            LEFT JOIN academic_year a ON s.year_id = a.id
            ORDER BY s.subject_name
        """
    elif report_type == 'attendance':
        return """
            SELECT a.id, a.student_id, a.subject_id, a.status,
                   u.name as student_name, s.subject_name
            FROM attendance a
            JOIN users u ON a.student_id = u.id
            JOIN subjects s ON a.subject_id = s.id
            ORDER BY u.name, s.subject_name
        """
    return None

@app.route('/api/admin/available_teacher_users', methods=['GET'])
def get_available_teachers():
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    # យកតែអ្នកដែលមាន Role='Teacher' ហើយមិនទាន់មានក្នុងតារាង teachers
    sql = """
        SELECT id, name, email FROM users 
        WHERE role = 'Teacher' 
        AND id NOT IN (SELECT user_id FROM teachers)
    """
    cursor.execute(sql)
    users = cursor.fetchall()
    conn.close()
    return jsonify({'status': 'success', 'data': users})
# ==========================================
# Decorators សម្រាប់កំណត់សិទ្ធិ (Permissions)
# ==========================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('សូមចូលប្រើប្រាស់គណនីរបស់អ្នកជាមុនសិន។', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('អ្នកមិនមានសិទ្ធិចូលកាន់ទំព័រនេះទេ!', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):

            if 'user_id' not in session:
                flash('សូមចូលប្រើប្រាស់គណនីរបស់អ្នកជាមុនសិន។', 'warning')
                return redirect(url_for('login'))

            if session.get('role') not in roles:
                flash('អ្នកមិនមានសិទ្ធិចូលកាន់ទំព័រនេះទេ!', 'danger')
                return redirect(url_for('dashboard'))

            return f(*args, **kwargs)

        return decorated_function
    return wrapper

@app.route('/api/admin/colleges', methods=['GET'])
@admin_required
def get_admin_colleges():
    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    cursor = None
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            """
            SELECT id, college_name
            FROM colleges
            ORDER BY college_name ASC
            """
        )
        data = cursor.fetchall() or []
        return jsonify({'status': 'success', 'data': data})
    except pymysql.MySQLError as err:
        return jsonify({'status': 'error', 'message': str(err)}), 500
    finally:
        if cursor:
            cursor.close()
        conn.close()


@app.route('/api/admin/departments', methods=['GET'])
@admin_required
def get_admin_departments():
    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    cursor = None
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            """
            SELECT id, department_name, college_id
            FROM department
            ORDER BY department_name ASC
            """
        )
        data = cursor.fetchall() or []
        return jsonify({'status': 'success', 'data': data})
    except pymysql.MySQLError as err:
        return jsonify({'status': 'error', 'message': str(err)}), 500
    finally:
        if cursor:
            cursor.close()
        conn.close()

# ==========================================
# Routes សម្រាប់ Login និង Logout
# ==========================================
@app.route('/')
def home():
    if 'loggedin' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'loggedin' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if user and user['password'] == password: # ពិនិត្យ Password
                session['loggedin'] = True
                session['user_id'] = user['id']
                session['role'] = user['role'].lower()
                session['name'] = user['name']
                
                flash('ស្វាគមន៍មកកាន់ Dashboard!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('អ៊ីមែល ឬ ពាក្យសម្ងាត់មិនត្រឹមត្រូវទេ!', 'error')
        else:
            flash('មិនអាចភ្ជាប់ទៅកាន់ Database បានទេ!', 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear() # លុប Session ទាំងអស់
    return redirect(url_for('login'))

# ==========================================
# Route សម្រាប់ Dashboard (ទាញយកទិន្នន័យ)
# ==========================================
@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session.get('user_id')
    conn = get_db_connection()

    users_list, departments, academic_years, timetables = [], [], [], []
    colleges_list, classes_list, generations_data = [], [], []
    roles = ['Admin', 'Teacher', 'Student']
    my_profile = None

    if conn:
        cursor = None
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            sql_all_users = """
                SELECT u.id, u.name, u.email, u.role, u.status,
                       p.id_number, p.phone, p.address,
                       d.department_name AS department,
                       a.year_name AS academic_year
                FROM users u
                LEFT JOIN user_profiles p ON u.id = p.user_id
                LEFT JOIN department d ON p.department_id = d.id
                LEFT JOIN academic_year a ON p.academic_year_id = a.id
            """
            cursor.execute(sql_all_users)
            users_list = cursor.fetchall() or []
            my_profile = next((u for u in users_list if u.get('id') == user_id), None)

            cursor.execute("SELECT id, department_name, college_id FROM department")
            departments = cursor.fetchall() or []

            cursor.execute("SELECT id, year_name FROM academic_year")
            academic_years = cursor.fetchall() or []

            cursor.execute("SELECT id, college_name FROM colleges")
            colleges_list = cursor.fetchall() or []

            cursor.execute("SELECT id, class_name, session_type FROM classes")
            classes_list = cursor.fetchall() or []

            cursor.execute("SELECT id, generation_name FROM generations")
            generations_data = cursor.fetchall() or []

            # Detect room schema for timetable
            cursor.execute("SHOW TABLES LIKE 'rooms'")
            has_rooms = cursor.fetchone() is not None
            cursor.execute("SHOW TABLES LIKE 'room'")
            has_room = cursor.fetchone() is not None
            room_table = 'rooms' if has_rooms else ('room' if has_room else None)

            cursor.execute("SHOW COLUMNS FROM timetable LIKE 'room_id'")
            has_room_id = cursor.fetchone() is not None
            cursor.execute("SHOW COLUMNS FROM timetable LIKE 'room'")
            has_room_text = cursor.fetchone() is not None

            if has_room_id and room_table:
                room_select = "COALESCE(r.room_number, r.room_name, '-') AS room"
                room_join = f"LEFT JOIN {room_table} r ON t.room_id = r.id"
            elif has_room_text:
                room_select = "COALESCE(t.room, '-') AS room"
                room_join = ""
            else:
                room_select = "'-' AS room"
                room_join = ""

            sql_timetable = f"""
                SELECT
                    t.id,
                    t.subject_name,
                    t.day_of_week,
                    TIME_FORMAT(t.start_time, '%H:%i') AS start_time,
                    TIME_FORMAT(t.end_time, '%H:%i') AS end_time,
                    {room_select},
                    u.name AS teacher_name,
                    d.department_name,
                    a.year_name
                FROM timetable t
                {room_join}
                LEFT JOIN users u ON t.teacher_id = u.id
                LEFT JOIN department d ON t.department_id = d.id
                LEFT JOIN academic_year a ON t.academic_year_id = a.id
                ORDER BY FIELD(
                    t.day_of_week,
                    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
                ), t.start_time
            """
            cursor.execute(sql_timetable)
            timetables = cursor.fetchall() or []

        except pymysql.MySQLError as e:
            print(f"Dashboard load error: {e}")
        finally:
            if cursor:
                cursor.close()
            conn.close()

    return render_template(
        'index.html',
        users=users_list,
        generations=generations_data,
        roles=roles,
        profile=my_profile,
        departments=departments,
        academic_years=academic_years,
        colleges=colleges_list,
        classes=classes_list,
        timetables=timetables
    )

# ==========================================
# API Routes សម្រាប់ CRUD (Admin)
# ==========================================
@app.route('/add_user', methods=['POST'])
@admin_required
def add_user():
    data = request.get_json() or {}
    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("SHOW COLUMNS FROM users LIKE 'created_by'")
        has_created_by_col = cursor.fetchone() is not None
        cursor.execute("SHOW COLUMNS FROM user_profiles LIKE 'date_of_birth'")
        has_date_of_birth_col = cursor.fetchone() is not None
        cursor.execute("SHOW COLUMNS FROM user_profiles LIKE 'dob'")
        has_dob_col = cursor.fetchone() is not None
        dob_column = 'date_of_birth' if has_date_of_birth_col else ('dob' if has_dob_col else None)

        # ១. បញ្ចូលទៅក្នុងតារាង users
        created_by_user_id = session.get('user_id')
        if has_created_by_col:
            sql_user = "INSERT INTO users (name, email, password, role, status, created_by) VALUES (%s, %s, %s, %s, %s, %s)"
            user_params = (
                data.get('name'),
                data.get('email'),
                '123456',
                data.get('role'),
                data.get('status', 'Active'),
                created_by_user_id
            )
        else:
            sql_user = "INSERT INTO users (name, email, password, role, status) VALUES (%s, %s, %s, %s, %s)"
            user_params = (
                data.get('name'),
                data.get('email'),
                '123456',
                data.get('role'),
                data.get('status', 'Active')
            )

        cursor.execute(sql_user, user_params)
        user_id = cursor.lastrowid

        # ២. Update ព័ត៌មានបន្ថែមក្នុង user_profiles (Trigger បង្កើត Row ឱ្យរួចហើយ)
        # រៀបចំទិន្នន័យតាម Role
        role = data.get('role')

        dob = _normalize_dob(data.get('dob'))

        dep_id = data.get('department')
        dep_id = dep_id if dep_id else None

        ay_id = data.get('academic_year_id') or data.get('year')
        ay_id = ay_id if ay_id else None

        class_id = data.get('class_id')
        class_id = class_id if class_id else None

        gen_id = data.get('generation_id')
        gen_id = gen_id if gen_id else None

        # Apply student-only relationship fields.
        if role != 'Student':
            gen_id = None
            ay_id = None
            class_id = None

        address = data.get('address')

        if dob_column:
            sql_profile = """
                UPDATE user_profiles SET
                    gender = %s, phone = %s, {dob_column} = %s, id_number = %s, address = %s,
                    department_id = %s, generation_id = %s,
                    academic_year_id = %s, class_id = %s
                WHERE user_id = %s
            """.format(dob_column=dob_column)
            profile_params = (
                data.get('gender'), data.get('phone'), dob, data.get('idNumber'),
                address, dep_id, gen_id, ay_id, class_id, user_id
            )
        else:
            sql_profile = """
                UPDATE user_profiles SET
                    gender = %s, phone = %s, id_number = %s, address = %s,
                    department_id = %s, generation_id = %s,
                    academic_year_id = %s, class_id = %s
                WHERE user_id = %s
            """
            profile_params = (
                data.get('gender'), data.get('phone'), data.get('idNumber'),
                address, dep_id, gen_id, ay_id, class_id, user_id
            )

        cursor.execute(sql_profile, profile_params)

        # ៣. ប្រសិនបើជា Teacher ត្រូវបញ្ចូលទៅក្នុងតារាង teachers ដែរ
        if role == 'Teacher':
            sql_teacher = "INSERT INTO teachers (user_id, teacher_code, department_id) VALUES (%s, %s, %s)"
            cursor.execute(sql_teacher, (user_id, data.get('idNumber'), dep_id))
        elif role == 'Student':
            sql_student = "INSERT INTO students (user_id, student_code, class_id) VALUES (%s, %s, %s)"
            cursor.execute(sql_student, (user_id, data.get('idNumber'), class_id))
        elif role == 'Admin':
            sql_admin = "INSERT INTO admins (user_id, position) VALUES (%s, %s)"
            cursor.execute(sql_admin, (user_id, 'Administrator'))

        conn.commit()
        return jsonify({'status': 'success', 'message': f'បន្ថែម {role} ជោគជ័យ!'})

    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()
    
@app.route('/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM users WHERE id = %s', (user_id,)) # លុបតាម ID
            conn.commit()
            return jsonify({'status': 'success', 'message': 'លុបជោគជ័យ!'})
        except Exception as e:
            conn.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500
    return jsonify({'status': 'error', 'message': 'Database Error'}), 500

@app.route('/update_user', methods=['POST'])
@app.route('/update_user/<int:user_id>', methods=['POST'])
@app.route('/update_stuents', methods=['POST'])
@app.route('/update_stuennt/<int:user_id>', methods=['POST'])
@admin_required
def update_user(user_id=None):
    data = request.get_json() or {}
    user_id = user_id or data.get('id')
    role = data.get('role')

    if not user_id:
        return jsonify({'status': 'error', 'message': 'Missing user id'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': 'មិនអាចភ្ជាប់ Database បានទេ'}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("SHOW COLUMNS FROM user_profiles LIKE 'date_of_birth'")
        has_date_of_birth_col = cursor.fetchone() is not None
        cursor.execute("SHOW COLUMNS FROM user_profiles LIKE 'dob'")
        has_dob_col = cursor.fetchone() is not None
        dob_column = 'date_of_birth' if has_date_of_birth_col else ('dob' if has_dob_col else None)

        # ១. Update ព័ត៌មានមូលដ្ឋានក្នុងតារាង users
        sql_user = "UPDATE users SET name=%s, email=%s, role=%s, status=%s WHERE id=%s"
        cursor.execute(sql_user, (data.get('name'), data.get('email'), role, data.get('status', 'Active'), user_id))

        # ២. កំណត់តម្លៃសម្រាប់ Profile ផ្អែកតាម Role
        is_student = (role == 'Student')
        is_teacher = (role == 'Teacher')

        dob = _normalize_dob(data.get('dob'))

        dep_id = data.get('department') if (is_student or is_teacher) else None
        dep_id = dep_id if dep_id else None

        gen_id = data.get('generation_id') if is_student else None
        gen_id = gen_id if gen_id else None

        ay_id = (data.get('academic_year_id') or data.get('year')) if is_student else None
        ay_id = ay_id if ay_id else None

        class_id = data.get('class_id') if is_student else None
        class_id = class_id if class_id else None

        # ៣. Update តារាង user_profiles
        if dob_column:
            sql_profile = """
                UPDATE user_profiles SET
                    gender=%s, phone=%s, {dob_column}=%s, id_number=%s, address=%s,
                    department_id=%s, generation_id=%s,
                    academic_year_id=%s, class_id=%s
                WHERE user_id=%s
            """.format(dob_column=dob_column)
            profile_params = (
                data.get('gender'), data.get('phone'), dob, data.get('idNumber'), data.get('address'),
                dep_id, gen_id, ay_id, class_id, user_id
            )
        else:
            sql_profile = """
                UPDATE user_profiles SET
                    gender=%s, phone=%s, id_number=%s, address=%s,
                    department_id=%s, generation_id=%s,
                    academic_year_id=%s, class_id=%s
                WHERE user_id=%s
            """
            profile_params = (
                data.get('gender'), data.get('phone'), data.get('idNumber'), data.get('address'),
                dep_id, gen_id, ay_id, class_id, user_id
            )

        cursor.execute(sql_profile, profile_params)

        # ៤. គ្រប់គ្រងទិន្នន័យក្នុងតារាង teachers/students/admins (ប្រសិនបើមានការប្តូរ Role)
        if is_teacher:
            cursor.execute("SELECT id FROM teachers WHERE user_id = %s", (user_id,))
            if cursor.fetchone():
                cursor.execute(
                    "UPDATE teachers SET teacher_code=%s, department_id=%s WHERE user_id=%s",
                    (data.get('idNumber'), dep_id, user_id)
                )
            else:
                cursor.execute(
                    "INSERT INTO teachers (user_id, teacher_code, department_id) VALUES (%s, %s, %s)",
                    (user_id, data.get('idNumber'), dep_id)
                )
        else:
            cursor.execute("DELETE FROM teachers WHERE user_id = %s", (user_id,))

        if is_student:
            cursor.execute("SELECT id FROM students WHERE user_id = %s", (user_id,))
            if cursor.fetchone():
                cursor.execute(
                    "UPDATE students SET student_code=%s, class_id=%s WHERE user_id=%s",
                    (data.get('idNumber'), class_id, user_id)
                )
            else:
                cursor.execute(
                    "INSERT INTO students (user_id, student_code, class_id) VALUES (%s, %s, %s)",
                    (user_id, data.get('idNumber'), class_id)
                )
        else:
            cursor.execute("DELETE FROM students WHERE user_id = %s", (user_id,))

        if role == 'Admin':
            cursor.execute("SELECT id FROM admins WHERE user_id = %s", (user_id,))
            if cursor.fetchone():
                cursor.execute(
                    "UPDATE admins SET position=%s WHERE user_id=%s",
                    ('Administrator', user_id)
                )
            else:
                cursor.execute(
                    "INSERT INTO admins (user_id, position) VALUES (%s, %s)",
                    (user_id, 'Administrator')
                )
        else:
            cursor.execute("DELETE FROM admins WHERE user_id = %s", (user_id,))

        conn.commit()
        return jsonify({'status': 'success', 'message': 'កែប្រែទិន្នន័យអ្នកប្រើប្រាស់ជោគជ័យ!'})

    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/admin/users', methods=['GET'])
@admin_required
def get_admin_users():
    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    cursor = None
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SHOW COLUMNS FROM user_profiles LIKE 'date_of_birth'")
        has_date_of_birth_col = cursor.fetchone() is not None
        cursor.execute("SHOW COLUMNS FROM user_profiles LIKE 'dob'")
        has_dob_col = cursor.fetchone() is not None
        dob_select = "p.date_of_birth AS date_of_birth" if has_date_of_birth_col else (
            "p.dob AS date_of_birth" if has_dob_col else "NULL AS date_of_birth"
        )
        sql = f"""
            SELECT
                u.id,
                u.name,
                u.email,
                u.role,
                u.status,
                u.created_at,
                u.created_by,
                p.id_number,
                p.phone,
                p.address,
                {dob_select},
                p.department_id,
                p.generation_id,
                p.academic_year_id,
                p.class_id,
                p.gender,
                d.college_id,
                d.department_name,
                ay.year_name AS academic_year_name,
                c.class_name,
                s.student_code,
                uc.name AS created_by_name
            FROM users u
            LEFT JOIN user_profiles p ON p.user_id = u.id
            LEFT JOIN department d ON d.id = p.department_id
            LEFT JOIN academic_year ay ON ay.id = p.academic_year_id
            LEFT JOIN classes c ON c.id = p.class_id
            LEFT JOIN students s ON s.user_id = u.id
            LEFT JOIN users uc ON uc.id = u.created_by
            ORDER BY u.id DESC
        """
        cursor.execute(sql)
        return jsonify({'status': 'success', 'data': cursor.fetchall() or []})
    except pymysql.MySQLError as err:
        return jsonify({'status': 'error', 'message': str(err)}), 500
    finally:
        if cursor:
            cursor.close()
        conn.close()


@app.route('/api/admin/student', methods=['GET'])
@admin_required
def get_admin_student():
    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    cursor = None
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SHOW COLUMNS FROM user_profiles LIKE 'date_of_birth'")
        has_date_of_birth_col = cursor.fetchone() is not None
        cursor.execute("SHOW COLUMNS FROM user_profiles LIKE 'dob'")
        has_dob_col = cursor.fetchone() is not None
        dob_select = "p.date_of_birth AS date_of_birth" if has_date_of_birth_col else (
            "p.dob AS date_of_birth" if has_dob_col else "NULL AS date_of_birth"
        )
        sql = f"""
            SELECT
                u.id,
                u.name,
                u.email,
                u.role,
                u.status,
                u.created_at,
                u.created_by,
                p.id_number,
                p.phone,
                p.address,
                {dob_select},
                p.department_id,
                p.generation_id,
                p.academic_year_id,
                p.class_id,
                p.gender,
                d.college_id,
                d.department_name,
                ay.year_name AS academic_year_name,
                c.class_name,
                s.student_code,
                uc.name AS created_by_name
            FROM users u
            LEFT JOIN user_profiles p ON p.user_id = u.id
            LEFT JOIN department d ON d.id = p.department_id
            LEFT JOIN academic_year ay ON ay.id = p.academic_year_id
            LEFT JOIN classes c ON c.id = p.class_id
            LEFT JOIN students s ON s.user_id = u.id
            LEFT JOIN users uc ON uc.id = u.created_by
            WHERE LOWER(u.role) = 'student'
            ORDER BY u.id DESC
        """
        cursor.execute(sql)
        return jsonify({'status': 'success', 'data': cursor.fetchall() or []})
    except pymysql.MySQLError as err:
        return jsonify({'status': 'error', 'message': str(err)}), 500
    finally:
        if cursor:
            cursor.close()
        conn.close()

@app.route('/statistics', methods=['GET'])
@admin_required
def statistics():
    
    from datetime import date, timedelta

    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    cursor = None
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        def detect_column(table_name, candidates):
            for col in candidates:
                cursor.execute(f"SHOW COLUMNS FROM {table_name} LIKE %s", (col,))
                if cursor.fetchone():
                    return col
            return None

        role_col = detect_column('users', ['role', 'user_type', 'type'])
        name_col = detect_column('users', ['name', 'full_name', 'username'])
        date_col = detect_column('attendance', ['attendance_date', 'date', 'taken_at', 'created_at'])

        dashboard = {
            'users': {'student': 0, 'teacher': 0, 'admin': 0},
            'today': {'present': 0, 'absent': 0, 'late': 0},
            'attendance_trend': {'labels': [], 'data': []},
            'class_stats': {'labels': [], 'data': []},
            'weekly_absent': [0, 0, 0, 0, 0, 0, 0],
            'top_students': [],
        }

        # 1) Users by role
        if role_col:
            cursor.execute(
                f"""
                SELECT
                    SUM(CASE WHEN LOWER({role_col})='student' THEN 1 ELSE 0 END) AS student,
                    SUM(CASE WHEN LOWER({role_col})='teacher' THEN 1 ELSE 0 END) AS teacher,
                    SUM(CASE WHEN LOWER({role_col})='admin' THEN 1 ELSE 0 END) AS admin
                FROM users
                """
            )
            row = cursor.fetchone() or {}
            dashboard['users'] = {
                'student': int(row.get('student') or 0),
                'teacher': int(row.get('teacher') or 0),
                'admin': int(row.get('admin') or 0),
            }

        # 2) Today attendance summary
        if date_col:
            cursor.execute(
                f"""
                SELECT
                    SUM(CASE WHEN LOWER(status)='present' THEN 1 ELSE 0 END) AS present,
                    SUM(CASE WHEN LOWER(status)='absent' THEN 1 ELSE 0 END) AS absent,
                    SUM(CASE WHEN LOWER(status)='late' THEN 1 ELSE 0 END) AS late
                FROM attendance
                WHERE DATE({date_col}) = CURDATE()
                """
            )
            row = cursor.fetchone() or {}
            dashboard['today'] = {
                'present': int(row.get('present') or 0),
                'absent': int(row.get('absent') or 0),
                'late': int(row.get('late') or 0),
            }

        # 3) Attendance trend (last 7 days, present count)
        if date_col:
            cursor.execute(
                f"""
                SELECT DATE({date_col}) AS d,
                       SUM(CASE WHEN LOWER(status)='present' THEN 1 ELSE 0 END) AS present_count
                FROM attendance
                WHERE DATE({date_col}) >= CURDATE() - INTERVAL 6 DAY
                GROUP BY DATE({date_col})
                ORDER BY DATE({date_col})
                """
            )
            trend_rows = cursor.fetchall() or []
            trend_map = {str(r['d']): int(r.get('present_count') or 0) for r in trend_rows}

            labels, data = [], []
            start = date.today() - timedelta(days=6)
            for i in range(7):
                d = start + timedelta(days=i)
                key = d.isoformat()
                labels.append(d.strftime('%b %d'))
                data.append(trend_map.get(key, 0))

            dashboard['attendance_trend'] = {'labels': labels, 'data': data}

        # 4) Students by class
        if role_col:
            cursor.execute(
                f"""
                SELECT
                    c.class_name,
                    SUM(CASE WHEN LOWER(u.{role_col})='student' THEN 1 ELSE 0 END) AS student_total
                FROM classes c
                LEFT JOIN user_profiles up ON up.class_id = c.id
                LEFT JOIN users u ON u.id = up.user_id
                GROUP BY c.id, c.class_name
                ORDER BY c.class_name
                """
            )
        else:
            cursor.execute(
                """
                SELECT
                    c.class_name,
                    COUNT(up.user_id) AS student_total
                FROM classes c
                LEFT JOIN user_profiles up ON up.class_id = c.id
                GROUP BY c.id, c.class_name
                ORDER BY c.class_name
                """
            )

        class_rows = cursor.fetchall() or []
        dashboard['class_stats'] = {
            'labels': [r.get('class_name') or '-' for r in class_rows],
            'data': [int(r.get('student_total') or 0) for r in class_rows],
        }

        # 5) Weekly absent (Mon..Sun)
        if date_col:
            cursor.execute(
                f"""
                SELECT DAYOFWEEK(DATE({date_col})) AS dow,
                       SUM(CASE WHEN LOWER(status)='absent' THEN 1 ELSE 0 END) AS absent_count
                FROM attendance
                WHERE DATE({date_col}) >= CURDATE() - INTERVAL 6 DAY
                GROUP BY DAYOFWEEK(DATE({date_col}))
                """
            )
            rows = cursor.fetchall() or []
            # MySQL: 1=Sun,2=Mon,...,7=Sat -> target index Mon..Sun => [0..6]
            dow_to_index = {2: 0, 3: 1, 4: 2, 5: 3, 6: 4, 7: 5, 1: 6}
            weekly = [0, 0, 0, 0, 0, 0, 0]
            for r in rows:
                idx = dow_to_index.get(int(r.get('dow') or 0))
                if idx is not None:
                    weekly[idx] = int(r.get('absent_count') or 0)
            dashboard['weekly_absent'] = weekly

        # 6) Top 4 attendants
        if date_col and name_col:
            cursor.execute(
                f"""
                SELECT
                    u.id,
                    u.{name_col} AS name,
                    SUM(CASE WHEN LOWER(a.status)='present' THEN 1 ELSE 0 END) AS present_days,
                    COUNT(a.id) AS total_days
                FROM attendance a
                JOIN users u ON u.id = a.student_id
                GROUP BY u.id, u.{name_col}
                HAVING total_days > 0
                ORDER BY present_days DESC, total_days DESC
                LIMIT 4
                """
            )
            top_rows = cursor.fetchall() or []
            top_students = []
            for r in top_rows:
                present_days = int(r.get('present_days') or 0)
                total_days = int(r.get('total_days') or 0)
                pct = (present_days / total_days * 100) if total_days else 0
                top_students.append({
                    'name': r.get('name') or 'Unknown',
                    'days': f"{present_days} days",
                    'percentage': f"{pct:.0f}%",
                })
            dashboard['top_students'] = top_students

        return jsonify({'status': 'success', 'data': dashboard})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        conn.close()

@app.route('/profile', methods=['GET'])
@login_required
def profile():
    user_id = session.get('user_id') # ទាញយក ID របស់ម្ចាស់គណនីដែលកំពុង Login
    conn = get_db_connection()
    user_profile = None
    
    if conn:
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            # Query ទាញយកព័ត៌មានលម្អិត រួមទាំង Department និង Academic Year
            sql = """
                SELECT u.name, u.email, u.role, u.status, 
                       p.id_number, p.phone, p.address, p.department_id, p.academic_year_id,
                       d.department_name as department, 
                       a.year_name as academic_year 
                FROM users u 
                LEFT JOIN user_profiles p ON u.id = p.user_id
                LEFT JOIN department d ON d.id = p.department_id
                LEFT JOIN academic_year a ON p.academic_year_id = a.id
                WHERE u.id = %s
            """
            cursor.execute(sql, (user_id,))
            user_profile = cursor.fetchone()
        except Exception as e:
            # ករណីមាន Error បើ JS ជាអ្នកហៅ បញ្ជូនសារជា JSON
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'status': 'error', 'message': str(e)}), 500
            flash('មិនអាចទាញយកព័ត៌មានបានទេ: ' + str(e), 'error')
        finally:
            cursor.close()
            conn.close()
    
    # 🌟 ត្រួតពិនិត្យប្រភេទ Request
    # ១. បើហៅតាមរយៈ fetchProfile() (JS) ឱ្យបញ្ជូនជា JSON
    if request.headers.get('Accept') == 'application/json':
        if user_profile:
            return jsonify(user_profile)
        return jsonify({'status': 'error', 'message': 'រកមិនឃើញទិន្នន័យ'}), 404
    return jsonify({'status': 'error', 'message': 'Database Error'}), 500

@app.route('/update_my_profile', methods=['POST'])
@login_required # តម្រូវឱ្យ Login សិនទើបអាចកែប្រែបាន
def update_my_profile():
    # ១. ទទួលយកទិន្នន័យ JSON ពី JavaScript
    data = request.get_json()
    user_id = session.get('user_id')
    
    # ការពារសុវត្ថិភាព បើគ្មានសិទ្ធិ ឬមិនទាន់ Login
    if not user_id:
        return jsonify({'status': 'error', 'message': 'សូមចូលគណនីម្តងទៀត (Unauthorized)'}), 401
        
    # ទាញយកតម្លៃពី JSON (ប្រើ .get() ដើម្បីកុំឱ្យ Error បើវាទទេ)
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    address = data.get('address')
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # ២. កែប្រែទិន្នន័យក្នុងតារាង users (ឈ្មោះ និងអ៊ីមែល)
            sql_users = "UPDATE users SET name=%s, email=%s WHERE id=%s"
            cursor.execute(sql_users, (name, email, user_id))
            
            # ៣. ពិនិត្យមើលថាតើគាត់មាន Profile ក្នុងតារាង user_profiles ហើយឬនៅ?
            cursor.execute("SELECT id FROM user_profiles WHERE user_id = %s", (user_id,))
            profile_exists = cursor.fetchone()
            
            if profile_exists:
                # បើមានហើយ -> ធ្វើការ Update
                sql_update_profile = "UPDATE user_profiles SET phone=%s, address=%s WHERE user_id=%s"
                cursor.execute(sql_update_profile, (phone, address, user_id))
            else:
                # បើមិនទាន់មាន -> បង្កើតថ្មី (Insert)
                sql_insert_profile = "INSERT INTO user_profiles (user_id, phone, address) VALUES (%s, %s, %s)"
                cursor.execute(sql_insert_profile, (user_id, phone, address))
            
            conn.commit()
            
            # ៤. Update ឈ្មោះក្នុង Session ដើម្បីឱ្យ Header ដូរឈ្មោះតាម (បើលោកអ្នកមានបង្ហាញឈ្មោះលើ Header)
            if 'name' in session:
                session['name'] = name
                
            return jsonify({'status': 'success', 'message': 'កែប្រែប្រវត្តិរូបបានជោគជ័យ!'})
            
        except pymysql.err.IntegrityError as e:
            conn.rollback()
            # ករណីអ៊ីមែលជាន់គ្នាជាមួយអ្នកដទៃ
            if 'Duplicate entry' in str(e) and 'email' in str(e):
                return jsonify({'status': 'error', 'message': 'អ៊ីមែលនេះមានអ្នកប្រើប្រាស់រួចហើយ!'}), 400
            return jsonify({'status': 'error', 'message': 'កំហុសទិន្នន័យ: ' + str(e)}), 500
            
        except Exception as e:
            conn.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500
            
        finally:
            cursor.close()
            conn.close()
            
    return jsonify({'status': 'error', 'message': 'Database Error'}), 500

@app.route('/chat', methods=['POST'])
@login_required # លុបបន្ទាត់នេះចេញបើចង់ឱ្យអ្នកអត់ទាន់ Login ក៏ឆាតបាន
def chat_api():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'error': 'គ្មានសារត្រូវបានបញ្ជូនមកទេ'}), 400

    # 🌟 ទីតាំងសម្រាប់សរសេរ Logic របស់ Chatbot 🌟
    # អ្នកអាចសរសេរលក្ខខណ្ឌធម្មតា (If/Else) ឬភ្ជាប់ជាមួយ AI Model នៅទីនេះ
    
    user_message_lower = user_message.lower()
    bot_reply = ""

    # ឧទាហរណ៍នៃ Rule-based Q&A សាមញ្ញ៖
    if "សួស្តី" in user_message_lower or "hello" in user_message_lower:
        bot_reply = "សួស្តី! ខ្ញុំគឺ UniBot។ តើថ្ងៃនេះមានអ្វីឱ្យខ្ញុំជួយពាក់ព័ន្ធនឹងប្រព័ន្ធសាលារៀនដែរឬទេ?"
    elif "តម្លៃសិក្សា" in user_message_lower or "fee" in user_message_lower:
        bot_reply = "សម្រាប់ព័ត៌មានលម្អិតអំពីតម្លៃសិក្សា សូមចូលទៅកាន់ទំព័រទម្រង់បង់ប្រាក់ ឬទាក់ទងទៅផ្នែកគណនេយ្យ។"
    else:
        # កន្លែងនេះអ្នកអាចបញ្ជូន user_message ទៅកាន់ Gemini API ឬ NLP Model របស់អ្នក
        bot_reply = f"ខ្ញុំទទួលបានសំណួររបស់អ្នកទាក់ទងនឹង: '{user_message}'។ ដោយសារខ្ញុំកំពុងស្ថិតក្នុងការអភិវឌ្ឍ ខ្ញុំសុំកត់ត្រាសំណួរនេះសិន។"

    return jsonify({
        'reply': bot_reply,
        'status': 'success'
    })
@app.route('/contact_support')
def contact_support():
    # បង្ហាញទំព័រ Contact IT Support ដែលយើងទើបបង្កើត
    
    return render_template('Contact_IT_Support.html')
@app.route('/api/submit_ticket', methods=['POST'])
@login_required
def submit_ticket():
    data = request.get_json()
    user_id = session.get('user_id')
    
    # ទាញយកទិន្នន័យពី JSON
    subject = data.get('subject')
    category = data.get('category')
    priority = data.get('priority')
    description = data.get('description')
    
    # ផ្ទៀងផ្ទាត់ទិន្នន័យ (Validation)
    if not subject or not description:
        return jsonify({'status': 'error', 'message': 'សូមបញ្ចូលចំណងជើង និងការពិពណ៌នាឱ្យបានគ្រប់គ្រាន់!'}), 400
        
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # បញ្ចូលទិន្នន័យទៅក្នុងតារាង support_tickets
            sql = """
                INSERT INTO support_tickets (user_id, subject, category, priority, description) 
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (user_id, subject, category, priority, description))
            conn.commit()
            
            return jsonify({
                'status': 'success', 
                'message': 'សំណើរបស់អ្នកត្រូវបានបញ្ជូនជោគជ័យ! ក្រុមការងារនឹងពិនិត្យមើលឆាប់ៗនេះ។'
            })
            
        except Exception as e:
            conn.rollback()
            return jsonify({'status': 'error', 'message': f'មានបញ្ហាក្នុងការរក្សាទុកទិន្នន័យ៖ {str(e)}'}), 500
            
        finally:
            cursor.close()
            conn.close()
            
    return jsonify({'status': 'error', 'message': 'មិនអាចភ្ជាប់ទៅកាន់ Database បានទេ'}), 500

# ១. Route សម្រាប់ទាញទិន្នន័យមកបង្ហាញក្នុងតារាង
@app.route('/manageDepartment', methods=['GET'])
def get_department_view():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # ✅ បន្ថែម d.id AS department_id ទៅក្នុង SELECT
            sql = """SELECT
                d.id AS department_id,
                c.id AS college_id,
                c.college_name,
                d.department_name
            FROM colleges c
            JOIN department d 
            ON c.id = d.college_id
            ORDER BY c.college_name, d.department_name"""
            
            cursor.execute(sql)
            users = cursor.fetchall()
            
            # រក្សាទុក key 'users' ដដែល ដើម្បីកុំឱ្យប៉ះពាល់ដល់ JavaScript របស់លោកអ្នក
            return jsonify({'status': 'success', 'users': users})
            
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
        finally:
            cursor.close()
            conn.close()
    return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

# ២. Route សម្រាប់រក្សាទុកដេប៉ាតឺម៉ង់ថ្មី
@app.route('/add_department', methods=['POST'])
def add_department():
    data = request.get_json()
    college_id = data.get('college_id')
    name = data.get('name')

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # បញ្ចូលទិន្នន័យទៅក្នុងតារាង department (ឬ departments តាមឈ្មោះពិតរបស់អ្នក)
            sql = "INSERT INTO department (department_name, college_id) VALUES (%s, %s)"
            cursor.execute(sql, (name, college_id))
            conn.commit()
            return jsonify({'status': 'success', 'message': 'បន្ថែមដេប៉ាតឺម៉ង់ជោគជ័យ!'})
        except Exception as e:
            conn.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500
        finally:
            cursor.close()
            conn.close()
    return jsonify({'status': 'error', 'message': 'Database error'}), 500

@app.route('/delete_department/<int:id>', methods=['POST'])
def delete_department(id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # លុបទិន្នន័យពីតារាង department តាម id
            sql = "DELETE FROM department WHERE id = %s"
            cursor.execute(sql, (id,))
            conn.commit()
            
            # ឆែកមើលថាពិតជាមានទិន្នន័យត្រូវបានលុបមែនឬទេ
            if cursor.rowcount == 0:
                return jsonify({'status': 'error', 'message': 'រកមិនឃើញដេប៉ាតឺម៉ង់នេះទេ!'}), 404
                
            return jsonify({'status': 'success', 'message': 'លុបដេប៉ាតឺម៉ង់បានជោគជ័យ!'})
        except Exception as e:
            conn.rollback()
            # ប្រសិនបើជាប់ Foreign Key (មានសិស្សកំពុងរៀន) វានឹងលោត Error
            if "foreign key constraint fails" in str(e).lower():
                 return jsonify({'status': 'error', 'message': 'មិនអាចលុបបានទេ ព្រោះមានទិន្នន័យសិស្ស ឬមុខវិជ្ជាកំពុងជាប់ទាក់ទងនឹងដេប៉ាតឺម៉ង់នេះ!'}), 400
            return jsonify({'status': 'error', 'message': f'មានកំហុស៖ {str(e)}'}), 500
        finally:
            cursor.close()
            conn.close()
            
    return jsonify({'status': 'error', 'message': 'មិនអាចភ្ជាប់ទៅកាន់ Database បានទេ'}), 500


# ==========================================
# ៣. កែប្រែដេប៉ាតឺម៉ង់ (Update)
# ==========================================
@app.route('/update_department', methods=['POST'])
def update_department():
    data = request.get_json()
    dept_id = data.get('id')
    college_id = data.get('college_id')
    name = data.get('name')

    if not dept_id or not college_id or not name:
        return jsonify({'status': 'error', 'message': 'ទិន្នន័យមិនពេញលេញ សូមព្យាយាមម្តងទៀត!'}), 400

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            sql = "UPDATE department SET department_name = %s, college_id = %s WHERE id = %s"
            cursor.execute(sql, (name, college_id, dept_id))
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({'status': 'error', 'message': 'រកមិនឃើញដេប៉ាតឺម៉ង់នេះក្នុងប្រព័ន្ធទេ!'}), 404
                
            return jsonify({'status': 'success', 'message': 'កែប្រែដេប៉ាតឺម៉ង់បានជោគជ័យ!'})
        except Exception as e:
            conn.rollback()
            return jsonify({'status': 'error', 'message': f'មានកំហុស៖ {str(e)}'}), 500
        finally:
            cursor.close()
            conn.close()
    return jsonify({'status': 'error', 'message': 'មិនអាចភ្ជាប់ទៅកាន់ Database បានទេ'}), 500


# ==========================================
# ទាញយកបញ្ជីមុខវិជ្ជាមកបង្ហាញក្នុងតារាង
# ==========================================
@app.route('/manageSubjects', methods=['GET'])
def get_subjects_view():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            # ប្រើ JOIN ដើម្បីទាញយកឈ្មោះដេប៉ាតឺម៉ង់ និងឆ្នាំសិក្សា
            sql = """SELECT
                s.id,
                s.subject_name,
                s.credits,
                s.semester,
                s.department_id,
                d.department_name,
                s.year_id,
                ay.year_name
            FROM subjects s
            JOIN department d ON s.department_id = d.id
            JOIN academic_year ay ON s.year_id = ay.id
            ORDER BY d.department_name, ay.year_name, s.semester, s.subject_name"""
            
            cursor.execute(sql)
            subjects = cursor.fetchall()
            
            return jsonify({'status': 'success', 'subjects': subjects})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
        finally:
            cursor.close()
            conn.close()
            
    return jsonify({'status': 'error', 'message': 'មិនអាចភ្ជាប់ទៅកាន់ Database បានទេ'}), 500

@app.route('/add_subject', methods=['POST'])
def add_subject():
    data = request.get_json()
    
    # ទី១៖ ប្តូរពី 'name' មក 'subject_name' ឱ្យត្រូវនឹង JS JSON Payload
    name = data.get('subject_name') 
    credits = data.get('credits')
    semester = data.get('semester')
    department_id = data.get('department_id')
    year_id = data.get('year_id')

    # ទី២៖ គួរមានការត្រួតពិនិត្យ (Validation) មុននឹងបញ្ចូលទៅ Database
    if not name or not department_id or not year_id or not semester:
        return jsonify({'status': 'error', 'message': 'សូមបំពេញព័ត៌មានឱ្យបានគ្រប់ជ្រុងជ្រោយ!'}), 400

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            sql = "INSERT INTO subjects (subject_name, credits, semester, department_id, year_id) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (name, credits, semester, department_id, year_id))
            conn.commit()
            return jsonify({'status': 'success', 'message': 'បន្ថែមមុខវិជ្ជាជោគជ័យ!'})
        except Exception as e:
            conn.rollback()
            error_msg = str(e).lower()
            
            # ទី៣៖ ចាប់ Error ករណីបញ្ចូលទិន្នន័យជាន់គ្នា (UNIQUE constraint ដែលយើងបានបង្កើត)
            if 'duplicate entry' in error_msg:
                 return jsonify({'status': 'error', 'message': 'មុខវិជ្ជានេះមានរួចហើយនៅក្នុងដេប៉ាតឺម៉ង់ និងឆមាសនេះ!'}), 400
                 
            return jsonify({'status': 'error', 'message': f'មានកំហុស៖ {str(e)}'}), 500
        finally:
            cursor.close()
            conn.close()
            
    return jsonify({'status': 'error', 'message': 'មិនអាចភ្ជាប់ទៅកាន់ Database បានទេ'}), 500

@app.route('/delete_subject/<int:id>', methods=['POST'])
def delete_subject(id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            sql = "DELETE FROM subjects WHERE id = %s"
            cursor.execute(sql, (id,))
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({'status': 'error', 'message': 'រកមិនឃើញមុខវិជ្ជានេះទេ!'}), 404
                
            return jsonify({'status': 'success', 'message': 'លុបមុខវិជ្ជាបានជោគជ័យ!'})
        except Exception as e:
            conn.rollback()
            # ប្រសិនបើជាប់ Foreign Key (មានកាលវិភាគ ឬសិស្សកំពុងរៀន) វានឹងលោត Error
            if "foreign key constraint fails" in str(e).lower():
                return jsonify({'status': 'error', 'message': 'មិនអាចលុបបានទេ ព្រោះមានទិន្នន័យកាលវិភាគ ឬសិស្សកំពុងជាប់ទាក់ទងនឹងមុខវិជ្ជានេះ!'}), 400
            return jsonify({'status': 'error', 'message': f'មានកំហុស៖ {str(e)}'}), 500
        finally:
            cursor.close()
            conn.close()
            
    return jsonify({'status': 'error', 'message': 'មិនអាចភ្ជាប់ទៅកាន់ Database បានទេ'}), 500
@app.route('/update_subject', methods=['POST'])
def update_subject():
    data = request.get_json()
    
    # ចាប់យក ID ដើម្បីដឹងថាត្រូវ Update ទិន្នន័យមួយណា
    subject_id = data.get('id')
    # ចាប់យកឈ្មោះតាមរយៈ Key 'name' ឱ្យស៊ីគ្នានឹង JS payload ដែលយើងបានសរសេរ
    name = data.get('name') 
    credits = data.get('credits')
    semester = data.get('semester')
    department_id = data.get('department_id')
    year_id = data.get('year_id')

    # Validation
    if not subject_id or not name or not department_id or not year_id or not semester:
        return jsonify({'status': 'error', 'message': 'សូមបំពេញព័ត៌មានឱ្យបានគ្រប់ជ្រុងជ្រោយ!'}), 400

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            sql = """
                UPDATE subjects 
                SET subject_name = %s, credits = %s, semester = %s, department_id = %s, year_id = %s
                WHERE id = %s
            """
            cursor.execute(sql, (name, credits, semester, department_id, year_id, subject_id))
            conn.commit()
            
            # ឆែកមើលថាពិតជាមានទិន្នន័យត្រូវបាន Update មែនឬទេ
            if cursor.rowcount == 0:
                return jsonify({'status': 'error', 'message': 'រកមិនឃើញមុខវិជ្ជានេះនៅក្នុងប្រព័ន្ធទេ!'}), 404
                
            return jsonify({'status': 'success', 'message': 'កែប្រែមុខវិជ្ជាបានជោគជ័យ!'})
        except Exception as e:
            conn.rollback()
            # ការពារការកែប្រែឈ្មោះជាន់គ្នា ក្នុងដេប៉ាតឺម៉ង់ និងឆមាសតែមួយ
            if 'duplicate entry' in str(e).lower():
                 return jsonify({'status': 'error', 'message': 'មុខវិជ្ជានេះមានរួចហើយនៅក្នុងប្រព័ន្ធ!'}), 400
            return jsonify({'status': 'error', 'message': f'មានកំហុស៖ {str(e)}'}), 500
        finally:
            cursor.close()
            conn.close()
            
    return jsonify({'status': 'error', 'message': 'មិនអាចភ្ជាប់ទៅកាន់ Database បានទេ'}), 500



# ==========================================
# ១. ទាញយកបញ្ជីថ្នាក់រៀន
# ==========================================
@app.route('/manageClasses', methods=['GET'])
def get_classes_view():
    conn = get_db_connection()
    if conn:
        cursor = None
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            cursor.execute(
                "SHOW COLUMNS FROM classes LIKE 'room_id'"
            )
            has_room_id = cursor.fetchone() is not None

            cursor.execute(
                "SHOW COLUMNS FROM classes LIKE 'room_name'"
            )
            has_room_name = cursor.fetchone() is not None

            cursor.execute(
                "SHOW COLUMNS FROM classes LIKE "
                "'academic_year_id'"
            )
            has_academic_year_id = (
                cursor.fetchone() is not None
            )

            cursor.execute("SHOW TABLES LIKE 'rooms'")
            has_rooms = cursor.fetchone() is not None
            room_table = 'rooms' if has_rooms else 'room'

            cursor.execute("SHOW TABLES LIKE 'buildings'")
            has_buildings = cursor.fetchone() is not None
            has_room_building_id = False
            if has_buildings:
                cursor.execute(
                    f"SHOW COLUMNS FROM {room_table} "
                    "LIKE 'building_id'"
                )
                has_room_building_id = (
                    cursor.fetchone() is not None
                )

            if has_academic_year_id:
                year_select = "c.academic_year_id, ay.year_name"
                year_join = (
                    "LEFT JOIN academic_year ay "
                    "ON c.academic_year_id = ay.id"
                )
                year_group = (
                    ", c.academic_year_id, "
                    "ay.year_name"
                )
            else:
                year_select = "NULL AS academic_year_id, NULL AS year_name"
                year_join = ""
                year_group = ""

            if has_room_id:
                if has_buildings and has_room_building_id:
                    room_select = (
                        "c.room_id, "
                        "r.room_number, "
                        "r.room_name, "
                        "b.id AS building_id, "
                        "b.building_name"
                    )
                    room_join = (
                        f"LEFT JOIN {room_table} r "
                        "ON c.room_id = r.id "
                        "LEFT JOIN buildings b "
                        "ON r.building_id = b.id"
                    )
                    room_group = (
                        ", c.room_id, "
                        "r.room_number, "
                        "r.room_name, "
                        "b.id, "
                        "b.building_name"
                    )
                else:
                    room_select = (
                        "c.room_id, "
                        "r.room_number, "
                        "r.room_name, "
                        "NULL AS building_id, "
                        "NULL AS building_name"
                    )
                    room_join = (
                        f"LEFT JOIN {room_table} r "
                        "ON c.room_id = r.id"
                    )
                    room_group = (
                        ", c.room_id, "
                        "r.room_number, "
                        "r.room_name"
                    )
            elif has_room_name:
                room_select = (
                    "NULL AS room_id, "
                    "c.room_name AS room_number, "
                    "c.room_name, "
                    "NULL AS building_id, "
                    "NULL AS building_name"
                )
                room_join = ""
                room_group = ", c.room_name"
            else:
                room_select = (
                    "NULL AS room_id, "
                    "NULL AS room_number, "
                    "NULL AS room_name, "
                    "NULL AS building_id, "
                    "NULL AS building_name"
                )
                room_join = ""
                room_group = ""

            if has_academic_year_id:
                class_order = (
                    "c.department_id, c.academic_year_id, "
                    "FIELD(c.session_type, 'M', 'A', 'E', 'SLS'), c.class_name"
                )
            else:
                class_order = (
                    "c.department_id, "
                    "FIELD(c.session_type, 'M', 'A', 'E', 'SLS'), c.class_name"
                )

            sql = f"""
                SELECT
                    c.id,
                    c.class_name,
                    c.session_type,
                    c.department_id,
                    {year_select},
                    {room_select},
                    d.department_name,
                    COUNT(up.user_id) AS student_count
                FROM classes c
                LEFT JOIN department d
                    ON c.department_id = d.id
                {year_join}
                {room_join}
                LEFT JOIN user_profiles up
                    ON c.id = up.class_id
                GROUP BY
                    c.id,
                    c.class_name,
                    c.session_type,
                    c.department_id,
                    d.department_name
                    {year_group}
                    {room_group}
                ORDER BY {class_order}
            """
            cursor.execute(sql)
            classes = cursor.fetchall()
            return jsonify(
                {
                    'status': 'success',
                    'classes': classes
                }
            )
        except Exception as e:
            return jsonify(
                {
                    'status': 'error',
                    'message': str(e)
                }
            ), 500
        finally:
            if cursor:
                cursor.close()
            conn.close()
    return jsonify(
        {
            'status': 'error',
            'message': 'មិនអាចភ្ជាប់ Database បានទេ'
        }
    ), 500


@app.route('/add_class', methods=['POST'])
def add_class():
    """
    បន្ថែមថ្នាក់រៀនថ្មី
    ទៅក្នុងតារាង classes។
    """
    payload = _class_payload(
        request.get_json(silent=True) or {}
    )
    error_msg = _validate_class_payload(payload)
    if error_msg:
        return jsonify(
            {
                'status': 'error',
                'message': error_msg
            }
        ), 400

    conn = get_db_connection()
    if not conn:
        return jsonify(
            {
                'status': 'error',
                'message': 'មិនអាចភ្ជាប់ Database បានទេ'
            }
        ), 500

    cursor = None
    try:
        cursor = conn.cursor()
        schema = _get_class_schema(cursor)
        sql, params = _build_class_insert_sql(
            cursor,
            payload,
            schema
        )
        cursor.execute(sql, params)
        conn.commit()
        return jsonify(
            {
                'status': 'success',
                'message': 'បន្ថែមថ្នាក់រៀនជោគជ័យ!',
            }
        )

    except pymysql.err.IntegrityError as err:
        conn.rollback()
        return _class_integrity_response(err)

    except pymysql.MySQLError as err:
        conn.rollback()
        return jsonify(
            {
                'status': 'error',
                'message': str(err),
            }
        ), 500

    finally:
        if cursor:
            cursor.close()
        conn.close()


@app.route('/update_class', methods=['POST'])
def update_class():
    """
    កែប្រែថ្នាក់រៀន
    និងឆ្នាំសិក្សា។
    """
    payload = _class_payload(
        request.get_json(silent=True) or {}
    )
    error_msg = _validate_class_payload(
        payload,
        require_id=True
    )
    if error_msg:
        return jsonify(
            {
                'status': 'error',
                'message': error_msg
            }
        ), 400

    conn = get_db_connection()
    if not conn:
        return jsonify(
            {
                'status': 'error',
                'message': 'មិនអាចភ្ជាប់ Database បានទេ'
            }
        ), 500

    cursor = None
    try:
        cursor = conn.cursor()
        schema = _get_class_schema(cursor)
        sql, params = _build_class_update_sql(
            cursor,
            payload,
            schema
        )
        cursor.execute(sql, params)
        conn.commit()
        return jsonify(
            {
                'status': 'success',
                'message': 'កែប្រែថ្នាក់រៀនជោគជ័យ!'
            }
        )

    except pymysql.err.IntegrityError as err:
        conn.rollback()
        return _class_integrity_response(
            err,
            include_fk=True
        )

    except pymysql.MySQLError as err:
        conn.rollback()
        return jsonify(
            {
                'status': 'error',
                'message': str(err)
            }
        ), 500

    finally:
        if cursor:
            cursor.close()
        conn.close()

@app.route('/delete_class/<int:id>', methods=['POST'])
def delete_class(id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            sql = "DELETE FROM classes WHERE id = %s"
            cursor.execute(sql, (id,))
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({'status': 'error', 'message': 'រកមិនឃើញថ្នាក់រៀននេះទេ!'}), 404
                
            return jsonify({'status': 'success', 'message': 'លុបថ្នាក់រៀនបានជោគជ័យ!'})
        except Exception as e:
            conn.rollback()
            if "foreign key constraint fails" in str(e).lower():
                return jsonify({'status': 'error', 'message': 'មិនអាចលុបបានទេ ព្រោះមានសិស្សកំពុងជាប់ទាក់ទងនឹងថ្នាក់រៀននេះ!'}), 400
            return jsonify({'status': 'error', 'message': str(e)}), 500
        finally:
            cursor.close()
            conn.close()
    return jsonify({'status': 'error', 'message': 'មិនអាចភ្ជាប់ Database បានទេ'}), 500

@app.route('/manageAttendance', methods=['GET'])
def get_attendance_view():
    """
    ទាញយកបញ្ជីវត្តមានសិស្សសម្រាប់ផ្ទាំង Admin Attendance។
    បញ្ជូន JSON ដែលមាន key/field ស៊ីគ្នាជាមួយ Frontend។
    """
    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    cursor = None
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Resolve the actual date column name to avoid SQL errors across schema versions.
        date_col = None
        for candidate in ('attendance_date', 'date', 'taken_at', 'created_at'):
            cursor.execute(f"SHOW COLUMNS FROM attendance LIKE '{candidate}'")
            if cursor.fetchone() is not None:
                date_col = candidate
                break

        date_select = f"a.{date_col}" if date_col else "NULL"
        order_by = f"a.{date_col} DESC, a.id DESC" if date_col else "a.id DESC"

        sql = f"""
            SELECT
                a.id,
                a.student_id,
                a.subject_id,
                {date_select} AS attendance_date,
                a.status,
                a.remarks,
                s.name AS student_name,
                COALESCE(c.class_name, '-') AS class_name,
                sub.subject_name,
                '-' AS teacher_name
            FROM attendance a
            JOIN users s ON a.student_id = s.id
            JOIN subjects sub ON a.subject_id = sub.id
            LEFT JOIN user_profiles up ON up.user_id = s.id
            LEFT JOIN classes c ON c.id = up.class_id
            ORDER BY {order_by}
        """
        cursor.execute(sql)
        attendance_records = cursor.fetchall()
        return jsonify({'status': 'success', 'attendance': attendance_records})

    except pymysql.MySQLError as err:
        return jsonify({'status': 'error', 'message': str(err)}), 500

    finally:
        if cursor:
            cursor.close()
        conn.close()

@app.route('/api/admin/update_attendance', methods=['POST'])
def update_attendance_admin():
    data = request.get_json(silent=True) or {}
    att_id = data.get('id')
    status = data.get('status')
    remarks = data.get('remarks', '')

    if not att_id or not status:
        return jsonify({'status': 'error', 'message': 'ទិន្នន័យមិនគ្រប់គ្រាន់!'}), 400

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # ធ្វើការ Update តែ status និង remarks ដោយផ្អែកលើ Primary Key (id)
            sql = "UPDATE attendance SET status = %s, remarks = %s WHERE id = %s"
            cursor.execute(sql, (status, remarks, att_id))
            conn.commit()

            if cursor.rowcount == 0:
                return jsonify({'status': 'error', 'message': 'រកមិនឃើញទិន្នន័យវត្តមាននេះទេ!'}), 404

            return jsonify({'status': 'success', 'message': 'កែប្រែវត្តមានបានជោគជ័យ!'})
        except Exception as e:
            conn.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500
        finally:
            cursor.close()
            conn.close()

    return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500



@app.route('/api/reports/get_all_data', methods=['GET'])
@admin_required
def get_all_report_data():
    report_type = (request.args.get('type') or '').strip().lower()
    allowed_types = {
        'students', 'teachers', 'classes', 'subjects',
        'teachers_with_subjects', 'classes_with_students',
        'students_by_class', 'attendance_summary', 'attendance'
    }

    if report_type not in allowed_types:
        return jsonify({'status': 'error', 'message': 'ប្រភេទរបាយការណ៍មិនត្រឹមត្រូវ'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    cursor = None
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        sql = _get_report_sql(report_type, cursor)

        if not sql:
            return jsonify({'status': 'error', 'message': 'ប្រភេទរបាយការណ៍មិនត្រឹមត្រូវ'}), 400

        cursor.execute(sql)
        return jsonify({'status': 'success', 'data': cursor.fetchall()})

    except pymysql.MySQLError as err:
        return jsonify({'status': 'error', 'message': str(err)}), 500

    finally:
        if cursor:
            cursor.close()
        conn.close()


@app.route('/api/reports/summary', methods=['GET'])
@admin_required
def get_report_summary():
    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    cursor = None
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("SELECT COUNT(*) AS total FROM users WHERE LOWER(role) = 'student'")
        student_count = (cursor.fetchone() or {}).get('total', 0)

        cursor.execute("SELECT COUNT(*) AS total FROM users WHERE LOWER(role) = 'teacher'")
        teacher_count = (cursor.fetchone() or {}).get('total', 0)

        cursor.execute("SELECT COUNT(*) AS total FROM classes")
        class_count = (cursor.fetchone() or {}).get('total', 0)

        return jsonify({
            'status': 'success',
            'data': {
                'students': student_count,
                'teachers': teacher_count,
                'classes': class_count
            }
        })
    except pymysql.MySQLError as err:
        return jsonify({'status': 'error', 'message': str(err)}), 500
    finally:
        if cursor:
            cursor.close()
        conn.close()


@app.route('/api/admin/schedules', methods=['GET'])
@admin_required
def get_admin_schedules():
    """
    Return schedules for admin table/grid view.
    Supports schema variants for room, teacher,
    class, department, and academic year fields.
    """
    conn = get_db_connection()
    if not conn:
        return jsonify(
            {
                'status': 'error',
                'message': 'មិនអាចភ្ជាប់ Database បានទេ',
            }
        ), 500

    cursor = None
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("SHOW TABLES LIKE 'rooms'")
        has_rooms = cursor.fetchone() is not None

        cursor.execute("SHOW TABLES LIKE 'room'")
        has_room = cursor.fetchone() is not None

        cursor.execute("SHOW TABLES LIKE 'buildings'")
        has_buildings = cursor.fetchone() is not None

        cursor.execute("SHOW TABLES LIKE 'classes'")
        has_classes = cursor.fetchone() is not None

        room_table = (
            'rooms'
            if has_rooms
            else ('room' if has_room else None)
        )

        cursor.execute("SHOW COLUMNS FROM timetable LIKE 'room_id'")
        has_room_id = cursor.fetchone() is not None

        cursor.execute("SHOW COLUMNS FROM timetable LIKE 'room'")
        has_room_text = cursor.fetchone() is not None

        cursor.execute("SHOW COLUMNS FROM timetable LIKE 'teacher_id'")
        has_teacher_id = cursor.fetchone() is not None

        cursor.execute("SHOW COLUMNS FROM timetable LIKE 'class_id'")
        has_class_id = cursor.fetchone() is not None

        cursor.execute("SHOW COLUMNS FROM timetable LIKE 'subject_id'")
        has_subject_id = cursor.fetchone() is not None

        cursor.execute(
            "SHOW COLUMNS FROM timetable LIKE 'academic_year_id'"
        )
        has_academic_year_id = cursor.fetchone() is not None

        cursor.execute(
            "SHOW COLUMNS FROM timetable LIKE 'department_id'"
        )
        has_department_id = cursor.fetchone() is not None

        has_class_department_id = False
        if has_classes:
            cursor.execute(
                "SHOW COLUMNS FROM classes LIKE 'department_id'"
            )
            has_class_department_id = (
                cursor.fetchone() is not None
            )

        has_room_building_id = False
        if room_table and has_buildings:
            cursor.execute(
                f"SHOW COLUMNS FROM {room_table} "
                "LIKE 'building_id'"
            )
            has_room_building_id = (
                cursor.fetchone() is not None
            )

        room_id_select = (
            "t.room_id"
            if has_room_id
            else "NULL AS room_id"
        )
        teacher_select = (
            "t.teacher_id"
            if has_teacher_id
            else "NULL AS teacher_id"
        )
        class_select = (
            "t.class_id"
            if has_class_id
            else "NULL AS class_id"
        )
        subject_select = (
            "t.subject_id"
            if has_subject_id
            else "NULL AS subject_id"
        )
        year_select = (
            "t.academic_year_id"
            if has_academic_year_id
            else "NULL AS academic_year_id"
        )

        academic_year_join = (
            "LEFT JOIN academic_year a "
            "ON t.academic_year_id = a.id"
            if has_academic_year_id
            else ""
        )
        academic_year_select = (
            "a.year_name AS academic_year"
            if has_academic_year_id
            else "NULL AS academic_year"
        )

        # Department source priority:
        # 1) timetable.department_id
        # 2) classes.department_id via timetable.class_id
        if (
            has_department_id
            and has_class_id
            and has_classes
            and has_class_department_id
        ):
            department_join = (
                "LEFT JOIN classes c ON t.class_id = c.id "
                "LEFT JOIN department d "
                "ON COALESCE(t.department_id, c.department_id) = d.id"
            )
            department_id_select = (
                "COALESCE(t.department_id, c.department_id) AS department_id"
            )
            department_select = (
                "d.department_name AS department_name"
            )
        elif has_department_id:
            department_join = (
                "LEFT JOIN department d "
                "ON t.department_id = d.id"
            )
            department_id_select = (
                "t.department_id AS department_id"
            )
            department_select = (
                "d.department_name AS department_name"
            )
        elif (
            has_class_id
            and has_classes
            and has_class_department_id
        ):
            department_join = (
                "LEFT JOIN classes c ON t.class_id = c.id "
                "LEFT JOIN department d ON c.department_id = d.id"
            )
            department_id_select = (
                "c.department_id AS department_id"
            )
            department_select = (
                "d.department_name AS department_name"
            )
        else:
            department_join = ""
            department_id_select = (
                "NULL AS department_id"
            )
            department_select = (
                "NULL AS department_name"
            )

        teacher_join = (
            "LEFT JOIN users u ON t.teacher_id = u.id"
            if has_teacher_id
            else ""
        )
        teacher_name_select = (
            "u.name AS teacher_name"
            if has_teacher_id
            else "NULL AS teacher_name"
        )

        if has_room_id and room_table:
            resolved_room_expr = (
                "CASE "
                "WHEN r.room_number IS NULL "
                "OR r.room_number = '' "
                "THEN COALESCE(r.room_name, '-') "
                "WHEN r.room_name IS NOT NULL "
                "AND r.room_name <> '' "
                "AND r.room_number REGEXP '^[0-9]+$' "
                "THEN r.room_name "
                "ELSE r.room_number "
                "END"
            )
            room_number_select = (
                f"{resolved_room_expr} AS room_number"
            )
            room_name_select = "r.room_name"

            if has_room_building_id:
                building_id_select = "r.building_id AS building_id"
                building_sort_select = "COALESCE(r.building_id, 0) AS building_sort"
                room_display_select = (
                    "CASE "
                    "WHEN b.building_name IS NOT NULL "
                    "AND b.building_name <> '' "
                    f"THEN CONCAT(b.building_name, ' / ', {resolved_room_expr}) "
                    f"ELSE {resolved_room_expr} "
                    "END AS room_display"
                )
                room_join = (
                    f"LEFT JOIN {room_table} r ON t.room_id = r.id "
                    "LEFT JOIN buildings b ON r.building_id = b.id"
                )
            else:
                building_id_select = "NULL AS building_id"
                building_sort_select = "0 AS building_sort"
                room_display_select = (
                    "NULL AS room_display"
                )
                room_join = (
                    f"LEFT JOIN {room_table} r "
                    "ON t.room_id = r.id"
                )
        elif has_room_text:
            building_id_select = "NULL AS building_id"
            building_sort_select = "0 AS building_sort"
            room_number_select = (
                "COALESCE(t.room, '-') AS room_number"
            )
            room_name_select = (
                "t.room AS room_name"
            )
            room_display_select = (
                "t.room AS room_display"
            )
            room_join = ""
        else:
            building_id_select = "NULL AS building_id"
            building_sort_select = "0 AS building_sort"
            room_number_select = (
                "'-' AS room_number"
            )
            room_name_select = (
                "NULL AS room_name"
            )
            room_display_select = (
                "NULL AS room_display"
            )
            room_join = ""

        sql = f"""
            SELECT
                t.id,
                t.day_of_week,
                t.subject_name,
                TIME_FORMAT(t.start_time, '%H:%i:%s') AS start_time,
                TIME_FORMAT(t.end_time, '%H:%i:%s') AS end_time,
                {room_id_select},
                {building_id_select},
                {building_sort_select},
                {room_number_select},
                {room_name_select},
                {room_display_select},
                {teacher_select},
                {class_select},
                {subject_select},
                {year_select},
                {academic_year_select},
                {department_id_select},
                {department_select},
                {teacher_name_select}
            FROM timetable t
            {room_join}
            {academic_year_join}
            {department_join}
            {teacher_join}
            ORDER BY
                building_sort,
                FIELD(
                    t.day_of_week,
                    'Monday',
                    'Tuesday',
                    'Wednesday',
                    'Thursday',
                    'Friday',
                    'Saturday',
                    'Sunday'
                ),
                t.start_time
        """
        cursor.execute(sql)
        data = cursor.fetchall()
        return jsonify(
            {
                'status': 'success',
                'data': data,
            }
        )

    except pymysql.MySQLError as err:
        return jsonify(
            {
                'status': 'error',
                'message': str(err),
            }
        ), 500

    finally:
        if cursor:
            cursor.close()
        conn.close()


@app.route('/api/admin/delete_schedule/<int:id>', methods=['POST'])
@admin_required
def delete_schedule(id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM timetable WHERE id = %s", (id,))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'status': 'error', 'message': 'រកមិនឃើញកាលវិភាគនេះទេ'}), 404

        return jsonify({'status': 'success', 'message': 'លុបកាលវិភាគបានជោគជ័យ'})
    except pymysql.MySQLError as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        conn.close()
@app.route('/api/admin/add_schedule', methods=['POST'])
@admin_required
def add_schedule():
    data = request.get_json(silent=True) or {}
    day_of_week = data.get('day_of_week')
    department_id = data.get('department_id')
    academic_year_id = data.get('academic_year_id') or 1
    class_id = data.get('class_id') or None
    subject_id = data.get('subject_id') or None
    subject_name = data.get('subject_name')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    room_id = data.get('room_id') or None
    teacher_id = data.get('teacher_id') or 2

    if not day_of_week or not start_time or not end_time:
        return jsonify({'status': 'error', 'message': 'សូមបំពេញព័ត៌មានឱ្យបានគ្រប់'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    cursor = None
    try:
        cursor = conn.cursor()

        cursor.execute("SHOW COLUMNS FROM timetable LIKE 'class_id'")
        has_class_id = cursor.fetchone() is not None
        cursor.execute("SHOW COLUMNS FROM timetable LIKE 'subject_id'")
        has_subject_id = cursor.fetchone() is not None
        cursor.execute("SHOW COLUMNS FROM timetable LIKE 'academic_year_id'")
        has_academic_year_id = cursor.fetchone() is not None
        cursor.execute("SHOW COLUMNS FROM timetable LIKE 'room_id'")
        has_room_id = cursor.fetchone() is not None
        cursor.execute("SHOW COLUMNS FROM timetable LIKE 'teacher_id'")
        has_teacher_id = cursor.fetchone() is not None
        cursor.execute("SHOW COLUMNS FROM timetable LIKE 'department_id'")
        has_department_id = cursor.fetchone() is not None

        has_classes_table = False
        has_class_department_id = False
        cursor.execute("SHOW TABLES LIKE 'classes'")
        has_classes_table = cursor.fetchone() is not None
        if has_classes_table:
            cursor.execute("SHOW COLUMNS FROM classes LIKE 'department_id'")
            has_class_department_id = cursor.fetchone() is not None

        # If department is not sent from UI, infer from selected class.
        if not department_id and class_id and has_classes_table and has_class_department_id:
            cursor.execute(
                "SELECT department_id FROM classes WHERE id = %s",
                (class_id,)
            )
            row = cursor.fetchone()
            if isinstance(row, dict):
                department_id = row.get('department_id')
            elif row:
                department_id = row[0]

        if has_department_id and not department_id:
            return jsonify({'status': 'error', 'message': 'សូមជ្រើសរើសដេប៉ាតឺម៉ង់!'}), 400

        if has_room_id and room_id:
            check_sql = """
                SELECT id FROM timetable
                WHERE day_of_week = %s AND room_id = %s
                AND (
                    (start_time <= %s AND end_time > %s) OR
                    (start_time < %s AND end_time >= %s)
                )
            """
            cursor.execute(check_sql, (day_of_week, room_id, start_time, start_time, end_time, end_time))
            if cursor.fetchone():
                return jsonify({'status': 'error', 'message': 'បន្ទប់នេះមានថ្នាក់ផ្សេងរៀនរួចហើយ!'})

        if not subject_name and subject_id:
            cursor.execute("SELECT subject_name FROM subjects WHERE id = %s", (subject_id,))
            row = cursor.fetchone()
            if isinstance(row, dict):
                subject_name = row.get('subject_name') or ''
            else:
                subject_name = row[0] if row else ''

        columns = ['day_of_week', 'subject_name', 'start_time', 'end_time']
        values = [day_of_week, subject_name or '', start_time, end_time]

        if has_department_id:
            columns.append('department_id')
            values.append(department_id)

        if has_academic_year_id:
            columns.append('academic_year_id')
            values.append(academic_year_id)

        if has_class_id:
            columns.append('class_id')
            values.append(class_id)
        if has_subject_id:
            columns.append('subject_id')
            values.append(subject_id)
        if has_room_id:
            columns.append('room_id')
            values.append(room_id)
        if has_teacher_id:
            columns.append('teacher_id')
            values.append(teacher_id)

        placeholders = ', '.join(['%s'] * len(columns))
        sql = f"INSERT INTO timetable ({', '.join(columns)}) VALUES ({placeholders})"
        cursor.execute(sql, tuple(values))
        conn.commit()
        return jsonify({'status': 'success', 'message': 'បន្ថែមបានជោគជ័យ'})
    except pymysql.MySQLError as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        conn.close()


@app.route('/api/admin/edit_schedule/<int:schedule_id>', methods=['POST'])
@admin_required
def edit_schedule(schedule_id):
    data = request.get_json(silent=True) or {}

    day_of_week = data.get('day_of_week')
    department_id = data.get('department_id')
    academic_year_id = data.get('academic_year_id') or 1
    class_id = data.get('class_id') or None
    subject_id = data.get('subject_id') or None
    subject_name = data.get('subject_name')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    room_id = data.get('room_id') or None
    teacher_id = data.get('teacher_id') or 2

    if not day_of_week or not start_time or not end_time:
        return jsonify({'status': 'error', 'message': 'សូមបំពេញព័ត៌មានឱ្យបានគ្រប់'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    cursor = None
    try:
        cursor = conn.cursor()

        cursor.execute("SHOW COLUMNS FROM timetable LIKE 'class_id'")
        has_class_id = cursor.fetchone() is not None
        cursor.execute("SHOW COLUMNS FROM timetable LIKE 'subject_id'")
        has_subject_id = cursor.fetchone() is not None
        cursor.execute("SHOW COLUMNS FROM timetable LIKE 'academic_year_id'")
        has_academic_year_id = cursor.fetchone() is not None
        cursor.execute("SHOW COLUMNS FROM timetable LIKE 'room_id'")
        has_room_id = cursor.fetchone() is not None
        cursor.execute("SHOW COLUMNS FROM timetable LIKE 'teacher_id'")
        has_teacher_id = cursor.fetchone() is not None
        cursor.execute("SHOW COLUMNS FROM timetable LIKE 'department_id'")
        has_department_id = cursor.fetchone() is not None

        has_classes_table = False
        has_class_department_id = False
        cursor.execute("SHOW TABLES LIKE 'classes'")
        has_classes_table = cursor.fetchone() is not None
        if has_classes_table:
            cursor.execute("SHOW COLUMNS FROM classes LIKE 'department_id'")
            has_class_department_id = cursor.fetchone() is not None

        # If department is not sent from UI, infer from selected class.
        if not department_id and class_id and has_classes_table and has_class_department_id:
            cursor.execute(
                "SELECT department_id FROM classes WHERE id = %s",
                (class_id,)
            )
            row = cursor.fetchone()
            if isinstance(row, dict):
                department_id = row.get('department_id')
            elif row:
                department_id = row[0]

        if has_department_id and not department_id:
            return jsonify({'status': 'error', 'message': 'សូមជ្រើសរើសដេប៉ាតឺម៉ង់!'}), 400

        if has_room_id and room_id:
            check_sql = """
                SELECT id FROM timetable
                WHERE day_of_week = %s AND room_id = %s AND id <> %s
                AND (
                    (start_time <= %s AND end_time > %s) OR
                    (start_time < %s AND end_time >= %s)
                )
            """
            cursor.execute(check_sql, (day_of_week, room_id, schedule_id, start_time, start_time, end_time, end_time))
            if cursor.fetchone():
                return jsonify({'status': 'error', 'message': 'បន្ទប់នេះមានថ្នាក់ផ្សេងរៀនរួចហើយ!'})

        if not subject_name and subject_id:
            cursor.execute("SELECT subject_name FROM subjects WHERE id = %s", (subject_id,))
            row = cursor.fetchone()
            if isinstance(row, dict):
                subject_name = row.get('subject_name') or ''
            else:
                subject_name = row[0] if row else ''

        set_parts = [
            "day_of_week = %s",
            "subject_name = %s",
            "start_time = %s",
            "end_time = %s",
        ]
        params = [day_of_week, subject_name or '', start_time, end_time]

        if has_class_id:
            set_parts.append("class_id = %s")
            params.append(class_id)
        if has_subject_id:
            set_parts.append("subject_id = %s")
            params.append(subject_id)
        if has_academic_year_id:
            set_parts.append("academic_year_id = %s")
            params.append(academic_year_id)
        if has_department_id:
            set_parts.append("department_id = %s")
            params.append(department_id)
        if has_room_id:
            set_parts.append("room_id = %s")
            params.append(room_id)
        if has_teacher_id:
            set_parts.append("teacher_id = %s")
            params.append(teacher_id)

        sql = f"UPDATE timetable SET {', '.join(set_parts)} WHERE id = %s"
        params.append(schedule_id)
        cursor.execute(sql, tuple(params))
        conn.commit()

        if cursor.rowcount == 0:
            # MySQL returns rowcount=0 when values are unchanged.
            cursor.execute("SELECT id FROM timetable WHERE id = %s", (schedule_id,))
            exists = cursor.fetchone() is not None
            if not exists:
                return jsonify({'status': 'error', 'message': 'រកមិនឃើញកាលវិភាគនេះទេ'}), 404

            return jsonify({'status': 'success', 'message': 'មិនមានទិន្នន័យថ្មីសម្រាប់កែប្រែទេ'})

        return jsonify({'status': 'success', 'message': 'កែប្រែកាលវិភាគបានជោគជ័យ'})
    except pymysql.MySQLError as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        conn.close()


@app.route('/api/admin/rooms', methods=['GET'])
@admin_required
def get_admin_rooms():
    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    cursor = None
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("SHOW TABLES LIKE 'rooms'")
        has_rooms = cursor.fetchone() is not None
        table_name = 'rooms' if has_rooms else 'room'

        cursor.execute("SHOW TABLES LIKE 'buildings'")
        has_buildings = cursor.fetchone() is not None
        has_room_building_id = False
        if has_buildings:
            cursor.execute(
                f"SHOW COLUMNS FROM {table_name} "
                "LIKE 'building_id'"
            )
            has_room_building_id = (
                cursor.fetchone() is not None
            )

        if has_buildings and has_room_building_id:
            sql = (
                f"SELECT r.id, r.room_number, r.room_name, r.building_id, b.building_name "
                f"FROM {table_name} r "
                "LEFT JOIN buildings b ON r.building_id = b.id "
                "ORDER BY r.id"
            )
        else:
            sql = f"SELECT id, room_number, room_name, NULL AS building_id, NULL AS building_name FROM {table_name} ORDER BY id"
        cursor.execute(sql)
        rooms = cursor.fetchall() or []
        return jsonify({'status': 'success', 'data': rooms})
    except pymysql.MySQLError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        conn.close()


@app.route('/api/admin/classes', methods=['GET'])
@admin_required
def get_admin_classes_for_schedule():
    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    cursor = None
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SHOW COLUMNS FROM classes LIKE 'room_id'")
        has_room_id = cursor.fetchone() is not None
        cursor.execute("SHOW COLUMNS FROM classes LIKE 'academic_year_id'")
        has_academic_year_id = cursor.fetchone() is not None
        room_col = "room_id" if has_room_id else "NULL AS room_id"
        year_col = "academic_year_id" if has_academic_year_id else "NULL AS academic_year_id"
        if has_academic_year_id:
            class_order = (
                "department_id, academic_year_id, "
                "FIELD(session_type, 'M', 'A', 'E', 'SLS'), class_name"
            )
        else:
            class_order = (
                "department_id, "
                "FIELD(session_type, 'M', 'A', 'E', 'SLS'), class_name"
            )
        cursor.execute(
            f"SELECT id, class_name, session_type, department_id, {room_col}, {year_col} "
            f"FROM classes ORDER BY {class_order}"
        )
        data = cursor.fetchall() or []
        return jsonify({'status': 'success', 'data': data})
    except pymysql.MySQLError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        conn.close()


@app.route('/api/admin/subjects', methods=['GET'])
@admin_required
def get_admin_subjects_for_schedule():
    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    cursor = None
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            """
            SELECT
                s.id,
                s.subject_name,
                s.department_id,
                s.year_id,
                s.semester,
                ay.year_name
            FROM subjects s
            LEFT JOIN academic_year ay ON s.year_id = ay.id
            ORDER BY s.subject_name
            """
        )
        data = cursor.fetchall() or []
        return jsonify({'status': 'success', 'data': data})
    except pymysql.MySQLError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        conn.close()


@app.route('/api/admin/academic_years', methods=['GET'])
@admin_required
def get_years():
    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    cursor = None
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT id, year_name FROM academic_year ORDER BY id")
        years = cursor.fetchall() or []
        return jsonify({'status': 'success', 'data': years})
    except pymysql.MySQLError as err:
        return jsonify({'status': 'error', 'message': str(err)}), 500
    finally:
        if cursor:
            cursor.close()
        conn.close()


@app.route('/api/admin/schedule_dependencies')
@admin_required
def get_schedule_dependencies():
    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    cursor = None
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("SHOW COLUMNS FROM classes LIKE 'room_id'")
        has_room_id = cursor.fetchone() is not None
        cursor.execute("SHOW COLUMNS FROM classes LIKE 'academic_year_id'")
        has_academic_year_id = cursor.fetchone() is not None
        room_col = "room_id" if has_room_id else "NULL AS room_id"
        year_col = "academic_year_id" if has_academic_year_id else "NULL AS academic_year_id"
        if has_academic_year_id:
            class_order = (
                "department_id, academic_year_id, "
                "FIELD(session_type, 'M', 'A', 'E', 'SLS'), class_name"
            )
        else:
            class_order = (
                "department_id, "
                "FIELD(session_type, 'M', 'A', 'E', 'SLS'), class_name"
            )
        cursor.execute(
            f"SELECT id, class_name, session_type, department_id, {room_col}, {year_col} "
            f"SELECT subject_name, year_id, semester FROM subjects ORDER BY subject_name"
            f"FROM classes ORDER BY {class_order}"
        )
        classes = cursor.fetchall() or []

        cursor.execute(
            """
            SELECT
                s.id,
                s.subject_name,
                s.year_id,
                s.semester,
                ay.year_name
            FROM subjects s
            LEFT JOIN academic_year ay ON s.year_id = ay.id
            ORDER BY s.subject_name
            """
        )
        subjects = cursor.fetchall() or []

        cursor.execute("SHOW TABLES LIKE 'rooms'")
        has_rooms = cursor.fetchone() is not None
        room_table = 'rooms' if has_rooms else 'room'

        cursor.execute("SHOW TABLES LIKE 'buildings'")
        has_buildings = cursor.fetchone() is not None
        has_room_building_id = False
        if has_buildings:
            cursor.execute(
                f"SHOW COLUMNS FROM {room_table} "
                "LIKE 'building_id'"
            )
            has_room_building_id = (
                cursor.fetchone() is not None
            )

        if has_buildings and has_room_building_id:
            cursor.execute(
                f"SELECT r.id, r.room_number, r.room_name, r.building_id, b.building_name "
                f"FROM {room_table} r "
                "LEFT JOIN buildings b ON r.building_id = b.id "
                "ORDER BY r.room_number"
            )
        else:
            cursor.execute(f"SELECT id, room_number, room_name, NULL AS building_id, NULL AS building_name FROM {room_table} ORDER BY room_number")
        rooms = cursor.fetchall() or []

        cursor.execute("SELECT id, year_name FROM academic_year ORDER BY id")
        years = cursor.fetchall() or []

        return jsonify({
            'status': 'success',
            'classes': classes,
            'subjects': subjects,
            'rooms': rooms,
            'years': years
        })
    except pymysql.MySQLError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        conn.close()

@app.route('/api/admin/teachers', methods=['GET'])
def get_teachers():
    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    cursor = None
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        sql = """
            SELECT
                t.id,
                t.department_id,
                u.name AS teacher_name,
                t.teacher_code,
                d.department_name,
                IFNULL(NULLIF(t.subject_teach, ''), 'មិនទាន់មានមុខវិជ្ជា') AS subject_teach,
                t.subject_teach AS subject_name,
                u.status
            FROM teachers t
            JOIN users u ON t.user_id = u.id
            LEFT JOIN department d ON t.department_id = d.id
            ORDER BY u.name ASC
        """
        cursor.execute(sql)
        teachers = cursor.fetchall()
        return jsonify({'status': 'success', 'data': teachers})
    finally:
        if cursor:
            cursor.close()
        conn.close()

@app.route('/api/admin/delete_teacher/<int:id>', methods=['POST'])
def delete_teacher(id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor()
        
        # ១. ពិនិត្យមើលថាតើគ្រូនេះមានជាប់កាលវិភាគបង្រៀនដែរឬទេ
        cursor.execute("SELECT id FROM timetable WHERE teacher_id = (SELECT user_id FROM teachers WHERE id = %s)", (id,))
        if cursor.fetchone():
            return jsonify({
                'status': 'error', 
                'message': 'មិនអាចលុបបានទេ! គ្រូបង្រៀននេះមានជាប់ក្នុងកាលវិភាគសិក្សា។'
            }), 400

        # ២. អនុវត្តការលុបចេញពីតារាង teachers
        cursor.execute("DELETE FROM teachers WHERE id = %s", (id,))
        conn.commit()
        
        return jsonify({
            'status': 'success', 
            'message': 'លុបទិន្នន័យគ្រូបង្រៀនបានជោគជ័យ!'
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/admin/add_teacher', methods=['POST'])
def add_teacher():
    data = request.get_json(silent=True) or {}

    # Validate required fields
    required_fields = ['user_id', 'teacher_code', 'department_id']
    for field in required_fields:
        if field not in data:
            return jsonify({
                "status": "error",
                "message": f"Missing field: {field}"
            }), 400

    subject_teach = data.get('subject_teach') or data.get('subjects_teach') or ''

    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    cursor = None
    try:
        cursor = conn.cursor()

        subject_id = data.get('subject_id')
        if not subject_teach and subject_id:
            cursor.execute("SELECT subject_name FROM subjects WHERE id = %s", (subject_id,))
            row = cursor.fetchone()
            if row:
                subject_teach = row[0]

        sql = """
        INSERT INTO teachers (user_id, teacher_code, department_id, subject_teach)
        VALUES (%s, %s, %s, %s)
        """

        cursor.execute(sql, (
            data['user_id'],
            data['teacher_code'],
            data['department_id'],
            subject_teach
        ))

        conn.commit()

        return jsonify({
            "status": "success",
            "message": "បន្ថែមគ្រូបង្រៀនជោគជ័យ!",
            "teacher_id": cursor.lastrowid
        })

    except Exception as e:
        conn.rollback()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        conn.close()

@app.route('/api/admin/update_teacher', methods=['POST'])
def update_teacher_info():
    data = request.json
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        sql = """UPDATE teachers 
                 SET teacher_code = %s, department_id = %s, subject_teach = %s 
                 WHERE id = %s"""
        cursor.execute(sql, (
            data['teacher_code'], 
            data['department_id'], 
            data['subject_teach'], 
            data['id']
        ))
        conn.commit()
        return jsonify({'status': 'success', 'message': 'កែប្រែព័ត៌មានគ្រូជោគជ័យ!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()
        
        
if __name__ == '__main__':
    app.run(debug=True)