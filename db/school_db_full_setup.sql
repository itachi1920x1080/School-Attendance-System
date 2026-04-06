-- ==========================================
-- School Database Full Setup (MySQL)
-- Fixed version of your script (room/rooms naming + table consistency)
-- ==========================================

SET FOREIGN_KEY_CHECKS = 0;

DROP DATABASE IF EXISTS school_db;
CREATE DATABASE school_db;
USE school_db;

-- ==========================================
-- 1) Parent Tables
-- ==========================================
CREATE TABLE colleges (
    id INT AUTO_INCREMENT PRIMARY KEY,
    college_name VARCHAR(150) UNIQUE NOT NULL
);

CREATE TABLE buildings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    building_name VARCHAR(100) NOT NULL,
    room_count INT
);

CREATE TABLE department (
    id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(150) NOT NULL,
    college_id INT NOT NULL,
    UNIQUE(department_name, college_id),
    FOREIGN KEY (college_id) REFERENCES colleges(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE academic_year (
    id INT AUTO_INCREMENT PRIMARY KEY,
    year_name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE generations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    generation_name VARCHAR(50) UNIQUE NOT NULL,
    start_year YEAR NOT NULL,
    end_year YEAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (end_year > start_year)
);

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('Admin', 'Teacher', 'Student') NOT NULL,
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    student_code VARCHAR(50),
    class_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE

);

CREATE TABLE teachers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    teacher_code VARCHAR(50),
    department_id INT,
    subject_teach VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    position VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ==========================================
-- 2) Child Tables
-- ==========================================
CREATE TABLE classes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class_name VARCHAR(20) NOT NULL,
    session_type ENUM('M', 'A', 'E', 'SLS') NOT NULL,
    department_id INT,
    building_id INT,
    room_id INT,
    teacher_id INT,
    room_name VARCHAR(50) DEFAULT 'N/A',
    academic_year_id INT,
    UNIQUE(class_name, academic_year_id),
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE SET NULL,
    FOREIGN KEY (department_id) REFERENCES department(id) ON DELETE SET NULL,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (academic_year_id) REFERENCES academic_year(id) ON DELETE SET NULL
);

CREATE TABLE subjects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject_name VARCHAR(150) NOT NULL,
    department_id INT NOT NULL,
    year_id INT NOT NULL,
    semester TINYINT NOT NULL CHECK (semester IN (1,2)),
    credits TINYINT DEFAULT 3,
    UNIQUE(subject_name, department_id, year_id, semester),
    FOREIGN KEY (department_id) REFERENCES department(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (year_id) REFERENCES academic_year(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Compatibility view for modules/scripts that use "courses" naming.
CREATE OR REPLACE VIEW courses AS
SELECT
    id,
    subject_name AS course_name,
    department_id,
    year_id,
    semester,
    credits
FROM subjects;

CREATE TABLE rooms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    building_id INT NOT NULL,
    room_number VARCHAR(20) NOT NULL,
    room_name VARCHAR(100) NOT NULL,
    floor INT NOT NULL,
    room_type VARCHAR(50) NOT NULL,
    UNIQUE(building_id, room_number),
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
);

-- after rooms table exists
ALTER TABLE classes
ADD CONSTRAINT fk_classes_room
FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE SET NULL;

CREATE TABLE user_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    user_id INT NOT NULL,
    id_number VARCHAR(50),
    gender ENUM('Male', 'Female', 'Other'),
    dob DATE,
    generation_id INT,
    department_id INT,
    academic_year_id INT,
    class_id INT,
    phone VARCHAR(20),
    address TEXT,
    photo VARCHAR(255) DEFAULT 'default.png',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (generation_id) REFERENCES generations(id) ON DELETE SET NULL,
    FOREIGN KEY (department_id) REFERENCES department(id) ON DELETE SET NULL,
    FOREIGN KEY (academic_year_id) REFERENCES academic_year(id) ON DELETE SET NULL,
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE SET NULL
);

CREATE TABLE timetable (
    id INT AUTO_INCREMENT PRIMARY KEY,
    department_id INT,
    academic_year_id INT,
    class_id INT,
    subject_id INT,
    semester INT,
    subject_name VARCHAR(100) NOT NULL,
    day_of_week ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday') NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    room_id INT,
    teacher_id INT,
    
    FOREIGN KEY (department_id) REFERENCES department(id) ON DELETE CASCADE,
    FOREIGN KEY (academic_year_id) REFERENCES academic_year(id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE SET NULL,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE SET NULL,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE support_tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    subject VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    priority ENUM('Low', 'Medium', 'High') DEFAULT 'Medium',
    description TEXT NOT NULL,
    status ENUM('Open', 'In Progress', 'Resolved', 'Closed') DEFAULT 'Open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    class_id INT NOT NULL,
    subject_id INT NOT NULL,
    teacher_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    status ENUM('Present', 'Absent', 'Late', 'Excused') NOT NULL,
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, subject_id, attendance_date),
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE enrollments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    subject_id INT NOT NULL,
    academic_year_id INT NOT NULL,
    semester TINYINT NOT NULL,
    UNIQUE(student_id, subject_id),
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (academic_year_id) REFERENCES academic_year(id) ON DELETE CASCADE
);

CREATE TABLE grades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    enrollment_id INT NOT NULL,
    score DECIMAL(5,2),
    grade_letter VARCHAR(2),
    FOREIGN KEY (enrollment_id) REFERENCES enrollments(id) ON DELETE CASCADE
);

CREATE TABLE audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(255),
    table_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- ==========================================
-- 3) View
-- ==========================================
CREATE VIEW v_student_profiles AS
SELECT
    u.id AS user_id,
    u.name AS student_name,
    u.email,
    u.status,
    up.id_number,
    up.gender,
    up.phone,
    up.address,
    COALESCE(CONCAT(g.generation_name, ' (', g.start_year, '-', g.end_year, ')'), 'N/A') AS generation_display,
    d.id AS department_id,
    d.department_name,
    col.id AS college_id,
    col.college_name,
    ay.id AS academic_year_id,
    ay.year_name,
    cl.id AS class_id,
    cl.class_name
FROM users u
JOIN user_profiles up ON u.id = up.user_id
LEFT JOIN generations g ON up.generation_id = g.id
LEFT JOIN department d ON up.department_id = d.id
LEFT JOIN colleges col ON d.college_id = col.id
LEFT JOIN academic_year ay ON up.academic_year_id = ay.id
LEFT JOIN classes cl ON up.class_id = cl.id
WHERE u.role = 'Student';

CREATE VIEW v_teachers_with_timetable AS
SELECT
    u.id AS teacher_id,
    u.name AS teacher_name,
    u.email,
    COALESCE(tch.teacher_code, 'N/A') AS teacher_code,
    COALESCE(d.department_name, 'N/A') AS department_name,
    COUNT(t.id) AS schedule_count,
    MIN(t.start_time) AS first_period,
    MAX(t.end_time) AS last_period
FROM users u
LEFT JOIN teachers tch ON tch.user_id = u.id
LEFT JOIN department d ON d.id = tch.department_id
LEFT JOIN timetable t ON t.teacher_id = u.id
WHERE u.role = 'Teacher'
GROUP BY
    u.id,
    u.name,
    u.email,
    tch.teacher_code,
    d.department_name
HAVING COUNT(t.id) > 0;

CREATE VIEW v_teachers_without_timetable AS
SELECT
    u.id AS teacher_id,
    u.name AS teacher_name,
    u.email,
    COALESCE(tch.teacher_code, 'N/A') AS teacher_code,
    COALESCE(d.department_name, 'N/A') AS department_name
FROM users u
LEFT JOIN teachers tch ON tch.user_id = u.id
LEFT JOIN department d ON d.id = tch.department_id
LEFT JOIN timetable t ON t.teacher_id = u.id
WHERE u.role = 'Teacher'
GROUP BY
    u.id,
    u.name,
    u.email,
    tch.teacher_code,
    d.department_name
HAVING COUNT(t.id) = 0;

-- ==========================================
-- 4) Trigger
-- ==========================================
DELIMITER //
CREATE TRIGGER after_user_insert
AFTER INSERT ON users
FOR EACH ROW
BEGIN
    INSERT INTO user_profiles (user_id) VALUES (NEW.id);
END //
DELIMITER ;

-- ==========================================
-- 5) Master Data
-- ==========================================
INSERT INTO colleges (college_name) VALUES
('College of Social Sciences and Humanities'),
('Faculty of Engineering'),
('Faculty of Science'),
('Faculty of Development Studies'),
('College of Education'),
('Institute of International Studies and Public Policy'),
('Institute of Foreign Languages');

INSERT INTO department (department_name, college_id) VALUES
('Khmer Literature', 1), ('Geography and Land Management', 1), ('Psychology', 1), ('Sociology', 1), ('History', 1), ('Philosophy', 1), ('Communication media', 1), ('Tourism', 1), ('Linguistics', 1), ('International Business Management', 1),
('Biological Engineering', 2), ('Information Technology Engineering', 2), ('Electronics and telecommunications engineering', 2), ('Food Engineering and Technology', 2), ('Data Science Engineering', 2), ('Environmental Engineering', 2), ('Automation and supply chain engineering', 2),
('Mathematics', 3), ('Physics', 3), ('Biology', 3), ('Environment', 3), ('Information Technology', 3), ('Chemistry', 3),
('Economic development', 4), ('Community development', 4), ('Manage and development of natural resources', 4), ('Urban planning and sustainable urban development', 4),
('Lifelong education', 5), ('Education', 5), ('Higher Education Management and Development', 5),
('International Relations', 6), ('International Economy', 6), ('Political Science and Public Administration', 6),
('English', 7), ('French', 7), ('Japanese', 7), ('Korean', 7), ('Chinese', 7), ('Thai', 7);

INSERT INTO buildings (building_name, room_count) VALUES
('Building A', 72),
('Building B', 72),
('Building C', 72),
('Building D', 72),
('Building T', 72);

