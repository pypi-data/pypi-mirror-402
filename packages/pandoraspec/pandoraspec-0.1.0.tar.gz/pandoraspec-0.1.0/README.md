# PanDoraSpec - DORA Compliance Audit Tool

The PanDoraSpec Tool is an automated audit system designed to verify compliance with DORA (Digital Operational Resilience Act) requirements for third-party ICT providers. It performs deep technical analysis of APIs to detect schema drift, resilience issues, and security vulnerabilities.

## Project Structure

This is a monorepo containing both the backend and frontend components:

- **backend/**: Python/FastAPI/Celery application that runs the audit engine using Schemathesis.
- **frontend/**: Next.js application providing the user interface for submitting audits and viewing reports.

## Getting Started

### Prerequisites

- Docker Desktop installed and running.

### Application Setup

The entire stack is containerized using Docker Compose.

1.  **Start the application:**

    ```bash
    docker-compose up --build
    ```

    This will start the following services:
    - `frontend`: Available at http://localhost:3000
    - `api`: Backend API at http://localhost:8000
    - `worker`: Celery worker for processing audit tasks
    - `redis`: Message broker and result backend

2.  **Access the Dashboard:**

    Open your browser to [http://localhost:3000](http://localhost:3000).

3.  **Run an Audit:**
    - Enter a Vendor Name.
    - Provide the OpenAPI Schema URL **OR** Upload a local Schema File (JSON/YAML).
    - (Optional) detailed API Key.
    - Click "Run DORA Audit".

## Audit Modules

### Module A: The "Docs vs. Code" Drift Check (The Integrity Test)
**Why**: DORA requires you to monitor if the service effectively supports your critical functions. If the API behaves differently than documented, it's a risk.

### Module B: The "Resilience" Stress Test (Art. 24 & 25)
**Why**: DORA Article 25 explicitly calls for "Digital operational resilience testing".

### Module C: The Security Hygiene Check
**Why**: Basic ICT security requirements.

### Module D: The Compliance Report (The Deliverable)
**Output**: A branded PDF titled "DORA ICT Third-Party Technical Risk Assessment".

## CLI Usage (Open Core)

You can run the audit engine directly from the command line using the `pandoraspec` command.

```bash
# Run against a URL using Docker
docker exec -it checker-api-1 pandoraspec https://petstore.swagger.io/v2/swagger.json --vendor "PetStore"

# Run locally (if installed via pip install .)
pandoraspec https://petstore.swagger.io/v2/swagger.json

# Run against a local file
pandoraspec ./openapi.json
```

**(Note: The CLI provides beautiful terminal output powered by Rich)**

## Deployment

This project is configured for **Railway** deployment out-of-the-box.

### Production Notes

- **Frontend**: The `frontend/Dockerfile` uses a multi-stage build (`standalone` output) for optimized production performance.
- **Backend API**: Runs via Uvicorn.
- **Worker**: Runs via Celery with Redis as the broker.

## Documentation

- [Frontend Documentation](./frontend/README.md)
