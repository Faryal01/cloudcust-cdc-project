"""
CloudCUST — Course Registration Service  (Port 5002)
Endpoints: GET /health  GET /courses  POST /enroll  GET /my-courses  POST /drop
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2, psycopg2.extras, requests, os, time

app = Flask(__name__)
CORS(app)

DB_URL           = os.environ.get("DATABASE_URL",     "postgresql://cloudcust:cloudcust123@db:5432/cloudcust")
AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://auth-service:5001")

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
        return None, "Missing or malformed Authorization header"
    try:
        resp = requests.post(f"{AUTH_SERVICE_URL}/verify",
                             json={"token": header.split(" ",1)[1]}, timeout=3)
        data = resp.json()
        return (data["payload"], None) if data.get("valid") else (None, data.get("error","Invalid token"))
    except Exception:
        return None, "Auth service unreachable"

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "course"}), 200

@app.route("/courses")
def list_courses():
    payload, err = verify_token(request)
    if err: return jsonify({"error": err}), 401
    try:
        conn = get_db(); cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT c.id, c.code, c.title, c.credits, c.instructor, c.schedule,
                   c.capacity,
                   c.capacity - COUNT(r.id) FILTER (WHERE r.status='enrolled') AS seats_available
            FROM courses c
            LEFT JOIN registrations r ON r.course_id = c.id
            GROUP BY c.id ORDER BY c.code
        """)
        rows = [dict(r) for r in cur.fetchall()]
        cur.close(); conn.close()
        return jsonify({"courses": rows}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/enroll", methods=["POST"])
def enroll():
    payload, err = verify_token(request)
    if err: return jsonify({"error": err}), 401
    course_id = (request.get_json() or {}).get("course_id")
    if not course_id: return jsonify({"error": "course_id required"}), 400
    user_id = payload["user_id"]
    try:
        conn = get_db(); cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id FROM registrations WHERE user_id=%s AND course_id=%s AND status='enrolled'",
                    (user_id, course_id))
        if cur.fetchone(): return jsonify({"error": "Already enrolled"}), 409
        cur.execute("""
            SELECT c.capacity - COUNT(r.id) FILTER (WHERE r.status='enrolled') AS seats
            FROM courses c LEFT JOIN registrations r ON r.course_id=c.id
            WHERE c.id=%s GROUP BY c.capacity
        """, (course_id,))
        row = cur.fetchone()
        if not row or row["seats"] <= 0: return jsonify({"error": "No seats available"}), 409
        cur.execute("INSERT INTO registrations (user_id,course_id,status) VALUES (%s,%s,'enrolled') RETURNING id",
                    (user_id, course_id))
        reg_id = cur.fetchone()["id"]; conn.commit(); cur.close(); conn.close()
        return jsonify({"message": "Enrolled successfully", "registration_id": reg_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/my-courses")
def my_courses():
    payload, err = verify_token(request)
    if err: return jsonify({"error": err}), 401
    try:
        conn = get_db(); cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT c.code, c.title, c.credits, c.instructor, c.schedule,
                   r.status, r.enrolled_at
            FROM registrations r JOIN courses c ON c.id=r.course_id
            WHERE r.user_id=%s ORDER BY r.enrolled_at DESC
        """, (payload["user_id"],))
        rows = [dict(r) for r in cur.fetchall()]; cur.close(); conn.close()
        return jsonify({"courses": rows}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/drop", methods=["POST"])
def drop():
    payload, err = verify_token(request)
    if err: return jsonify({"error": err}), 401
    course_id = (request.get_json() or {}).get("course_id")
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("UPDATE registrations SET status='dropped' WHERE user_id=%s AND course_id=%s AND status='enrolled'",
                    (payload["user_id"], course_id))
        if cur.rowcount == 0: return jsonify({"error": "Enrollment not found"}), 404
        conn.commit(); cur.close(); conn.close()
        return jsonify({"message": "Course dropped"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