INSERT INTO rooms (building_id, room_number, room_name, floor, room_type) VALUES
(1, 'A-101', 'General Classroom A-101', 1, 'Classroom'),
(1, 'A-102', 'General Classroom A-102', 1, 'Classroom'),
(1, 'A-103', 'General Classroom A-103', 1, 'Classroom'),
(1, 'A-104', 'General Classroom A-104', 1, 'Classroom'),
(1, 'A-105', 'General Classroom A-105', 1, 'Classroom'),
(1, 'A-106', 'General Classroom A-106', 1, 'Classroom'),
(1, 'A-107', 'General Classroom A-107', 1, 'Classroom'),
(1, 'A-108', 'General Classroom A-108', 1, 'Classroom'),
(1, 'A-109', 'General Classroom A-109', 1, 'Classroom'),
(1, 'A-LAB-STAM', 'Computer Lab STAM', 6, 'Computer Lab STAM'),
(1, 'A-110', 'General Classroom A-110', 1, 'Classroom'),
(1, 'A-111', 'General Classroom A-111', 1, 'Classroom'),
(1, 'A-112', 'General Classroom A-112', 1, 'Classroom'),
(1, 'A-113', 'General Classroom A-113', 1, 'Classroom'),
(1, 'A-114', 'General Classroom A-114', 2, 'Classroom'),
(1, 'A-115', 'General Classroom A-115', 2, 'Classroom'),
(1, 'A-116', 'General Classroom A-116', 2, 'Classroom'),
(1, 'A-117', 'General Classroom A-117', 2, 'Classroom'),
(1, 'A-118', 'General Classroom A-118', 2, 'Classroom'),
(1, 'A-201', 'General Classroom A-201', 2, 'Classroom'),
(1, 'A-202', 'General Classroom A-202', 2, 'Classroom'),
(1, 'A-203', 'General Classroom A-203', 2, 'Classroom'),
(1, 'A-204', 'General Classroom A-204', 2, 'Classroom'),
(1, 'A-205', 'General Classroom A-205', 2, 'Classroom'),
(1, 'A-206', 'General Classroom A-206', 2, 'Classroom'),
(1, 'A-207', 'General Classroom A-207', 2, 'Classroom'),
(1, 'A-208', 'General Classroom A-208', 2, 'Classroom'),
(1, 'A-209', 'General Classroom A-209', 2, 'Classroom'),
(1, 'A-210', 'Lab Room A-210', 2, 'Laboratory'),
(1, 'A-301', 'General Classroom A-301', 3, 'Classroom'),
(1, 'A-302', 'General Classroom A-302', 3, 'Classroom'),
(1, 'A-303', 'General Classroom A-303', 3, 'Classroom'),
(1, 'A-304', 'General Classroom A-304', 3, 'Classroom'),
(1, 'A-305', 'General Classroom A-305', 3, 'Classroom'),
(1, 'A-306', 'General Classroom A-306', 3, 'Classroom'),
(1, 'A-307', 'General Classroom A-307', 3, 'Classroom'),
(1, 'A-308', 'General Classroom A-308', 3, 'Classroom'),
(1, 'A-309', 'General Classroom A-309', 3, 'Classroom'),
(1, 'A-310', 'Lab Room A-310', 3, 'Laboratory'),
(1, 'A-401', 'General Classroom A-401', 4, 'Classroom'),
(1, 'A-402', 'General Classroom A-402', 4, 'Classroom'),
(1, 'A-403', 'General Classroom A-403', 4, 'Classroom'),
(1, 'A-404', 'General Classroom A-404', 4, 'Classroom'),
(1, 'A-405', 'General Classroom A-405', 4, 'Classroom'),
(1, 'A-406', 'General Classroom A-406', 4, 'Classroom'),
(1, 'A-407', 'General Classroom A-407', 4, 'Classroom'),
(1, 'A-408', 'General Classroom A-408', 4, 'Classroom'),
(1, 'A-409', 'General Classroom A-409', 4, 'Classroom'),
(1, 'A-410', 'Lab Room A-410', 4, 'Laboratory'),
(1, 'A-501', 'Meeting Room A-501', 5, 'Meeting'),
(1, 'A-502', 'Conference Room A-502', 5, 'Conference'),
(1, 'A-503', 'Library A-503', 5, 'Library'),
(1, 'A-504', 'Admin Office A-504', 5, 'Office'),
(1, 'A-211', 'General Classroom A-211', 2, 'Classroom'),
(1, 'A-212', 'Computer Lab Floor 2', 2, 'Computer Lab'),
(1, 'A-311', 'General Classroom A-311', 3, 'Classroom'),
(1, 'A-312', 'Computer Lab Floor 3', 3, 'Computer Lab'),
(1, 'A-411', 'General Classroom A-411', 4, 'Classroom'),
(1, 'A-412', 'Computer Lab Floor 4', 4, 'Computer Lab'),
(1, 'A-511', 'General Classroom A-511', 5, 'Classroom'),
(1, 'A-512', 'Computer Lab Floor 5', 5, 'Computer Lab'),

-- Building B (building_id = 2)
(2, 'B-101', 'General Classroom B-101', 1, 'Classroom'),
(2, 'B-102', 'General Classroom B-102', 1, 'Classroom'),
(2, 'B-103', 'General Classroom B-103', 1, 'Classroom'),
(2, 'B-104', 'General Classroom B-104', 1, 'Classroom'),
(2, 'B-105', 'General Classroom B-105', 1, 'Classroom'),
(2, 'B-106', 'General Classroom B-106', 1, 'Classroom'),
(2, 'B-107', 'General Classroom B-107', 1, 'Classroom'),
(2, 'B-108', 'General Classroom B-108', 1, 'Classroom'),
(2, 'B-109', 'General Classroom B-109', 1, 'Classroom'),
(2, 'B-110', 'General Classroom B-110', 1, 'Classroom'),
(2, 'B-201', 'General Classroom B-201', 2, 'Classroom'),
(2, 'B-202', 'General Classroom B-202', 2, 'Classroom'),
(2, 'B-203', 'General Classroom B-203', 2, 'Classroom'),
(2, 'B-204', 'General Classroom B-204', 2, 'Classroom'),
(2, 'B-205', 'General Classroom B-205', 2, 'Classroom'),
(2, 'B-206', 'General Classroom B-206', 2, 'Classroom'),
(2, 'B-207', 'General Classroom B-207', 2, 'Classroom'),
(2, 'B-208', 'General Classroom B-208', 2, 'Classroom'),
(2, 'B-209', 'General Classroom B-209', 2, 'Classroom'),
(2, 'B-210', 'Lab Room B-210', 2, 'Laboratory'),
(2, 'B-211', 'General Classroom B-211', 2, 'Classroom'),
(2, 'B-212', 'Computer Lab Floor 2', 2, 'Computer Lab'),
(2, 'B-301', 'General Classroom B-301', 3, 'Classroom'),
(2, 'B-302', 'General Classroom B-302', 3, 'Classroom'),
(2, 'B-303', 'General Classroom B-303', 3, 'Classroom'),
(2, 'B-304', 'General Classroom B-304', 3, 'Classroom'),
(2, 'B-305', 'General Classroom B-305', 3, 'Classroom'),
(2, 'B-306', 'General Classroom B-306', 3, 'Classroom'),
(2, 'B-307', 'General Classroom B-307', 3, 'Classroom'),
(2, 'B-308', 'General Classroom B-308', 3, 'Classroom'),
(2, 'B-309', 'General Classroom B-309', 3, 'Classroom'),
(2, 'B-310', 'Lab Room B-310', 3, 'Laboratory'),
(2, 'B-311', 'General Classroom B-311', 3, 'Classroom'),
(2, 'B-312', 'Computer Lab Floor 3', 3, 'Computer Lab'),
(2, 'B-401', 'General Classroom B-401', 4, 'Classroom'),
(2, 'B-402', 'General Classroom B-402', 4, 'Classroom'),
(2, 'B-403', 'General Classroom B-403', 4, 'Classroom'),
(2, 'B-404', 'General Classroom B-404', 4, 'Classroom'),
(2, 'B-405', 'General Classroom B-405', 4, 'Classroom'),
(2, 'B-406', 'General Classroom B-406', 4, 'Classroom'),
(2, 'B-407', 'General Classroom B-407', 4, 'Classroom'),
(2, 'B-408', 'General Classroom B-408', 4, 'Classroom'),
(2, 'B-409', 'General Classroom B-409', 4, 'Classroom'),
(2, 'B-410', 'Lab Room B-410', 4, 'Laboratory'),
(2, 'B-411', 'General Classroom B-411', 4, 'Classroom'),
(2, 'B-412', 'Computer Lab Floor 4', 4, 'Computer Lab'),
(2, 'B-501', 'Meeting Room B-501', 5, 'Meeting'),
(2, 'B-502', 'Conference Room B-502', 5, 'Conference'),
(2, 'B-503', 'Library B-503', 5, 'Library'),
(2, 'B-504', 'Admin Office B-504', 5, 'Office'),
(2, 'B-511', 'General Classroom B-511', 5, 'Classroom'),
(2, 'B-512', 'Computer Lab Floor 5', 5, 'Computer Lab'),

-- Building C (building_id = 3)
(3, 'C-101', 'General Classroom C-101', 1, 'Classroom'),
(3, 'C-102', 'General Classroom C-102', 1, 'Classroom'),
(3, 'C-103', 'General Classroom C-103', 1, 'Classroom'),
(3, 'C-104', 'General Classroom C-104', 1, 'Classroom'),
(3, 'C-105', 'General Classroom C-105', 1, 'Classroom'),
(3, 'C-106', 'General Classroom C-106', 1, 'Classroom'),
(3, 'C-107', 'General Classroom C-107', 1, 'Classroom'),
(3, 'C-108', 'General Classroom C-108', 1, 'Classroom'),
(3, 'C-109', 'General Classroom C-109', 1, 'Classroom'),
(3, 'C-110', 'General Classroom C-110', 1, 'Classroom'),
(3, 'C-201', 'General Classroom C-201', 2, 'Classroom'),
(3, 'C-202', 'General Classroom C-202', 2, 'Classroom'),
(3, 'C-203', 'General Classroom C-203', 2, 'Classroom'),
(3, 'C-204', 'General Classroom C-204', 2, 'Classroom'),
(3, 'C-205', 'General Classroom C-205', 2, 'Classroom'),
(3, 'C-206', 'General Classroom C-206', 2, 'Classroom'),
(3, 'C-207', 'General Classroom C-207', 2, 'Classroom'),
(3, 'C-208', 'General Classroom C-208', 2, 'Classroom'),
(3, 'C-209', 'General Classroom C-209', 2, 'Classroom'),
(3, 'C-210', 'Lab Room C-210', 2, 'Laboratory'),
(3, 'C-211', 'General Classroom C-211', 2, 'Classroom'),
(3, 'C-212', 'Computer Lab Floor 2', 2, 'Computer Lab'),
(3, 'C-301', 'General Classroom C-301', 3, 'Classroom'),
(3, 'C-302', 'General Classroom C-302', 3, 'Classroom'),
(3, 'C-303', 'General Classroom C-303', 3, 'Classroom'),
(3, 'C-304', 'General Classroom C-304', 3, 'Classroom'),
(3, 'C-305', 'General Classroom C-305', 3, 'Classroom'),
(3, 'C-306', 'General Classroom C-306', 3, 'Classroom'),
(3, 'C-307', 'General Classroom C-307', 3, 'Classroom'),
(3, 'C-308', 'General Classroom C-308', 3, 'Classroom'),
(3, 'C-309', 'General Classroom C-309', 3, 'Classroom'),
(3, 'C-310', 'Lab Room C-310', 3, 'Laboratory'),
(3, 'C-311', 'General Classroom C-311', 3, 'Classroom'),
(3, 'C-312', 'Computer Lab Floor 3', 3, 'Computer Lab'),
(3, 'C-401', 'General Classroom C-401', 4, 'Classroom'),
(3, 'C-402', 'General Classroom C-402', 4, 'Classroom'),
(3, 'C-403', 'General Classroom C-403', 4, 'Classroom'),
(3, 'C-404', 'General Classroom C-404', 4, 'Classroom'),
(3, 'C-405', 'General Classroom C-405', 4, 'Classroom'),
(3, 'C-406', 'General Classroom C-406', 4, 'Classroom'),
(3, 'C-407', 'General Classroom C-407', 4, 'Classroom'),
(3, 'C-408', 'General Classroom C-408', 4, 'Classroom'),
(3, 'C-409', 'General Classroom C-409', 4, 'Classroom'),
(3, 'C-410', 'Lab Room C-410', 4, 'Laboratory'),
(3, 'C-411', 'General Classroom C-411', 4, 'Classroom'),
(3, 'C-412', 'Computer Lab Floor 4', 4, 'Computer Lab'),
(3, 'C-501', 'Meeting Room C-501', 5, 'Meeting'),
(3, 'C-502', 'Conference Room C-502', 5, 'Conference'),
(3, 'C-503', 'Library C-503', 5, 'Library'),
(3, 'C-504', 'Admin Office C-504', 5, 'Office'),
(3, 'C-511', 'General Classroom C-511', 5, 'Classroom'),
(3, 'C-512', 'Computer Lab Floor 5', 5, 'Computer Lab'),

