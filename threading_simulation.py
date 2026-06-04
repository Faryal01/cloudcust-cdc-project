import json
import time
import statistics
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

AUTH_URL = "http://localhost:5001/login"
COURSE_URL = "http://localhost:5002/courses"

USERNAME = "Faryal"
PASSWORD = "123456"
TOTAL_STUDENTS = 100
TIMEOUT = 30


def get_token():
    response = requests.post(
        AUTH_URL,
        json={"username": USERNAME, "password": PASSWORD},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["token"]


def simulate_student(student_no, token):
    start = time.perf_counter()

    try:
        response = requests.get(
            COURSE_URL,
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT,
        )

        latency = time.perf_counter() - start

        return {
            "student_no": student_no,
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "latency_seconds": round(latency, 4),
            "error": None if response.status_code == 200 else response.text[:200],
        }

    except Exception as e:
        latency = time.perf_counter() - start

        return {
            "student_no": student_no,
            "success": False,
            "status_code": None,
            "latency_seconds": round(latency, 4),
            "error": str(e),
        }


def run_simulation():
    print("=" * 70)
    print("  CloudCUST — Concurrent Course Registration Workload Simulation")
    print(f"  Students: {TOTAL_STUDENTS} | Target: {COURSE_URL}")
    print("=" * 70)

    print("\nGetting JWT token from Auth Service...")
    token = get_token()
    print("JWT token received successfully.")

    print(f"\nLaunching {TOTAL_STUDENTS} concurrent student requests...\n")

    wall_start = time.perf_counter()
    results = []

    with ThreadPoolExecutor(max_workers=TOTAL_STUDENTS) as executor:
        futures = [
            executor.submit(simulate_student, i + 1, token)
            for i in range(TOTAL_STUDENTS)
        ]

        for future in as_completed(futures):
            results.append(future.result())

    wall_time = time.perf_counter() - wall_start

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    latencies = [r["latency_seconds"] for r in successful]

    print("-" * 70)
    print("  RESULTS")
    print("-" * 70)
    print(f"  Total students simulated : {TOTAL_STUDENTS}")
    print(f"  Successful               : {len(successful)}")
    print(f"  Failed                   : {len(failed)}")
    print(f"  Total wall-clock time    : {wall_time:.2f}s")

    if latencies:
        print("\n  Per-request latency:")
        print(f"    Min     : {min(latencies):.3f}s")
        print(f"    Max     : {max(latencies):.3f}s")
        print(f"    Mean    : {statistics.mean(latencies):.3f}s")
        print(f"    Median  : {statistics.median(latencies):.3f}s")
        print(
            f"    Std Dev : "
            f"{(statistics.stdev(latencies) if len(latencies) > 1 else 0):.3f}s"
        )

    if failed:
        print("\n  Sample errors:")
        for item in failed[:5]:
            print(f"    Student {item['student_no']}: {item['error']}")

    report = {
        "simulation_name": "CloudCUST Concurrent Course Registration Workload",
        "total_students": TOTAL_STUDENTS,
        "successful": len(successful),
        "failed": len(failed),
        "wall_clock_seconds": round(wall_time, 4),
        "target_url": COURSE_URL,
        "latency_summary": {
            "min": min(latencies) if latencies else None,
            "max": max(latencies) if latencies else None,
            "mean": statistics.mean(latencies) if latencies else None,
            "median": statistics.median(latencies) if latencies else None,
            "std_dev": statistics.stdev(latencies) if len(latencies) > 1 else 0,
        },
        "results": results,
    }

    Path("distributed").mkdir(exist_ok=True)

    with open("distributed/threading_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\nReport saved to: distributed/threading_report.json")
    print("=" * 70)


if __name__ == "__main__":
    run_simulation()