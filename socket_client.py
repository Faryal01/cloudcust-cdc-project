"""
CloudCUST — Socket Programming Module (Client)
Phase 3, Objective 4: TCP socket communication

Simulates the Exam Service querying the Course Service over TCP
to verify student enrollment before grade publication.

Run AFTER socket_server.py:  python distributed/socket_client.py
"""

import socket
import json
import time

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 6000


def send_request(action: str, **kwargs) -> dict:
    """Send a JSON request to the socket server and return the response."""
    payload = {"action": action, **kwargs}
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_HOST, SERVER_PORT))
        s.sendall((json.dumps(payload) + "\n").encode())
        response = b""
        while True:
            chunk = s.recv(1024)
            if not chunk:
                break
            response += chunk
            if response.endswith(b"\n"):
                break
    return json.loads(response.decode().strip())


def run_demo():
    print("=" * 60)
    print("  CloudCUST — Socket Communication Demo")
    print(f"  Connecting to {SERVER_HOST}:{SERVER_PORT}")
    print("=" * 60)

    # Test 1: Ping
    print("\n[TEST 1] Ping server")
    result = send_request("ping")
    print(f"  Response: {result}")

    # Test 2: Check enrollment for existing students
    print("\n[TEST 2] Check enrollment — student 5, course 1 (CPE4541)")
    result = send_request("check_enrollment", user_id=5, course_id=1)
    print(f"  Response: {result}")

    print("\n[TEST 3] Check enrollment — student 6, course 2 (CPE4521)")
    result = send_request("check_enrollment", user_id=6, course_id=2)
    print(f"  Response: {result}")

    # Test 4: Non-existent student
    print("\n[TEST 4] Check enrollment — unknown student (id=999)")
    result = send_request("check_enrollment", user_id=999, course_id=1)
    print(f"  Response: {result}")

    # Test 5: Latency benchmark over 20 requests
    print("\n[TEST 5] Latency benchmark — 20 rapid requests")
    latencies = []
    for i in range(20):
        start = time.time()
        send_request("check_enrollment", user_id=(i % 5) + 5, course_id=1)
        latencies.append((time.time() - start) * 1000)

    print(f"  Min:    {min(latencies):.2f} ms")
    print(f"  Max:    {max(latencies):.2f} ms")
    print(f"  Mean:   {sum(latencies)/len(latencies):.2f} ms")

    print("\n" + "=" * 60)
    print("  Socket demo complete.")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