-- Building D (building_id = 4)
(4, 'D-101', 'General Classroom D-101', 1, 'Classroom'),
(4, 'D-102', 'General Classroom D-102', 1, 'Classroom'),
(4, 'D-103', 'General Classroom D-103', 1, 'Classroom'),
(4, 'D-104', 'General Classroom D-104', 1, 'Classroom'),
(4, 'D-105', 'General Classroom D-105', 1, 'Classroom'),
(4, 'D-106', 'General Classroom D-106', 1, 'Classroom'),
(4, 'D-107', 'General Classroom D-107', 1, 'Classroom'),
(4, 'D-108', 'General Classroom D-108', 1, 'Classroom'),
(4, 'D-109', 'General Classroom D-109', 1, 'Classroom'),
(4, 'D-110', 'General Classroom D-110', 1, 'Classroom'),
(4, 'D-201', 'General Classroom D-201', 2, 'Classroom'),
(4, 'D-202', 'General Classroom D-202', 2, 'Classroom'),
(4, 'D-203', 'General Classroom D-203', 2, 'Classroom'),
(4, 'D-204', 'General Classroom D-204', 2, 'Classroom'),
(4, 'D-205', 'General Classroom D-205', 2, 'Classroom'),
(4, 'D-206', 'General Classroom D-206', 2, 'Classroom'),
(4, 'D-207', 'General Classroom D-207', 2, 'Classroom'),
(4, 'D-208', 'General Classroom D-208', 2, 'Classroom'),
(4, 'D-209', 'General Classroom D-209', 2, 'Classroom'),
(4, 'D-210', 'Lab Room D-210', 2, 'Laboratory'),
(4, 'D-211', 'General Classroom D-211', 2, 'Classroom'),
(4, 'D-212', 'Computer Lab Floor 2', 2, 'Computer Lab'),
(4, 'D-301', 'General Classroom D-301', 3, 'Classroom'),
(4, 'D-302', 'General Classroom D-302', 3, 'Classroom'),
(4, 'D-303', 'General Classroom D-303', 3, 'Classroom'),
(4, 'D-304', 'General Classroom D-304', 3, 'Classroom'),
(4, 'D-305', 'General Classroom D-305', 3, 'Classroom'),
(4, 'D-306', 'General Classroom D-306', 3, 'Classroom'),
(4, 'D-307', 'General Classroom D-307', 3, 'Classroom'),
(4, 'D-308', 'General Classroom D-308', 3, 'Classroom'),
(4, 'D-309', 'General Classroom D-309', 3, 'Classroom'),
(4, 'D-310', 'Lab Room D-310', 3, 'Laboratory'),
(4, 'D-311', 'General Classroom D-311', 3, 'Classroom'),
(4, 'D-312', 'Computer Lab Floor 3', 3, 'Computer Lab'),
(4, 'D-401', 'General Classroom D-401', 4, 'Classroom'),
(4, 'D-402', 'General Classroom D-402', 4, 'Classroom'),
(4, 'D-403', 'General Classroom D-403', 4, 'Classroom'),
(4, 'D-404', 'General Classroom D-404', 4, 'Classroom'),
(4, 'D-405', 'General Classroom D-405', 4, 'Classroom'),
(4, 'D-406', 'General Classroom D-406', 4, 'Classroom'),
(4, 'D-407', 'General Classroom D-407', 4, 'Classroom'),
(4, 'D-408', 'General Classroom D-408', 4, 'Classroom'),
(4, 'D-409', 'General Classroom D-409', 4, 'Classroom'),
(4, 'D-410', 'Lab Room D-410', 4, 'Laboratory'),
(4, 'D-411', 'General Classroom D-411', 4, 'Classroom'),
(4, 'D-412', 'Computer Lab Floor 4', 4, 'Computer Lab'),
(4, 'D-501', 'Meeting Room D-501', 5, 'Meeting'),
(4, 'D-502', 'Conference Room D-502', 5, 'Conference'),
(4, 'D-503', 'Library D-503', 5, 'Library'),
(4, 'D-504', 'Admin Office D-504', 5, 'Office'),
(4, 'D-511', 'General Classroom D-511', 5, 'Classroom'),
(4, 'D-512', 'Computer Lab Floor 5', 5, 'Computer Lab'),

-- Building T (building_id = 5)
(5, 'T-101', 'General Classroom T-101', 1, 'Classroom'),
(5, 'T-102', 'General Classroom T-102', 1, 'Classroom'),
(5, 'T-103', 'General Classroom T-103', 1, 'Classroom'),
(5, 'T-104', 'General Classroom T-104', 1, 'Classroom'),
(5, 'T-105', 'General Classroom T-105', 1, 'Classroom'),
(5, 'T-106', 'General Classroom T-106', 1, 'Classroom'),
(5, 'T-107', 'General Classroom T-107', 1, 'Classroom'),
(5, 'T-108', 'General Classroom T-108', 1, 'Classroom'),
(5, 'T-109', 'General Classroom T-109', 1, 'Classroom'),
(5, 'T-110', 'General Classroom T-110', 1, 'Classroom'),
(5, 'T-201', 'General Classroom T-201', 2, 'Classroom'),
(5, 'T-202', 'General Classroom T-202', 2, 'Classroom'),
(5, 'T-203', 'General Classroom T-203', 2, 'Classroom'),
(5, 'T-204', 'General Classroom T-204', 2, 'Classroom'),
(5, 'T-205', 'General Classroom T-205', 2, 'Classroom'),
(5, 'T-206', 'General Classroom T-206', 2, 'Classroom'),
(5, 'T-207', 'General Classroom T-207', 2, 'Classroom'),
(5, 'T-208', 'General Classroom T-208', 2, 'Classroom'),
(5, 'T-209', 'General Classroom T-209', 2, 'Classroom'),
(5, 'T-210', 'Lab Room T-210', 2, 'Laboratory'),
(5, 'T-211', 'General Classroom T-211', 2, 'Classroom'),
(5, 'T-212', 'Computer Lab Floor 2', 2, 'Computer Lab'),
(5, 'T-301', 'General Classroom T-301', 3, 'Classroom'),
(5, 'T-302', 'General Classroom T-302', 3, 'Classroom'),
(5, 'T-303', 'General Classroom T-303', 3, 'Classroom'),
(5, 'T-304', 'General Classroom T-304', 3, 'Classroom'),
(5, 'T-305', 'General Classroom T-305', 3, 'Classroom'),
(5, 'T-306', 'General Classroom T-306', 3, 'Classroom'),
(5, 'T-307', 'General Classroom T-307', 3, 'Classroom'),
(5, 'T-308', 'General Classroom T-308', 3, 'Classroom'),
(5, 'T-309', 'General Classroom T-309', 3, 'Classroom'),
(5, 'T-310', 'Lab Room T-310', 3, 'Laboratory'),
(5, 'T-311', 'General Classroom T-311', 3, 'Classroom'),
(5, 'T-312', 'Computer Lab Floor 3', 3, 'Computer Lab'),
(5, 'T-401', 'General Classroom T-401', 4, 'Classroom'),
(5, 'T-402', 'General Classroom T-402', 4, 'Classroom'),
(5, 'T-403', 'General Classroom T-403', 4, 'Classroom'),
(5, 'T-404', 'General Classroom T-404', 4, 'Classroom'),
(5, 'T-405', 'General Classroom T-405', 4, 'Classroom'),
(5, 'T-406', 'General Classroom T-406', 4, 'Classroom'),
(5, 'T-407', 'General Classroom T-407', 4, 'Classroom'),
(5, 'T-408', 'General Classroom T-408', 4, 'Classroom'),
(5, 'T-409', 'General Classroom T-409', 4, 'Classroom'),
(5, 'T-410', 'Lab Room T-410', 4, 'Laboratory'),
(5, 'T-411', 'General Classroom T-411', 4, 'Classroom'),
(5, 'T-412', 'Computer Lab Floor 4', 4, 'Computer Lab'),
(5, 'T-501', 'Meeting Room T-501', 5, 'Meeting'),
(5, 'T-502', 'Conference Room T-502', 5, 'Conference'),
(5, 'T-503', 'Library T-503', 5, 'Library'),
(5, 'T-504', 'Admin Office T-504', 5, 'Office'),
(5, 'T-511', 'General Classroom T-511', 5, 'Classroom'),
(5, 'T-512', 'Computer Lab Floor 5', 5, 'Computer Lab');

INSERT INTO academic_year (year_name) VALUES
('ឆ្នាំទី ១ (Year 1)'), ('ឆ្នាំទី ២ (Year 2)'), ('ឆ្នាំទី ៣ (Year 3)'), ('ឆ្នាំទី ៤ (Year 4)');

INSERT INTO generations (generation_name, start_year, end_year) VALUES
('Batch 1 (2023-2027)', 2023, 2027), ('Batch 2 (2024-2028)', 2024, 2028), ('Batch 3 (2025-2029)', 2025, 2029), ('Batch 4 (2026-2030)', 2026, 2030);

