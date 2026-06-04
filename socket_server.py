import json
import socket
import threading
import time

HOST = "0.0.0.0"
PORT = 6000


def check_enrollment(user_id, course_id):
    """
    Simulated enrollment check for socket communication demo.
    This keeps the socket module stable for CEP demonstration.
    Main database/API proof is already shown through Docker services.
    """
    sample_enrollments = {
        (5, 1): True,
        (6, 2): True,
        (7, 3): False,
        (8, 1): False,
        (9, 1): True,
    }

    enrolled = sample_enrollments.get((user_id, course_id), False)

    return {
        "enrolled": enrolled,
        "status": "ok",
        "user_id": user_id,
        "course_id": course_id,
        "source": "socket-server"
    }


def process_request(request):
    action = request.get("action")

    if action == "ping":
        return {
            "pong": True,
            "server": "course-socket-server",
            "status": "ok"
        }

    if action == "check_enrollment":
        user_id = int(request.get("user_id", 0))
        course_id = int(request.get("course_id", 0))
        return check_enrollment(user_id, course_id)

    return {
        "status": "error",
        "message": f"Unknown action: {action}"
    }


def handle_client(conn, addr):
    print(f"[SOCKET SERVER] Connection from {addr}")
    print(f"[SOCKET SERVER] Active threads: {threading.active_count()}")

    try:
        data = b""

        while True:
            chunk = conn.recv(1024)
            if not chunk:
                break
            data += chunk

            try:
                request = json.loads(data.decode("utf-8"))
                break
            except json.JSONDecodeError:
                continue

        print(f"[SOCKET SERVER] Request: {request}")

        response = process_request(request)

        time.sleep(0.02)

        conn.sendall(json.dumps(response).encode("utf-8"))
        print(f"[SOCKET SERVER] Response: {response}")

    except Exception as e:
        error_response = {
            "status": "error",
            "detail": str(e)
        }
        conn.sendall(json.dumps(error_response).encode("utf-8"))

    finally:
        conn.close()


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((HOST, PORT))
    server_socket.listen(10)

    print(f"[SOCKET SERVER] Listening on {HOST}:{PORT}")
    print("[SOCKET SERVER] Waiting for connections...\n")

    while True:
        conn, addr = server_socket.accept()
        client_thread = threading.Thread(
            target=handle_client,
            args=(conn, addr),
            daemon=True
        )
        client_thread.start()


if __name__ == "__main__":
    start_server()