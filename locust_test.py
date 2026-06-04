"""
CloudCUST — Load Testing with Locust
Phase 4, Objective 7: Performance testing and benchmarking

Simulates realistic concurrent user traffic across all three microservices.

Install:  pip install locust
Run:      locust -f monitoring/locust_test.py --host http://localhost
          Then open browser: http://localhost:8089
          Set users=50, spawn rate=5, press Start

For headless (no browser):
    locust -f monitoring/locust_test.py --host http://localhost \
           --users 50 --spawn-rate 5 --run-time 60s --headless \
           --csv monitoring/locust_results
"""

from locust import HttpUser, task, between, events
import random
import json

# ── Seed credentials matching database/init.sql ──────────────────────
STUDENT_CREDS = [
    {"username": "s001", "password": "student123"},
    {"username": "s002", "password": "student123"},
    {"username": "s003", "password": "student123"},
    {"username": "s004", "password": "student123"},
    {"username": "s005", "password": "student123"},
]

FACULTY_CREDS = [
    {"username": "dr.waseem", "password": "faculty123"},
    {"username": "dr.sara",   "password": "faculty123"},
]

COURSE_IDS = [1, 2, 3, 4, 5]


class StudentUser(HttpUser):
    """
    Simulates a student:
    - Logs in
    - Browses courses
    - Enrolls in a course
    - Views their exam schedule
    - Checks their results
    Weight=3 means 3 student users are created for every 1 faculty user.
    """
    wait_time = between(1, 4)   # realistic think time between actions
    weight    = 3

    def on_start(self):
        """Login once at session start."""
        creds = random.choice(STUDENT_CREDS)
        with self.client.post(
            "/api/auth/login",
            json=creds,
            catch_response=True,
            name="POST /api/auth/login"
        ) as resp:
            if resp.status_code == 200:
                self.token = resp.json().get("token", "")
                resp.success()
            else:
                self.token = ""
                resp.failure(f"Login failed: {resp.status_code}")

    def auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def browse_courses(self):
        self.client.get(
            "/api/course/courses",
            headers=self.auth_headers(),
            name="GET /api/course/courses"
        )

    @task(2)
    def view_my_courses(self):
        self.client.get(
            "/api/course/my-courses",
            headers=self.auth_headers(),
            name="GET /api/course/my-courses"
        )

    @task(1)
    def enroll_course(self):
        course_id = random.choice(COURSE_IDS)
        self.client.post(
            "/api/course/enroll",
            json={"course_id": course_id},
            headers=self.auth_headers(),
            name="POST /api/course/enroll"
        )

    @task(2)
    def view_my_exams(self):
        self.client.get(
            "/api/exam/my-exams",
            headers=self.auth_headers(),
            name="GET /api/exam/my-exams"
        )

    @task(2)
    def view_results(self):
        self.client.get(
            "/api/exam/results",
            headers=self.auth_headers(),
            name="GET /api/exam/results"
        )

    @task(1)
    def health_check(self):
        self.client.get("/api/auth/health",   name="GET /health (auth)")
        self.client.get("/api/course/health", name="GET /health (course)")
        self.client.get("/api/exam/health",   name="GET /health (exam)")


class FacultyUser(HttpUser):
    """
    Simulates a faculty member:
    - Logs in
    - Views all exams
    - Publishes grades
    Weight=1 means fewer faculty than students.
    """
    wait_time = between(2, 6)
    weight    = 1

    def on_start(self):
        creds = random.choice(FACULTY_CREDS)
        with self.client.post(
            "/api/auth/login",
            json=creds,
            catch_response=True,
            name="POST /api/auth/login"
        ) as resp:
            if resp.status_code == 200:
                self.token = resp.json().get("token", "")
                resp.success()
            else:
                self.token = ""
                resp.failure(f"Faculty login failed: {resp.status_code}")

    def auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    @task(2)
    def view_all_exams(self):
        self.client.get(
            "/api/exam/exams",
            headers=self.auth_headers(),
            name="GET /api/exam/exams"
        )

    @task(1)
    def publish_grade(self):
        self.client.post(
            "/api/exam/grades/publish",
            json={
                "user_id":     random.randint(5, 9),
                "exam_id":     random.randint(1, 5),
                "marks":       round(random.uniform(40, 100), 1),
                "total_marks": 100
            },
            headers=self.auth_headers(),
            name="POST /api/exam/grades/publish"
        )


# ── Event hooks for custom reporting ─────────────────────────────────
@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("\n" + "="*60)
    print("  CloudCUST Load Test Complete")
    print(f"  Total requests : {environment.runner.stats.total.num_requests}")
    print(f"  Failures       : {environment.runner.stats.total.num_failures}")
    print(f"  Avg response   : {environment.runner.stats.total.avg_response_time:.1f}ms")
    print(f"  RPS            : {environment.runner.stats.total.current_rps:.1f}")
    print("="*60)