INSERT INTO classes (
    class_name,
    session_type,
    department_id,
    room_id,
    room_name,
    academic_year_id
) VALUES
-- Year 1
('M1','M',22,1,'A-101',1),
('M2','M',22,2,'A-102',1),
('M3','M',22,3,'A-103',1),
('M4','M',22,4,'A-104',1),
('M5','M',22,5,'A-105',1),
('M6','M',22,6,'A-106',1),
('M7','M',22,7,'A-107',1),
('M8','M',22,8,'A-108',1),
('M9','M',22,9,'A-109',1),
('A1','A',22,1,'A-101',1),
('A2','A',22,2,'A-102',1),
('A3','A',22,3,'A-103',1),
('A4','A',22,4,'A-104',1),
('A5','A',22,5,'A-105',1),
('A6','A',22,6,'A-106',1),
('A7','A',22,7,'A-107',1),
('A8','A',22,8,'A-108',1),
('A9','A',22,9,'A-109',1),
('E1','E',22,1,'A-110',1),
('E2','E',22,2,'A-111',1),
('E3','E',22,3,'A-112',1),
('E4','E',22,4,'A-113',1),
('E5','E',22,5,'A-114',1),
('E6','E',22,6,'A-115',1),
('E7','E',22,7,'A-116',1),
('E8','E',22,8,'A-117',1),
('E9','E',22,9,'A-118',1),
('SLS','SLS',22,10,'A-LAB-STAM',1),

-- Year 2
('M1','M',22,1,'A-201',2),
('M2','M',22,2,'A-202',2),
('M3','M',22,3,'A-203',2),
('M4','M',22,4,'A-204',2),
('M5','M',22,5,'A-205',2),
('M6','M',22,6,'A-206',2),
('M7','M',22,7,'A-207',2),
('M8','M',22,8,'A-208',2),
('M9','M',22,9,'A-209',2),
('A1','A',22,1,'A-201',2),
('A2','A',22,2,'A-202',2),
('A3','A',22,3,'A-203',2),
('A4','A',22,4,'A-204',2),
('A5','A',22,5,'A-205',2),
('A6','A',22,6,'A-206',2),
('A7','A',22,7,'A-207',2),
('A8','A',22,8,'A-208',2),
('A9','A',22,9,'A-209',2),
('E1','E',22,1,'A-201',2),
('E2','E',22,2,'A-202',2),
('E3','E',22,3,'A-203',2),
('E4','E',22,4,'A-204',2),
('E5','E',22,5,'A-205',2),
('E6','E',22,6,'A-206',2),
('E7','E',22,7,'A-207',2),
('E8','E',22,8,'A-208',2),
('E9','E',22,9,'A-209',2),
('SLS','SLS',22,10,'A-LAB-STAM',2),

-- Year 3
('M1','M',22,1,'A-301',3),
('M2','M',22,2,'A-302',3),
('M3','M',22,3,'A-303',3),
('M4','M',22,4,'A-304',3),
('M5','M',22,5,'A-305',3),
('M6','M',22,6,'A-306',3),
('M7','M',22,7,'A-307',3),
('M8','M',22,8,'A-308',3),
('M9','M',22,9,'A-309',3),
('A1','A',22,1,'A-301',3),
('A2','A',22,2,'A-302',3),
('A3','A',22,3,'A-303',3),
('A4','A',22,4,'A-304',3),
('A5','A',22,5,'A-305',3),
('A6','A',22,6,'A-306',3),
('A7','A',22,7,'A-307',3),
('A8','A',22,8,'A-308',3),
('A9','A',22,9,'A-309',3),
('E1','E',22,1,'A-301',3),
('E2','E',22,2,'A-302',3),
('E3','E',22,3,'A-303',3),
('E4','E',22,4,'A-304',3),
('E5','E',22,5,'A-305',3),
('E6','E',22,6,'A-306',3),
('E7','E',22,7,'A-307',3),
('E8','E',22,8,'A-308',3),
('E9','E',22,9,'A-309',3),
('SLS','SLS',22,10,'A-LAB-STAM',3),

-- Year 4
('M1','M',22,1,'A-401',4),
('M2','M',22,2,'A-402',4),
('M3','M',22,3,'A-403',4),
('M4','M',22,4,'A-404',4),
('M5','M',22,5,'A-405',4),
('M6','M',22,6,'A-406',4),
('M7','M',22,7,'A-407',4),
('M8','M',22,8,'A-408',4),
('M9','M',22,9,'A-409',4),
('A1','A',22,1,'A-401',4),
('A2','A',22,2,'A-402',4),
('A3','A',22,3,'A-403',4),
('A4','A',22,4,'A-404',4),
('A5','A',22,5,'A-405',4),
('A6','A',22,6,'A-406',4),
('A7','A',22,7,'A-407',4),
('A8','A',22,8,'A-408',4),
('A9','A',22,9,'A-409',4),
('E1','E',22,1,'A-401',4),
('E2','E',22,2,'A-402',4),
('E3','E',22,3,'A-403',4),
('E4','E',22,4,'A-404',4),
('E5','E',22,5,'A-405',4),
('E6','E',22,6,'A-406',4),
('E7','E',22,7,'A-407',4),
('E8','E',22,8,'A-408',4),
('E9','E',22,9,'A-409',4),
('SLS','SLS',22,10,'A-LAB-STAM',4);

SET @OLD_SQL_SAFE_UPDATES_FOR_CLASS_FIX := @@SQL_SAFE_UPDATES;
SET SQL_SAFE_UPDATES = 0;

UPDATE classes c
LEFT JOIN rooms r ON c.room_id = r.id
SET c.building_id = r.building_id
WHERE c.building_id IS NULL;

SET SQL_SAFE_UPDATES = @OLD_SQL_SAFE_UPDATES_FOR_CLASS_FIX;

INSERT INTO subjects (subject_name, department_id, year_id, semester, credits) VALUES
-- Information Technology (Department 22)
('Introduction to Computer Science', 22, 1, 1, 3), ('Programming in C/C++', 22, 1, 2, 3), 
('Data Structures and Algorithms', 22, 2, 1, 3), ('Database Management Systems', 22, 2, 1, 3), 
('Web Development (HTML/CSS/JS)', 22, 2, 2, 3), ('Computer Networks', 22, 3, 1, 3), 
('Software Engineering', 22, 3, 2, 3), ('Mobile App Development', 22, 3, 1, 3),
('Cloud Computing', 22, 4, 1, 3), ('Cybersecurity Fundamentals', 22, 4, 2, 3),
('Artificial Intelligence', 22, 3, 2, 3), ('Machine Learning', 22, 4, 1, 3),

-- English (Department 34)
('Core English I', 34, 1, 1, 3), ('Core English II', 34, 1, 2, 3), 
('Speaking and Listening Skills', 34, 2, 1, 3), ('Academic Writing', 34, 2, 2, 3), 
('Translation and Interpretation', 34, 3, 1, 3), ('Business English', 34, 3, 2, 3),
('English Literature', 34, 3, 1, 3), ('Advanced English', 34, 4, 2, 3),

-- Khmer Literature (Department 1)
('ប្រវត្តិអក្សរសាស្ត្រខ្មែរ', 1, 1, 1, 3), ('វេយ្យាករណ៍ខ្មែរ', 1, 1, 2, 3), 
('កំណាព្យខ្មែរ', 1, 2, 1, 3), ('អក្សរសិល្ព៍ប្រជាប្រិយ', 1, 2, 2, 3),
('ប្រវត្តិសាស្ត្រខ្មែរ (History of Cambodia)', 1, 1, 1, 2), 
('ទស្សនវិជ្ជា (Philosophy)', 1, 1, 2, 2), ('ភាសាខ្មែរបឋម', 1, 1, 1, 2),

-- Mathematics (Department 18)
('Calculus I', 18, 1, 1, 4), ('Linear Algebra', 18, 1, 2, 4),
('Calculus II', 18, 2, 1, 4), ('Differential Equations', 18, 2, 2, 4),
('Advanced Mathematics', 18, 3, 1, 3), ('Numerical Methods', 18, 3, 2, 3),
('Statistics and Probability', 18, 2, 1, 3), ('Abstract Algebra', 18, 3, 2, 3),

-- Physics (Department 19)
('Physics I: Mechanics', 19, 1, 1, 4), ('Physics II: Electricity and Magnetism', 19, 1, 2, 4),
('Physics III: Waves and Optics', 19, 2, 1, 4), ('Modern Physics', 19, 2, 2, 4),
('Thermodynamics', 19, 1, 2, 3), ('Applied Physics', 19, 3, 1, 3),

-- Biology (Department 20)
('General Biology I', 20, 1, 1, 4), ('General Biology II', 20, 1, 2, 4),
('Molecular Biology', 20, 2, 1, 4), ('Ecology', 20, 2, 2, 3),
('Genetics', 20, 2, 1, 3), ('Microbiology', 20, 3, 1, 3),

-- Chemistry (Department 23)
('General Chemistry I', 23, 1, 1, 4), ('General Chemistry II', 23, 1, 2, 4),
('Organic Chemistry I', 23, 2, 1, 4), ('Organic Chemistry II', 23, 2, 2, 4),
('Analytical Chemistry', 23, 2, 1, 3), ('Biochemistry', 23, 3, 1, 3),

-- Engineering Departments (11-17)
('Structural Analysis', 2, 2, 1, 3), ('Materials Science', 2, 2, 2, 3),
('Thermodynamics for Engineers', 2, 2, 1, 3), ('Fluid Mechanics', 2, 3, 1, 3),
('Electrical Circuits', 2, 1, 2, 3), ('Digital Systems', 2, 1, 2, 3),
('Signal Processing', 2, 3, 1, 3), ('Control Systems', 2, 3, 2, 3),

-- Languages (Departments 35-39)
('French I', 35, 1, 1, 3), ('French II', 35, 1, 2, 3),
('Japanese I', 36, 1, 1, 3), ('Japanese II', 36, 1, 2, 3),
('Korean I', 37, 1, 1, 3), ('Korean II', 37, 1, 2, 3),
('Mandarin I', 38, 1, 1, 3), ('Mandarin II', 38, 1, 2, 3),
('Thai Language I', 39, 1, 1, 3), ('Thai Language II', 39, 1, 2, 3),

-- Business & Social Sciences (1, 24, 25)
('International Business Management', 1, 2, 1, 3), ('Applied Economics', 24, 1, 1, 3),
('Economic Development', 24, 1, 2, 3), ('Community Development', 25, 1, 1, 3),
('Sustainable Development', 25, 2, 1, 3), ('Urban Planning', 27, 2, 1, 3),

