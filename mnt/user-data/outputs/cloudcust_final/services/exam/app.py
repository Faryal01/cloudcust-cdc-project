"""
CloudCUST — Examination Service  (Port 5003)
Endpoints: GET /health  GET /exams  GET /my-exams  GET /results  POST /grades/publish
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2, psycopg2.extras, requests, os, time

app = Flask(__name__)
CORS(app)

DB_URL           = os.environ.get("DATABASE_URL",       "postgresql://cloudcust:cloudcust123@db:5432/cloudcust")
AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL",   "http://auth-service:5001")

def get_db():
    for attempt in range(10):
        try:
            return psycopg2.connect(DB_URL)
        except Exception:
            time.sleep(3)
    raise RuntimeError("Cannot connect to database")

def verify_token(req):
    header = req.headers.get("Authorization","")
    if not header.startswith("Bearer "):
        return None, "Missing token"
    try:
        resp = requests.post(f"{AUTH_SERVICE_URL}/verify",
                             json={"token": header.split(" ",1)[1]}, timeout=3)
        data = resp.json()
        return (data["payload"], None) if data.get("valid") else (None, data.get("error","Invalid"))
    except Exception:
        return None, "Auth service unreachable"

def calc_grade(marks, total):
    pct = (marks / total) * 100
    if pct >= 85: return "A"
    if pct >= 75: return "B"
    if pct >= 65: return "C"
    if pct >= 50: return "D"
    return "F"

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "exam"}), 200

@app.route("/exams")
def list_exams():
    payload, err = verify_token(request)
    if err: return jsonify({"error": err}), 401
    try:
        conn = get_db(); cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT e.id, c.code, c.title, e.exam_type, e.exam_date, e.venue, e.duration
            FROM exams e JOIN courses c ON c.id=e.course_id
            ORDER BY e.exam_date
        """)
        rows = [dict(r) for r in cur.fetchall()]; cur.close(); conn.close()
        return jsonify({"exams": rows}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/my-exams")
def my_exams():
    payload, err = verify_token(request)
    if err: return jsonify({"error": err}), 401
    try:
        conn = get_db(); cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT e.id, c.code, c.title, e.exam_type, e.exam_date, e.venue, e.duration
            FROM exams e
            JOIN courses c ON c.id=e.course_id
            JOIN registrations r ON r.course_id=c.id
            WHERE r.user_id=%s AND r.status='enrolled'
            ORDER BY e.exam_date
        """, (payload["user_id"],))
        rows = [dict(r) for r in cur.fetchall()]; cur.close(); conn.close()
        return jsonify({"exams": rows}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/results")
def results():
    payload, err = verify_token(request)
    if err: return jsonify({"error": err}), 401
    try:
        conn = get_db(); cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT c.code, c.title, e.exam_type, e.exam_date,
                   r.marks, r.total_marks, r.grade, r.submitted_at
            FROM results r
            JOIN exams e ON e.id=r.exam_id
            JOIN courses c ON c.id=e.course_id
            WHERE r.user_id=%s ORDER BY r.submitted_at DESC
        """, (payload["user_id"],))
        rows = [dict(r) for r in cur.fetchall()]; cur.close(); conn.close()
        return jsonify({"results": rows}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/grades/publish", methods=["POST"])
def publish_grade():
    payload, err = verify_token(request)
    if err: return jsonify({"error": err}), 401
    if payload["role"] not in ("faculty","admin"):
        return jsonify({"error": "faculty or admin only"}), 403
    d = request.get_json() or {}
    if not all(k in d for k in ("user_id","exam_id","marks","total_marks")):
        return jsonify({"error": "user_id, exam_id, marks, total_marks required"}), 400
    marks, total = float(d["marks"]), float(d["total_marks"])
    grade = calc_grade(marks, total)
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("""
            INSERT INTO results (user_id,exam_id,marks,total_marks,grade)
            VALUES (%s,%s,%s,%s,%s)
            ON CONFLICT (user_id,exam_id)
            DO UPDATE SET marks=EXCLUDED.marks, grade=EXCLUDED.grade, submitted_at=NOW()
            RETURNING id
        """, (d["user_id"], d["exam_id"], marks, total, grade))
        rid = cur.fetchone()[0]; conn.commit(); cur.close(); conn.close()
        return jsonify({"message": "Grade published", "result_id": rid, "grade": grade}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)
