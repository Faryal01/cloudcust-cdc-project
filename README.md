# CloudCUST
**Cloud-Native Distributed University Management System**  
CPE4541 · CUST · Fatima Shahid (BCPE223011) · Faryal Naseem (BCPE223051)

---

## Quick Start

```powershell
cd Z:\cdc\files
docker compose up --build
# Open http://localhost  →  login with s001 / student123
```

## Repository Structure

```
cloudcust/
├── services/
│   ├── auth/          Flask Auth Service   (JWT, bcrypt)  — Port 5001
│   ├── course/        Course Registration  (enroll/drop)  — Port 5002
│   └── exam/          Examination Service  (grades)       — Port 5003
├── frontend/          HTML/Bootstrap 5 single-page UI
├── database/          PostgreSQL schema + synthetic seed data
├── k8s/               Kubernetes manifests (6 files)
├── distributed/       Threading simulation + socket modules
├── gpu/               CPU benchmark notebook (simulates GPU)
├── monitoring/        Locust load tests
├── .github/workflows/ GitHub Actions CI/CD
├── docker-compose.yml
├── nginx.conf
└── HOW_TO_RUN.txt     ← Full setup guide
```

## Branching Strategy

| Branch | Purpose |
|---|---|
| `main` | Stable releases only — PR required |
| `dev` | Integration branch |
| `feature/auth` | Auth Service  |
| `feature/course` | Course Service  |
| `feature/exam` | Exam Service  |
| `feature/frontend` | UI  |
| `feature/distributed` | Threading + sockets |

## Test Credentials

| Username | Password | Role |
|---|---|---|
| `s001`–`s005` | `student123` | Student |
| `dr.waseem`, `dr.sara`, `dr.usman` | `faculty123` | Faculty |
| `admin` | `admin123` | Admin |

## SDG Alignment
- **SDG-4** Quality Education — zero downtime during exams and registration
- **SDG-9** Industry & Innovation — industry-standard cloud-native toolchain
- **SDG-11** Sustainable Cities — autoscaling reduces idle energy consumption

## Contributors
- Fatima Shahid (BCPE223011) - Auth Service, Threading, Socket Programming, Frontend UI
- Faryal Naseem (BCPE223051) - Course Service, Exam Service, Kubernetes, GPU Benchmark, Locust Testing