-- Education (Departments 28-30)
('Curriculum Design', 28, 1, 1, 3), ('Instructional Methods', 28, 1, 2, 3),
('Educational Psychology', 29, 1, 1, 3), ('Teaching and Learning', 29, 1, 2, 3),
('Higher Education Systems', 30, 2, 1, 3), ('Education Policy', 30, 2, 2, 3),

-- International Studies (Departments 31-33)
('International Relations', 31, 1, 1, 3), ('Diplomacy', 31, 2, 1, 3),
('International Economics', 32, 1, 1, 3), ('Global Trade', 32, 1, 2, 3),
('Political Science', 33, 1, 1, 3), ('Public Administration', 33, 2, 1, 3);

-- Users + profiles+ Admin/Teacher/Student tables
INSERT INTO users (name, email, password, role, status) VALUES
('MKS', 'admin@hitech.edu', '123456', 'Admin', 'Active'),
('Sarah Jenkins', 'teacher@hitech.edu', '123456', 'Teacher', 'Active'),
('Brooklyn Simmons', 'student@hitech.edu', '123456', 'Student', 'Active');

UPDATE user_profiles SET id_number = 'ADM-2026-001', gender = 'Male', phone = '012 345 678', address = 'Phnom Penh' WHERE user_id = 1;
UPDATE user_profiles SET id_number = 'TCH-2026-802', gender = 'Female', department_id = 22, phone = '098 765 432', address = 'Faculty Housing' WHERE user_id = 2;
UPDATE user_profiles SET id_number = 'STU-2026-1024', gender = 'Male', generation_id = 4, department_id = 22, academic_year_id = 2, class_id = 1, phone = '088 111 222', address = 'Dormitory A' WHERE user_id = 3;

INSERT INTO users (name, email, password, role, status) VALUES
('Sok Dara', 'sok.dara@hitech.edu', '123456', 'Student', 'Active'),
('Chan Minea', 'chan.minea@hitech.edu', '123456', 'Student', 'Active'),
('Keo Rotha', 'keo.rotha@hitech.edu', '123456', 'Student', 'Active'),
('Meas Sreyneath', 'meas.sreyneath@hitech.edu', '123456', 'Student', 'Active'),
('Chhorn Sovann', 'chhorn.sovann@hitech.edu', '123456', 'Student', 'Active'),
('Ngeth Sopheak', 'ngeth.sopheak@hitech.edu', '123456', 'Student', 'Active'),
('Phan Bopha', 'phan.bopha@hitech.edu', '123456', 'Student', 'Active'),
('Vong Tola', 'vong.tola@hitech.edu', '123456', 'Student', 'Active'),
('Ly Kimsour', 'ly.kimsour@hitech.edu', '123456', 'Student', 'Active');

UPDATE user_profiles
SET class_id = 1, department_id = 22, academic_year_id = 1, generation_id = 4
WHERE user_id >= 4;

-- Add users to role tables
INSERT INTO admins (user_id, position) VALUES
(1, 'System Administrator');

INSERT INTO teachers (user_id, teacher_code, department_id, subject_teach) VALUES
(2, 'TCH-2026-802', 22, 'Database Management Systems');

INSERT INTO students (user_id, student_code, class_id) VALUES
(3,  'STU-2026-1024', 1),
(4,  'STU-2026-1001', 1),
(5,  'STU-2026-1002', 1),
(6,  'STU-2026-1003', 1),
(7,  'STU-2026-1004', 1),
(8,  'STU-2026-1005', 1),
(9,  'STU-2026-1006', 1),
(10, 'STU-2026-1007', 1),
(11, 'STU-2026-1008', 1),
(12, 'STU-2026-1009', 1);

-- ==========================================
-- 100 Teacher Users (User IDs 13-112)
-- ==========================================
INSERT INTO users (name, email, password, role, status) VALUES
('Teacher 001', 'teacher001@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 002', 'teacher002@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 003', 'teacher003@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 004', 'teacher004@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 005', 'teacher005@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 006', 'teacher006@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 007', 'teacher007@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 008', 'teacher008@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 009', 'teacher009@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 010', 'teacher010@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 011', 'teacher011@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 012', 'teacher012@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 013', 'teacher013@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 014', 'teacher014@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 015', 'teacher015@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 016', 'teacher016@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 017', 'teacher017@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 018', 'teacher018@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 019', 'teacher019@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 020', 'teacher020@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 021', 'teacher021@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 022', 'teacher022@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 023', 'teacher023@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 024', 'teacher024@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 025', 'teacher025@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 026', 'teacher026@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 027', 'teacher027@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 028', 'teacher028@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 029', 'teacher029@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 030', 'teacher030@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 031', 'teacher031@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 032', 'teacher032@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 033', 'teacher033@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 034', 'teacher034@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 035', 'teacher035@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 036', 'teacher036@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 037', 'teacher037@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 038', 'teacher038@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 039', 'teacher039@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 040', 'teacher040@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 041', 'teacher041@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 042', 'teacher042@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 043', 'teacher043@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 044', 'teacher044@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 045', 'teacher045@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 046', 'teacher046@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 047', 'teacher047@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 048', 'teacher048@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 049', 'teacher049@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 050', 'teacher050@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 051', 'teacher051@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 052', 'teacher052@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 053', 'teacher053@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 054', 'teacher054@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 055', 'teacher055@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 056', 'teacher056@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 057', 'teacher057@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 058', 'teacher058@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 059', 'teacher059@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 060', 'teacher060@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 061', 'teacher061@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 062', 'teacher062@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 063', 'teacher063@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 064', 'teacher064@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 065', 'teacher065@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 066', 'teacher066@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 067', 'teacher067@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 068', 'teacher068@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 069', 'teacher069@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 070', 'teacher070@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 071', 'teacher071@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 072', 'teacher072@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 073', 'teacher073@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 074', 'teacher074@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 075', 'teacher075@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 076', 'teacher076@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 077', 'teacher077@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 078', 'teacher078@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 079', 'teacher079@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 080', 'teacher080@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 081', 'teacher081@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 082', 'teacher082@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 083', 'teacher083@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 084', 'teacher084@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 085', 'teacher085@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 086', 'teacher086@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 087', 'teacher087@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 088', 'teacher088@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 089', 'teacher089@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 090', 'teacher090@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 091', 'teacher091@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 092', 'teacher092@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 093', 'teacher093@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 094', 'teacher094@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 095', 'teacher095@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 096', 'teacher096@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 097', 'teacher097@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 098', 'teacher098@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 099', 'teacher099@hitech.edu', '123456', 'Teacher', 'Active'),
('Teacher 100', 'teacher100@hitech.edu', '123456', 'Teacher', 'Active');

INSERT INTO teachers (user_id, teacher_code, department_id, subject_teach) VALUES
(13, 'TCH-2026-001', 22, 'Programming in C/C++'),
(14, 'TCH-2026-002', 22, 'Data Structures and Algorithms'),
(15, 'TCH-2026-003', 22, 'Database Management Systems'),
(16, 'TCH-2026-004', 22, 'Web Development (HTML/CSS/JS)'),
(17, 'TCH-2026-005', 22, 'Computer Networks'),
(18, 'TCH-2026-006', 22, 'Software Engineering'),
(19, 'TCH-2026-007', 34, 'Core English I'),
(20, 'TCH-2026-008', 34, 'Core English II'),
(21, 'TCH-2026-009', 34, 'Speaking and Listening Skills'),
(22, 'TCH-2026-010', 34, 'Academic Writing'),
(23, 'TCH-2026-011', 34, 'Translation and Interpretation'),
(24, 'TCH-2026-012', 1, 'Khmer Literature'),
(25, 'TCH-2026-013', 1, 'Khmer Grammar'),
(26, 'TCH-2026-014', 1, 'Khmer Poetry'),
(27, 'TCH-2026-015', 1, 'Khmer Contemporary Literature'),
(28, 'TCH-2026-016', 1, 'Cambodian History'),
(29, 'TCH-2026-017', 1, 'Philosophy'),
(30, 'TCH-2026-018', 2, 'Biological Engineering'),
(31, 'TCH-2026-019', 2, 'Information Technology Engineering'),
(32, 'TCH-2026-020', 2, 'Electronics Engineering'),
(33, 'TCH-2026-021', 2, 'Telecommunications Engineering'),
(34, 'TCH-2026-022', 2, 'Food Engineering and Technology'),
(35, 'TCH-2026-023', 2, 'Data Science Engineering'),
(36, 'TCH-2026-024', 2, 'Environmental Engineering'),
(37, 'TCH-2026-025', 2, 'Automation Engineering'),
(38, 'TCH-2026-026', 3, 'Mathematics'),
(39, 'TCH-2026-027', 3, 'Physics'),
(40, 'TCH-2026-028', 3, 'Biology'),
(41, 'TCH-2026-029', 3, 'Environmental Science'),
(42, 'TCH-2026-030', 3, 'Information Technology'),
(43, 'TCH-2026-031', 3, 'Chemistry'),
(44, 'TCH-2026-032', 4, 'Economic Development'),
(45, 'TCH-2026-033', 4, 'Community Development'),
(46, 'TCH-2026-034', 4, 'Natural Resources Management'),
(47, 'TCH-2026-035', 4, 'Urban Planning'),
(48, 'TCH-2026-036', 5, 'Lifelong Education'),
(49, 'TCH-2026-037', 5, 'Educational Theory'),
(50, 'TCH-2026-038', 5, 'Higher Education Management'),
(51, 'TCH-2026-039', 6, 'International Relations'),
(52, 'TCH-2026-040', 6, 'International Economy'),
(53, 'TCH-2026-041', 6, 'Political Science'),
(54, 'TCH-2026-042', 7, 'English Language'),
(55, 'TCH-2026-043', 7, 'French Language'),
(56, 'TCH-2026-044', 7, 'Japanese Language'),
(57, 'TCH-2026-045', 7, 'Korean Language'),
(58, 'TCH-2026-046', 7, 'Chinese Language'),
(59, 'TCH-2026-047', 7, 'Thai Language'),
(60, 'TCH-2026-048', 22, 'Introduction to Computer Science'),
(61, 'TCH-2026-049', 1, 'Geography and Land Management'),
(62, 'TCH-2026-050', 1, 'Psychology'),
(63, 'TCH-2026-051', 1, 'Sociology'),
(64, 'TCH-2026-052', 1, 'Communication Media'),
(65, 'TCH-2026-053', 1, 'Tourism'),
(66, 'TCH-2026-054', 1, 'Linguistics'),
(67, 'TCH-2026-055', 1, 'International Business Management'),
(68, 'TCH-2026-056', 2, 'Supply Chain Engineering'),
(69, 'TCH-2026-057', 3, 'Advanced Mathematics'),
(70, 'TCH-2026-058', 3, 'Applied Physics'),
(71, 'TCH-2026-059', 3, 'Molecular Biology'),
(72, 'TCH-2026-060', 22, 'Advanced Algorithms'),
(73, 'TCH-2026-061', 22, 'Cloud Computing'),
(74, 'TCH-2026-062', 22, 'Cybersecurity'),
(75, 'TCH-2026-063', 22, 'Artificial Intelligence'),
(76, 'TCH-2026-064', 22, 'Machine Learning'),
(77, 'TCH-2026-065', 34, 'Business English'),
(78, 'TCH-2026-066', 34, 'Technical English'),
(79, 'TCH-2026-067', 34, 'Advanced English'),
(80, 'TCH-2026-068', 34, 'English Literature'),
(81, 'TCH-2026-069', 7, 'Spanish Language'),
(82, 'TCH-2026-070', 7, 'German Language'),
(83, 'TCH-2026-071', 7, 'Italian Language'),
(84, 'TCH-2026-072', 7, 'Portuguese Language'),
(85, 'TCH-2026-073', 1, 'Modern Cambodian History'),
(86, 'TCH-2026-074', 1, 'World History'),
(87, 'TCH-2026-075', 1, 'Cultural Studies'),
(88, 'TCH-2026-076', 2, 'Mechanical Engineering'),
(89, 'TCH-2026-077', 2, 'Civil Engineering'),
(90, 'TCH-2026-078', 2, 'Chemical Engineering'),
(91, 'TCH-2026-079', 3, 'Biochemistry'),
(92, 'TCH-2026-080', 3, 'Microbiology'),
(93, 'TCH-2026-081', 3, 'Ecology'),
(94, 'TCH-2026-082', 4, 'Sustainable Development'),
(95, 'TCH-2026-083', 5, 'Curriculum Design'),
(96, 'TCH-2026-084', 5, 'Instructional Technology'),
(97, 'TCH-2026-085', 6, 'Diplomacy and International Law'),
(98, 'TCH-2026-086', 6, 'Global Economics'),
(99, 'TCH-2026-087', 22, 'Mobile App Development'),
(100, 'TCH-2026-088', 22, 'Game Development'),
(101, 'TCH-2026-089', 22, 'Web Services and APIs'),
(102, 'TCH-2026-090', 22, 'DevOps and System Administration'),
(103, 'TCH-2026-091', 34, 'Language Skills Workshop'),
(104, 'TCH-2026-092', 34, 'Communication Workshop'),
(105, 'TCH-2026-093', 1, 'Seminar Series'),
(106, 'TCH-2026-094', 2, 'Advanced Engineering Workshop'),
(107, 'TCH-2026-095', 3, 'Research Methodology'),
(108, 'TCH-2026-096', 4, 'Development Projects'),
(109, 'TCH-2026-097', 5, 'Teaching Practice'),
(110, 'TCH-2026-098', 6, 'Seminar in International Studies'),
(111, 'TCH-2026-099', 7, 'Language Integration'),
(112, 'TCH-2026-100', 22, 'Capstone Project');

