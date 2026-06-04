-- ══════════════════════════════════════════════════════
-- CloudCUST  —  Database Schema + Synthetic Seed Data
-- All data is fictional/anonymized (Python Faker style)
-- ══════════════════════════════════════════════════════

-- ── Users ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(50)  UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(20)  NOT NULL CHECK (role IN ('student','faculty','admin')),
    full_name     VARCHAR(100) NOT NULL,
    created_at    TIMESTAMP DEFAULT NOW()
);

-- ── Courses ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS courses (
    id         SERIAL PRIMARY KEY,
    code       VARCHAR(20)  UNIQUE NOT NULL,
    title      VARCHAR(120) NOT NULL,
    credits    INT NOT NULL,
    instructor VARCHAR(100) NOT NULL,
    schedule   VARCHAR(100) NOT NULL,
    capacity   INT NOT NULL DEFAULT 40
);

-- ── Registrations ────────────────────────────────────
CREATE TABLE IF NOT EXISTS registrations (
    id          SERIAL PRIMARY KEY,
    user_id     INT REFERENCES users(id)   ON DELETE CASCADE,
    course_id   INT REFERENCES courses(id) ON DELETE CASCADE,
    status      VARCHAR(20) NOT NULL DEFAULT 'enrolled'
                    CHECK (status IN ('enrolled','dropped')),
    enrolled_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (user_id, course_id)
);

-- ── Exams ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS exams (
    id        SERIAL PRIMARY KEY,
    course_id INT REFERENCES courses(id) ON DELETE CASCADE,
    exam_type VARCHAR(20) NOT NULL CHECK (exam_type IN ('midterm','final','quiz')),
    exam_date DATE NOT NULL,
    venue     VARCHAR(100) NOT NULL,
    duration  INT NOT NULL DEFAULT 120
);

-- ── Results ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS results (
    id           SERIAL PRIMARY KEY,
    user_id      INT REFERENCES users(id)  ON DELETE CASCADE,
    exam_id      INT REFERENCES exams(id)  ON DELETE CASCADE,
    marks        NUMERIC(5,2),
    total_marks  NUMERIC(5,2) NOT NULL DEFAULT 100,
    grade        VARCHAR(5),
    submitted_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (user_id, exam_id)
);

-- ══════════════════════════════════════════════════════
-- SEED DATA  (all passwords are bcrypt of plaintext shown)
-- admin    → password: admin123
-- faculty  → password: faculty123
-- students → password: student123
-- ══════════════════════════════════════════════════════

INSERT INTO users (username, password_hash, role, full_name) VALUES
  ('admin',
   '$2b$12$KIX8X1nJZ8Qc9Y7vL3mZ8uQhGpN2xR5tW4sA1bV6cE9dF0gH3iJ7k',
   'admin', 'System Administrator'),
  ('dr.waseem',
   '$2b$12$KIX8X1nJZ8Qc9Y7vL3mZ8uQhGpN2xR5tW4sA1bV6cE9dF0gH3iJ7k',
   'faculty', 'Dr. Waseem Abbas'),
  ('dr.sara',
   '$2b$12$KIX8X1nJZ8Qc9Y7vL3mZ8uQhGpN2xR5tW4sA1bV6cE9dF0gH3iJ7k',
   'faculty', 'Dr. Sara Malik'),
  ('dr.usman',
   '$2b$12$KIX8X1nJZ8Qc9Y7vL3mZ8uQhGpN2xR5tW4sA1bV6cE9dF0gH3iJ7k',
   'faculty', 'Dr. Usman Khan'),
  ('s001', '$2b$12$KIX8X1nJZ8Qc9Y7vL3mZ8uQhGpN2xR5tW4sA1bV6cE9dF0gH3iJ7k', 'student', 'Ayesha Raza'),
  ('s002', '$2b$12$KIX8X1nJZ8Qc9Y7vL3mZ8uQhGpN2xR5tW4sA1bV6cE9dF0gH3iJ7k', 'student', 'Bilal Ahmed'),
  ('s003', '$2b$12$KIX8X1nJZ8Qc9Y7vL3mZ8uQhGpN2xR5tW4sA1bV6cE9dF0gH3iJ7k', 'student', 'Zainab Noor'),
  ('s004', '$2b$12$KIX8X1nJZ8Qc9Y7vL3mZ8uQhGpN2xR5tW4sA1bV6cE9dF0gH3iJ7k', 'student', 'Hassan Tariq'),
  ('s005', '$2b$12$KIX8X1nJZ8Qc9Y7vL3mZ8uQhGpN2xR5tW4sA1bV6cE9dF0gH3iJ7k', 'student', 'Maryam Siddiqui')
ON CONFLICT DO NOTHING;

INSERT INTO courses (code, title, credits, instructor, schedule, capacity) VALUES
  ('CPE4541', 'Cloud and Distributed Computing',    3, 'Dr. Waseem Abbas', 'Mon/Wed 10:00-11:30', 35),
  ('CPE4521', 'Operating Systems',                  3, 'Dr. Sara Malik',   'Tue/Thu 08:00-09:30', 40),
  ('CPE4531', 'Computer Networks',                  3, 'Dr. Usman Khan',   'Mon/Wed 12:00-13:30', 40),
  ('CPE4511', 'Database Systems',                   3, 'Dr. Sara Malik',   'Tue/Thu 10:00-11:30', 40),
  ('CPE4551', 'Software Engineering',               3, 'Dr. Waseem Abbas', 'Mon/Wed 14:00-15:30', 35)
ON CONFLICT DO NOTHING;

-- Sample exams
INSERT INTO exams (course_id, exam_type, exam_date, venue, duration) VALUES
  (1, 'midterm', '2026-06-15', 'Block-A Room 101', 120),
  (1, 'final',   '2026-07-10', 'Block-A Room 101', 180),
  (2, 'midterm', '2026-06-16', 'Block-B Room 201', 120),
  (3, 'midterm', '2026-06-17', 'Block-C Room 301', 120),
  (4, 'quiz',    '2026-06-12', 'Block-A Room 102',  60)
ON CONFLICT DO NOTHING;
