"""
CloudCUST — Auth Service  (Port 5001)
Endpoints: POST /register  POST /login  POST /verify  GET /health
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2, psycopg2.extras, bcrypt, jwt, os, datetime, time

app = Flask(__name__)
CORS(app)

SECRET_KEY = os.environ.get("JWT_SECRET", "cloudcust_secret_key_2026")
DB_URL     = os.environ.get("DATABASE_URL", "postgresql://cloudcust:cloudcust123@db:5432/cloudcust")

def get_db():
    for attempt in range(10):
        try:
            return psycopg2.connect(DB_URL)
        except Exception:
            time.sleep(3)
    raise RuntimeError("Cannot connect to database")

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "auth"}), 200

@app.route("/register", methods=["POST"])
def register():
    d = request.get_json() or {}
    if not all(k in d for k in ("username","password","role","full_name")):
        return jsonify({"error": "Missing fields: username, password, role, full_name"}), 400
    if d["role"] not in ("student","faculty","admin"):
        return jsonify({"error": "role must be student | faculty | admin"}), 400
    hashed = bcrypt.hashpw(d["password"].encode(), bcrypt.gensalt()).decode()
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username,password_hash,role,full_name) VALUES (%s,%s,%s,%s) RETURNING id",
            (d["username"].strip(), hashed, d["role"], d["full_name"].strip())
        )
        uid = cur.fetchone()[0]; conn.commit(); cur.close(); conn.close()
        return jsonify({"message": "Registered", "user_id": uid}), 201
    except psycopg2.errors.UniqueViolation:
        return jsonify({"error": "Username already exists"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/login", methods=["POST"])
def login():
    d = request.get_json() or {}
    if not all(k in d for k in ("username","password")):
        return jsonify({"error": "username and password required"}), 400
    try:
        conn = get_db(); cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM users WHERE username=%s", (d["username"].strip(),))
        user = cur.fetchone(); cur.close(); conn.close()
        if not user or not bcrypt.checkpw(d["password"].encode(), user["password_hash"].encode()):
            return jsonify({"error": "Invalid credentials"}), 401
        token = jwt.encode({
            "user_id":   user["id"],
            "username":  user["username"],
            "role":      user["role"],
            "full_name": user["full_name"],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)
        }, SECRET_KEY, algorithm="HS256")
        return jsonify({"token": token, "role": user["role"], "full_name": user["full_name"]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/verify", methods=["POST"])
def verify():
    token = (request.get_json() or {}).get("token","")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return jsonify({"valid": True, "payload": payload}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"valid": False, "error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"valid": False, "error": "Invalid token"}), 401

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