-- ==========================================
-- 100 Student Users
-- ==========================================
INSERT INTO users (name, email, password, role, status)
SELECT
    CONCAT('Student ', LPAD(nums.n, 3, '0')),
    CONCAT('student', LPAD(nums.n, 3, '0'), '@hitech.edu'),
    '123456',
    'Student',
    'Active'
FROM (
    SELECT (ones.d + tens.d * 10 + 1) AS n
    FROM
        (SELECT 0 AS d UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
         UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) ones
    CROSS JOIN
        (SELECT 0 AS d UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
         UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) tens
    WHERE (ones.d + tens.d * 10) < 100
) nums
ORDER BY nums.n;

-- Safe update mode compatibility (Workbench SQL_SAFE_UPDATES)
SET @OLD_SQL_SAFE_UPDATES := @@SQL_SAFE_UPDATES;
SET SQL_SAFE_UPDATES = 0;

UPDATE user_profiles up
JOIN users u ON u.id = up.user_id
SET
    up.id_number = CONCAT('STU-2026-', LPAD(CAST(SUBSTRING(u.email, 8, 3) AS UNSIGNED) + 1100, 4, '0')),
    up.department_id = 22,
    up.academic_year_id = 1,
    up.class_id = 1,
    up.generation_id = 4
WHERE u.email REGEXP '^student[0-9]{3}@hitech\\.edu$';

SET SQL_SAFE_UPDATES = @OLD_SQL_SAFE_UPDATES;

INSERT INTO students (user_id, student_code, class_id)
SELECT
    u.id,
    CONCAT('STU-2026-', LPAD(CAST(SUBSTRING(u.email, 8, 3) AS UNSIGNED) + 1100, 4, '0')),
    1
FROM users u
WHERE u.email REGEXP '^student[0-9]{3}@hitech\\.edu$';

-- ==========================================
-- 6) Procedure: Generate rooms for Building A
-- ==========================================
DELIMITER //
CREATE PROCEDURE generate_rooms_for_building_A()
BEGIN
    DECLARE f INT DEFAULT 1;
    DECLARE r INT DEFAULT 1;
    DECLARE room_num VARCHAR(10);
    DECLARE r_type VARCHAR(50);
    DECLARE r_name VARCHAR(100);

    WHILE f <= 6 DO
        SET r = 1;
        WHILE r <= 12 DO
            SET room_num = CONCAT('A-', f, LPAD(r, 2, '0'));

            IF r = 12 THEN
                SET r_type = 'Computer Lab';
                CASE f
                    WHEN 2 THEN SET r_name = 'Computer Lab B';
                    WHEN 3 THEN SET r_name = 'Computer Lab C';
                    WHEN 4 THEN SET r_name = 'Computer Lab D';
                    WHEN 5 THEN SET r_name = 'Computer Lab T';
                    WHEN 6 THEN SET r_name = 'Computer Lab STAM';
                    ELSE SET r_name = CONCAT('IT Lab Floor ', f);
                END CASE;
            ELSE
                SET r_type = 'Classroom';
                SET r_name = CONCAT('General Classroom ', room_num);
            END IF;

            INSERT IGNORE INTO rooms (building_id, room_number, room_name, floor, room_type)
            VALUES (1, room_num, r_name, f, r_type);

            SET r = r + 1;
        END WHILE;
        SET f = f + 1;
    END WHILE;
END //
DELIMITER ;

-- ==========================================
-- Execute room generation before timetable inserts
-- ==========================================
CALL generate_rooms_for_building_A();

-- ==========================================
-- បញ្ចូលទិន្នន័យកាលវិភាគរៀន (Full Timetable Insert)
-- ==========================================

-- លុបទិន្នន័យកាលវិភាគចាស់ចោលសិន ដើម្បីកុំឱ្យជាន់គ្នា
TRUNCATE TABLE timetable;

INSERT INTO timetable (department_id, academic_year_id, class_id, subject_id, semester, subject_name, day_of_week, start_time, end_time, room_id, teacher_id) VALUES

-- ឆ្នាំទី ១ (Year 1) - វេនព្រឹក (Morning) - ថ្នាក់ M1
(22, 1, 1, 1, 1, 'Introduction to Computer Science', 'Monday', '07:30:00', '09:00:00', 1, 2),
(22, 1, 1, 2, 1, 'Programming in C/C++', 'Monday', '09:30:00', '11:00:00', 1, 13),
(22, 1, 1, 13, 1, 'Core English I', 'Tuesday', '07:30:00', '09:00:00', 2, 19),
(22, 1, 1, 28, 1, 'Calculus I', 'Tuesday', '09:30:00', '11:00:00', 2, 38),
(22, 1, 1, 1, 1, 'Introduction to Computer Science', 'Wednesday', '07:30:00', '09:00:00', 1, 2),
(22, 1, 1, 2, 1, 'Programming in C/C++', 'Wednesday', '09:30:00', '11:00:00', 1, 13),
(22, 1, 1, 13, 1, 'Core English I', 'Thursday', '07:30:00', '09:00:00', 2, 19),
(22, 1, 1, 28, 1, 'Calculus I', 'Thursday', '09:30:00', '11:00:00', 2, 38),
(22, 1, 1, 36, 1, 'Physics I: Mechanics', 'Friday', '07:30:00', '09:00:00', 3, 39),
(22, 1, 1, 21, 1, 'ប្រវត្តិអក្សរសាស្ត្រខ្មែរ', 'Friday', '09:30:00', '11:00:00', 3, 24),

-- ឆ្នាំទី ១ (Year 1) - វេនរសៀល (Afternoon) - ថ្នាក់ A1
(22, 1, 10, 1, 1, 'Introduction to Computer Science', 'Monday', '13:30:00', '15:00:00', 4, 2),
(22, 1, 10, 2, 1, 'Programming in C/C++', 'Monday', '15:30:00', '17:00:00', 4, 13),
(22, 1, 10, 13, 1, 'Core English I', 'Tuesday', '13:30:00', '15:00:00', 5, 19),
(22, 1, 10, 28, 1, 'Calculus I', 'Tuesday', '15:30:00', '17:00:00', 5, 38),
(22, 1, 10, 1, 1, 'Introduction to Computer Science', 'Wednesday', '13:30:00', '15:00:00', 4, 2),
(22, 1, 10, 2, 1, 'Programming in C/C++', 'Wednesday', '15:30:00', '17:00:00', 4, 13),
(22, 1, 10, 13, 1, 'Core English I', 'Thursday', '13:30:00', '15:00:00', 5, 19),
(22, 1, 10, 28, 1, 'Calculus I', 'Thursday', '15:30:00', '17:00:00', 5, 38),
(22, 1, 10, 36, 1, 'Physics I: Mechanics', 'Friday', '13:30:00', '15:00:00', 6, 39),

-- ឆ្នាំទី ១ (Year 1) - វេនយប់ (Evening) - ថ្នាក់ E1
(22, 1, 19, 1, 1, 'Introduction to Computer Science', 'Monday', '17:30:00', '19:00:00', 11, 2),
(22, 1, 19, 2, 1, 'Programming in C/C++', 'Monday', '19:15:00', '20:45:00', 11, 13),
(22, 1, 19, 13, 1, 'Core English I', 'Tuesday', '17:30:00', '19:00:00', 12, 19),
(22, 1, 19, 28, 1, 'Calculus I', 'Tuesday', '19:15:00', '20:45:00', 12, 38),
(22, 1, 19, 1, 1, 'Introduction to Computer Science', 'Wednesday', '17:30:00', '19:00:00', 11, 2),
(22, 1, 19, 2, 1, 'Programming in C/C++', 'Wednesday', '19:15:00', '20:45:00', 11, 13),
(22, 1, 19, 13, 1, 'Core English I', 'Thursday', '17:30:00', '19:00:00', 12, 19),
(22, 1, 19, 28, 1, 'Calculus I', 'Thursday', '19:15:00', '20:45:00', 12, 38),
(22, 1, 19, 36, 1, 'Physics I: Mechanics', 'Friday', '17:30:00', '19:00:00', 13, 39),

