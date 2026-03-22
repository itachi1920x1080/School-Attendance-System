import pymysql
import pymysql.cursors
from db.db import DB_CONFIG

# ដាក់ function នេះលើគេ ដើម្បីអោយ init_db ស្គាល់វា
def get_db_connection():
    config = DB_CONFIG.copy()
    # ប្រើ DictCursor ដើម្បីងាយស្រួលទាញយកទិន្នន័យជាឈ្មោះ Column
    config['cursorclass'] = pymysql.cursors.DictCursor 
    return pymysql.connect(**config)

def init_db():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # ១. បង្កើតតារាង Users (ត្រូវតាមទម្រង់ដែល app.py ត្រូវការ)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    role ENUM('Admin', 'Teacher', 'Student', 'admin', 'teacher', 'student') NOT NULL,
                    status ENUM('Active', 'Inactive') DEFAULT 'Active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # ២. បង្កើតតារាង classes (តាម schema ដែលត្រូវការ)
            # ចំណាំ៖ តារាង department ត្រូវតែមានជាមុនសិន (Foreign Key)
            cursor.execute("SHOW TABLES LIKE 'department'")
            has_department = cursor.fetchone() is not None
            if has_department:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS classes (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        class_name VARCHAR(20) UNIQUE NOT NULL,
                        session_type ENUM('M', 'A', 'E', 'SLS') NOT NULL,
                        department_id INT,
                        room_name VARCHAR(50) DEFAULT 'N/A',
                        FOREIGN KEY (department_id) REFERENCES department(id) ON DELETE SET NULL
                    );
                """)
            
            # ៣. បង្កើតគណនី Admin ដោយស្វ័យប្រវត្តិ (បើមិនទាន់មាន)
            cursor.execute("SELECT COUNT(*) as count FROM users")
            result = cursor.fetchone()
            
            if result['count'] == 0:
                cursor.execute("""
                    INSERT INTO users (name, email, password, role, status) 
                    VALUES ('Admin User', 'admin@hitech.edu', '123456', 'Admin', 'Active')
                """)
                print("Default Admin user created: admin@hitech.edu / 123456")

        connection.commit()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        connection.close()

# ប្រសិនបើអ្នកចង់ឱ្យវា Run ពេលហៅ File នេះផ្ទាល់
if __name__ == "__main__":
    init_db()