-- ឆ្នាំទី ១ (Year 1) - SLS
(22, 1, 28, 1, 1, 'Introduction to Computer Science', 'Saturday', '08:00:00', '11:00:00', 10, 2),
(22, 1, 28, 2, 1, 'Programming in C/C++', 'Saturday', '13:00:00', '16:00:00', 10, 13),
(22, 1, 28, 13, 1, 'Core English I', 'Sunday', '08:00:00', '11:00:00', 10, 19),
(22, 1, 28, 28, 1, 'Calculus I', 'Sunday', '13:00:00', '16:00:00', 10, 38),

-- ឆ្នាំទី ២ (Year 2) - M1
(22, 2, 29, 3, 1, 'Data Structures and Algorithms', 'Monday', '07:30:00', '09:00:00', 20, 14),
(22, 2, 29, 4, 1, 'Database Management Systems', 'Monday', '09:30:00', '11:00:00', 20, 15),
(22, 2, 29, 5, 1, 'Web Development (HTML/CSS/JS)', 'Tuesday', '07:30:00', '09:00:00', 21, 16),
(22, 2, 29, 15, 1, 'Speaking and Listening Skills', 'Tuesday', '09:30:00', '11:00:00', 21, 21),
(22, 2, 29, 3, 1, 'Data Structures and Algorithms', 'Wednesday', '07:30:00', '09:00:00', 20, 14),
(22, 2, 29, 4, 1, 'Database Management Systems', 'Wednesday', '09:30:00', '11:00:00', 20, 15),
(22, 2, 29, 5, 1, 'Web Development (HTML/CSS/JS)', 'Thursday', '07:30:00', '09:00:00', 21, 16),
(22, 2, 29, 15, 1, 'Speaking and Listening Skills', 'Thursday', '09:30:00', '11:00:00', 21, 21),
(22, 2, 29, 30, 1, 'Calculus II', 'Friday', '07:30:00', '09:00:00', 22, 27),
(22, 2, 29, 49, 1, 'Organic Chemistry I', 'Friday', '09:30:00', '11:00:00', 22, 30),

-- ឆ្នាំទី ៣ (Year 3) - M1
(22, 3, 57, 6, 1, 'Computer Networks', 'Monday', '07:30:00', '09:00:00', 30, 17),
(22, 3, 57, 7, 1, 'Software Engineering', 'Monday', '09:30:00', '11:00:00', 30, 18),
(22, 3, 57, 8, 1, 'Mobile App Development', 'Tuesday', '07:30:00', '09:00:00', 31, 99),
(22, 3, 57, 17, 1, 'Translation and Interpretation', 'Tuesday', '09:30:00', '11:00:00', 31, 23),
(22, 3, 57, 6, 1, 'Computer Networks', 'Wednesday', '07:30:00', '09:00:00', 30, 17),
(22, 3, 57, 7, 1, 'Software Engineering', 'Wednesday', '09:30:00', '11:00:00', 30, 18),
(22, 3, 57, 8, 1, 'Mobile App Development', 'Thursday', '07:30:00', '09:00:00', 31, 99),
(22, 3, 57, 17, 1, 'Translation and Interpretation', 'Thursday', '09:30:00', '11:00:00', 31, 23),
(22, 3, 57, 32, 1, 'Advanced Mathematics', 'Friday', '07:30:00', '09:00:00', 32, 69),

-- ឆ្នាំទី ៤ (Year 4) - M1
(22, 4, 85, 9, 1, 'Cloud Computing', 'Monday', '07:30:00', '09:00:00', 40, 73),
(22, 4, 85, 10, 1, 'Cybersecurity Fundamentals', 'Monday', '09:30:00', '11:00:00', 40, 74),
(22, 4, 85, 11, 1, 'Artificial Intelligence', 'Tuesday', '07:30:00', '09:00:00', 41, 75),
(22, 4, 85, 12, 1, 'Machine Learning', 'Tuesday', '09:30:00', '11:00:00', 41, 76),
(22, 4, 85, 9, 1, 'Cloud Computing', 'Wednesday', '07:30:00', '09:00:00', 40, 73),
(22, 4, 85, 10, 1, 'Cybersecurity Fundamentals', 'Wednesday', '09:30:00', '11:00:00', 40, 74),
(22, 4, 85, 11, 1, 'Artificial Intelligence', 'Thursday', '07:30:00', '09:00:00', 41, 75),
(22, 4, 85, 12, 1, 'Machine Learning', 'Thursday', '09:30:00', '11:00:00', 41, 76),
(22, 4, 85, 20, 1, 'Advanced English', 'Friday', '07:30:00', '09:00:00', 42, 79);

-- Teacher 2 extra schedule data for morning/evening test
INSERT INTO timetable (department_id, academic_year_id, class_id, subject_id, semester, subject_name, day_of_week, start_time, end_time, room_id, teacher_id) VALUES
(22, 2, 30, 3, 1, 'Data Structures and Algorithms', 'Monday', '13:30:00', '15:00:00', 20, 2),
(22, 2, 30, 3, 1, 'Data Structures and Algorithms', 'Wednesday', '13:30:00', '15:00:00', 20, 2),
(22, 2, 47, 4, 1, 'Database Management Systems', 'Tuesday', '17:30:00', '19:00:00', 23, 2),
(22, 2, 47, 4, 1, 'Database Management Systems', 'Thursday', '17:30:00', '19:00:00', 23, 2),
(22, 2, 30, 5, 1, 'Web Development (HTML/CSS/JS)', 'Friday', '13:30:00', '15:00:00', 21, 2),
(22, 2, 47, 15, 1, 'Speaking and Listening Skills', 'Friday', '17:30:00', '19:00:00', 24, 2);

INSERT INTO support_tickets (user_id, subject, category, priority, description, status) VALUES
(3, 'ភ្លេចលេខសម្ងាត់ WiFi', 'Account Access', 'Medium', 'ខ្ញុំមិនអាចភ្ជាប់ WiFi នៅក្នុងបណ្ណាល័យបានទេ', 'Open');

-- Attendance sample (10 days x 10 students = 100 rows)
INSERT IGNORE INTO attendance (student_id, class_id, subject_id, teacher_id, attendance_date, status, remarks) VALUES
(3, 1, 1, 2, '2026-02-16', 'Present', ''), (4, 1, 1, 2, '2026-02-16', 'Present', ''), (5, 1, 1, 2, '2026-02-16', 'Late', 'ស្ទះចរាចរណ៍'), (6, 1, 1, 2, '2026-02-16', 'Present', ''), (7, 1, 1, 2, '2026-02-16', 'Present', ''), (8, 1, 1, 2, '2026-02-16', 'Excused', 'ឈឺផ្ដាសាយ'), (9, 1, 1, 2, '2026-02-16', 'Present', ''), (10, 1, 1, 2, '2026-02-16', 'Present', ''), (11, 1, 1, 2, '2026-02-16', 'Absent', ''), (12, 1, 1, 2, '2026-02-16', 'Present', ''),
(3, 1, 1, 2, '2026-02-17', 'Present', ''), (4, 1, 1, 2, '2026-02-17', 'Present', ''), (5, 1, 1, 2, '2026-02-17', 'Present', ''), (6, 1, 1, 2, '2026-02-17', 'Present', ''), (7, 1, 1, 2, '2026-02-17', 'Late', 'ម៉ូតូខូច'), (8, 1, 1, 2, '2026-02-17', 'Excused', 'សុំច្បាប់ទៅស្រុក'), (9, 1, 1, 2, '2026-02-17', 'Present', ''), (10, 1, 1, 2, '2026-02-17', 'Present', ''), (11, 1, 1, 2, '2026-02-17', 'Present', ''), (12, 1, 1, 2, '2026-02-17', 'Present', ''),
(3, 1, 1, 2, '2026-02-18', 'Present', ''), (4, 1, 1, 2, '2026-02-18', 'Absent', ''), (5, 1, 1, 2, '2026-02-18', 'Present', ''), (6, 1, 1, 2, '2026-02-18', 'Present', ''), (7, 1, 1, 2, '2026-02-18', 'Present', ''), (8, 1, 1, 2, '2026-02-18', 'Present', ''), (9, 1, 1, 2, '2026-02-18', 'Late', ''), (10, 1, 1, 2, '2026-02-18', 'Present', ''), (11, 1, 1, 2, '2026-02-18', 'Present', ''), (12, 1, 1, 2, '2026-02-18', 'Excused', 'ជាប់ធុរៈគ្រួសារ'),
(3, 1, 1, 2, '2026-02-19', 'Present', ''), (4, 1, 1, 2, '2026-02-19', 'Present', ''), (5, 1, 1, 2, '2026-02-19', 'Present', ''), (6, 1, 1, 2, '2026-02-19', 'Absent', ''), (7, 1, 1, 2, '2026-02-19', 'Present', ''), (8, 1, 1, 2, '2026-02-19', 'Present', ''), (9, 1, 1, 2, '2026-02-19', 'Present', ''), (10, 1, 1, 2, '2026-02-19', 'Present', ''), (11, 1, 1, 2, '2026-02-19', 'Late', ''), (12, 1, 1, 2, '2026-02-19', 'Present', ''),
(3, 1, 1, 2, '2026-02-20', 'Present', ''), (4, 1, 1, 2, '2026-02-20', 'Present', ''), (5, 1, 1, 2, '2026-02-20', 'Excused', 'ឈឺ'), (6, 1, 1, 2, '2026-02-20', 'Present', ''), (7, 1, 1, 2, '2026-02-20', 'Present', ''), (8, 1, 1, 2, '2026-02-20', 'Present', ''), (9, 1, 1, 2, '2026-02-20', 'Present', ''), (10, 1, 1, 2, '2026-02-20', 'Absent', ''), (11, 1, 1, 2, '2026-02-20', 'Present', ''), (12, 1, 1, 2, '2026-02-20', 'Present', ''),
(3, 1, 1, 2, '2026-02-23', 'Present', ''), (4, 1, 1, 2, '2026-02-23', 'Late', 'ភ្លៀងធ្លាក់'), (5, 1, 1, 2, '2026-02-23', 'Present', ''), (6, 1, 1, 2, '2026-02-23', 'Present', ''), (7, 1, 1, 2, '2026-02-23', 'Absent', ''), (8, 1, 1, 2, '2026-02-23', 'Present', ''), (9, 1, 1, 2, '2026-02-23', 'Present', ''), (10, 1, 1, 2, '2026-02-23', 'Present', ''), (11, 1, 1, 2, '2026-02-23', 'Present', ''), (12, 1, 1, 2, '2026-02-23', 'Excused', 'ទៅមន្ទីរពេទ្យ'),
(3, 1, 1, 2, '2026-02-24', 'Present', ''), (4, 1, 1, 2, '2026-02-24', 'Present', ''), (5, 1, 1, 2, '2026-02-24', 'Present', ''), (6, 1, 1, 2, '2026-02-24', 'Present', ''), (7, 1, 1, 2, '2026-02-24', 'Present', ''), (8, 1, 1, 2, '2026-02-24', 'Present', ''), (9, 1, 1, 2, '2026-02-24', 'Present', ''), (10, 1, 1, 2, '2026-02-24', 'Late', ''), (11, 1, 1, 2, '2026-02-24', 'Present', ''), (12, 1, 1, 2, '2026-02-24', 'Present', ''),
(3, 1, 1, 2, '2026-02-25', 'Late', ''), (4, 1, 1, 2, '2026-02-25', 'Present', ''), (5, 1, 1, 2, '2026-02-25', 'Present', ''), (6, 1, 1, 2, '2026-02-25', 'Present', ''), (7, 1, 1, 2, '2026-02-25', 'Present', ''), (8, 1, 1, 2, '2026-02-25', 'Absent', ''), (9, 1, 1, 2, '2026-02-25', 'Present', ''), (10, 1, 1, 2, '2026-02-25', 'Present', ''), (11, 1, 1, 2, '2026-02-25', 'Excused', 'ធ្វើលិខិតឆ្លងដែន'), (12, 1, 1, 2, '2026-02-25', 'Present', ''),
(3, 1, 1, 2, '2026-02-26', 'Present', ''), (4, 1, 1, 2, '2026-02-26', 'Present', ''), (5, 1, 1, 2, '2026-02-26', 'Present', ''), (6, 1, 1, 2, '2026-02-26', 'Present', ''), (7, 1, 1, 2, '2026-02-26', 'Present', ''), (8, 1, 1, 2, '2026-02-26', 'Present', ''), (9, 1, 1, 2, '2026-02-26', 'Present', ''), (10, 1, 1, 2, '2026-02-26', 'Present', ''), (11, 1, 1, 2, '2026-02-26', 'Present', ''), (12, 1, 1, 2, '2026-02-26', 'Present', ''),
(3, 1, 1, 2, '2026-02-27', 'Absent', ''), (4, 1, 1, 2, '2026-02-27', 'Present', ''), (5, 1, 1, 2, '2026-02-27', 'Present', ''), (6, 1, 1, 2, '2026-02-27', 'Late', 'កង់បែកកង់'), (7, 1, 1, 2, '2026-02-27', 'Present', ''), (8, 1, 1, 2, '2026-02-27', 'Present', ''), (9, 1, 1, 2, '2026-02-27', 'Excused', 'ឈឺ'), (10, 1, 1, 2, '2026-02-27', 'Present', ''), (11, 1, 1, 2, '2026-02-27', 'Present', ''), (12, 1, 1, 2, '2026-02-27', 'Present', '');

-- ==========================================
-- 6) Procedure: Generate rooms for Building A
-- Compatibility view for older scripts that reference `building`.
CREATE OR REPLACE VIEW building AS
SELECT
    id,
    building_name AS name,
    room_count
FROM buildings;

-- ==========================================
-- 7) Safe DB Update (Run on Existing school_db)
-- ==========================================
-- Use this section when you want to update schema without dropping data.
-- This block is idempotent and safe to run multiple times.

SET @phone_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'user_profiles'
      AND column_name = 'phone'
);

SET @address_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'user_profiles'
      AND column_name = 'address'
);
SET @sql := IF(@address_exists = 0,
    IF(@phone_exists > 0,
        'ALTER TABLE user_profiles ADD COLUMN address TEXT AFTER phone',
        'ALTER TABLE user_profiles ADD COLUMN address TEXT'
    ),
    'SELECT ''user_profiles.address already exists'''
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ==========================================
-- ស្គ្រីបសម្រាប់បង្កើតសិស្សគ្រប់ដេប៉ាតឺម៉ង់ និងវត្តមានសរុប
-- (Auto-Generate Students for All Departments & Bulk Attendance)
-- ==========================================

-- កំណត់ឱ្យលុប Procedure ចាស់ចោលសិនបើមាន
DROP PROCEDURE IF EXISTS GenerateStudentsForAllDepts;
DROP PROCEDURE IF EXISTS GenerateBulkAttendance;

DELIMITER $$

-- ១. Procedure សម្រាប់បង្កើតសិស្ស ៥នាក់ ចូលគ្រប់ដេប៉ាតឺម៉ង់
CREATE PROCEDURE GenerateStudentsForAllDepts()
BEGIN
    DECLARE done INT DEFAULT 0;
    DECLARE curr_dept_id INT;
    DECLARE curr_dept_name VARCHAR(150);
    DECLARE i INT;
    DECLARE new_user_id INT;
    DECLARE new_code VARCHAR(50);

    -- ទាញយកគ្រប់ដេប៉ាតឺម៉ង់ទាំងអស់មក Loop
    DECLARE dept_cursor CURSOR FOR SELECT id, department_name FROM department;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

    OPEN dept_cursor;

    dept_loop: LOOP
        FETCH dept_cursor INTO curr_dept_id, curr_dept_name;
        IF done = 1 THEN
            LEAVE dept_loop;
        END IF;

        SET i = 1;
        -- បង្កើតសិស្ស ៥ នាក់សម្រាប់ដេប៉ាតឺម៉ង់នីមួយៗ
        WHILE i <= 5 DO
            SET new_code = CONCAT('STU-', curr_dept_id, '-', YEAR(CURDATE()), '-', LPAD(FLOOR(RAND() * 9999), 4, '0'));

            -- ក. បញ្ចូលទៅតារាង users
            INSERT INTO users (name, email, password, role, status)
            VALUES (
                CONCAT('Student ', i, ' (', SUBSTRING(curr_dept_name, 1, 15), ')'),
                CONCAT('stu', curr_dept_id, '_', i, '_', FLOOR(RAND() * 1000), '@hitech.edu'),
                '123456',
                'Student',
                'Active'
            );
            SET new_user_id = LAST_INSERT_ID();

            -- ខ. Update តារាង user_profiles (Trigger បានបង្កើតជួររួចហើយ)
            UPDATE user_profiles
            SET
                id_number = new_code,
                department_id = curr_dept_id,
                academic_year_id = 1, -- កំណត់ឱ្យរៀនឆ្នាំទី ១
                class_id = 1, -- កំណត់ចូលថ្នាក់ទី ១ ជាបណ្តោះអាសន្ន
                gender = IF(RAND() > 0.5, 'Male', 'Female')
            WHERE user_id = new_user_id;

            -- គ. បញ្ចូលទៅតារាង students
            INSERT INTO students (user_id, student_code, class_id)
            VALUES (new_user_id, new_code, 1);

            SET i = i + 1;
        END WHILE;
    END LOOP;

    CLOSE dept_cursor;
END$$


-- ២. Procedure សម្រាប់កត់វត្តមានឱ្យសិស្សទាំងអស់ដោយ Random
CREATE PROCEDURE GenerateBulkAttendance(IN target_date DATE)
BEGIN
    INSERT IGNORE INTO attendance (student_id, class_id, subject_id, teacher_id, attendance_date, status, remarks)
    SELECT
        u.id AS student_id,
        COALESCE(up.class_id, 1) AS class_id,
        -- ព្យាយាមរកមុខវិជ្ជា និងគ្រូតាមដេប៉ាតឺម៉ង់ បើគ្មានទេយកលេខ 1 និងលេខ 2 ជា default
        COALESCE((SELECT subject_id FROM timetable t WHERE t.department_id = up.department_id LIMIT 1), 1) AS subject_id,
        COALESCE((SELECT teacher_id FROM timetable t WHERE t.department_id = up.department_id LIMIT 1), 2) AS teacher_id,
        target_date AS attendance_date,
        -- Random ស្ថានភាព (80% វត្តមាន, 10% អវត្តមាន, 5% យឺត, 5% ច្បាប់)
        CASE
            WHEN RAND() < 0.80 THEN 'Present'
            WHEN RAND() < 0.90 THEN 'Absent'
            WHEN RAND() < 0.95 THEN 'Late'
            ELSE 'Excused'
        END AS status,
        CASE
            WHEN RAND() > 0.95 THEN 'ឈឺគ្រុនក្តៅ'
            WHEN RAND() > 0.90 THEN 'ស្ទះចរាចរណ៍'
            ELSE ''
        END AS remarks
    FROM users u
    JOIN user_profiles up ON u.id = up.user_id
    WHERE u.role = 'Student';
END$$

DELIMITER ;

-- ==========================================
-- ៣. ដំណើរការ (Execute) Procedure ខាងលើ
-- ==========================================

-- ហៅមុខងារបង្កើតសិស្សចូលគ្រប់ដេប៉ា
CALL GenerateStudentsForAllDepts();

-- ហៅមុខងារកត់វត្តមានសម្រាប់ ៥ ថ្ងៃ (លោកអ្នកអាចដូរថ្ងៃខែបានតាមចិត្ត)
CALL GenerateBulkAttendance('2026-03-01');
CALL GenerateBulkAttendance('2026-03-02');
CALL GenerateBulkAttendance('2026-03-03');
CALL GenerateBulkAttendance('2026-03-04');
CALL GenerateBulkAttendance('2026-03-05');

-- អាចរត់កូដនេះដើម្បីមើលលទ្ធផលបាន៖
-- SELECT * FROM users WHERE role = 'Student';
-- SELECT * FROM attendance;

SET FOREIGN_KEY_CHECKS = 1;
SET SQL_SAFE_UPDATES = 1;

SET @dob_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'user_profiles'
      AND column_name = 'dob'
);
SET @sql := IF(@dob_exists = 0,
    IF(@address_exists > 0,
        'ALTER TABLE user_profiles ADD COLUMN dob DATE NULL AFTER address',
        'ALTER TABLE user_profiles ADD COLUMN dob DATE NULL'
    ),
    'SELECT ''user_profiles.dob already exists'''
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @created_by_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'users'
      AND column_name = 'created_by'
);
SET @sql := IF(@created_by_exists = 0,
    'ALTER TABLE users ADD COLUMN created_by INT NULL AFTER created_at',
    'SELECT ''users.created_by already exists'''
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;