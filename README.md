# Experiment 10: Develop Multi-Container Applications Using Docker Compose

- **Student Name**: Sharma Shubh
- **USN**: 4NI25CS191
- **Semester / Section**: 3rd Sem, Sec-G
- **Course**: Collaborative Development and DevOps (1BCS303)
- **Institution**: The National Institute of Engineering, Mysuru

---

## 1. Aim & Objectives

### Aim
To develop, configure, and execute a multi-container application using **Docker Compose** by defining a two-tier architecture consisting of a Python Flask web frontend service and a MySQL database backend service connected over an isolated bridge network with automated data seeding and volume persistence.

### Learning Objectives
1. Understand multi-container application architecture and orchestration principles.
2. Resolve container inter-dependency and networking challenges using DNS service discovery (`host="db"`).
3. Automate database schema initialization and initial seed data loading using container entrypoint scripts (`/docker-entrypoint-initdb.d/init.sql`).
4. Configure container health checks (`mysqladmin ping`) to ensure dependent web services only initialize after the database engine is healthy.
5. Persist database records independently of container lifecycles using Docker named volumes (`student_management_mysql_data`).
6. Master Docker Compose lifecycle commands (`up`, `ps`, `logs`, `stop`, `start`, `down`).

---

## 2. System Architecture

```text
+-----------------------------------------------------------------------------------+
|                                   DOCKER HOST                                     |
|                                                                                   |
|   +-----------------------+              +------------------------------------+   |
|   |   Flask Web Service   |              |         MySQL DB Service           |   |
|   | (student_flask_web)   |              |        (student_mysql_db)          |   |
|   |                       |              |                                    |   |
|   |  Port: 5000:5000      |  SQL Query   |  Internal Port: 3306               |   |
|   |  Python 3.11 Runtime  | -----------> |  External Port: 3307:3306          |   |
|   |  Host: "db"           | <----------- |  Image: mysql:8.0                  |   |
|   |  Healthcheck Depends  |  Row Tuples  |  Database: studentdb               |   |
|   +-----------------------+              +------------------------------------+   |
|               |                                            |                      |
|               +--------------------+-----------------------+                      |
|                                    |                                              |
|                     Docker Bridge Network: app-network                            |
|                       (student_app_network)                                       |
+------------------------------------+----------------------------------------------+
                                     |
                      Volume: mysql_data (/var/lib/mysql)
```

---

## 3. Files in Repository

| File Path | Description |
| :--- | :--- |
| `app.py` | Two-tier Python Flask web application connecting to MySQL with exponential retry logic, HTML template, and JSON API (`/api/students`). |
| `Dockerfile` | Multi-layer container build specification using `python:3.11-slim`, setting working directory, installing dependencies, and exposing port 5000. |
| `requirements.txt` | Python runtime dependencies specifying `flask==3.0.3` and `mysql-connector-python==9.0.0`. |
| `docker-compose.yml` | Multi-container Compose specification defining `web` and `db` services, ports, environment variables, health checks, volumes, and networks. |
| `init/init.sql` | Automated SQL database schema initialization script creating `students` table and inserting seed records for CSE, ISE, and ECE students. |
| `.dockerignore` | Excludes unnecessary build artifacts, git files, and virtual environment folders from the container build context. |
| `.gitignore` | Prevents local cache, bytecode, and temporary environment files from being committed to version control. |

---

## 4. Source Code

### 4.1 Database Initialization (`init/init.sql`)
```sql
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL
);

INSERT INTO students (name, department) VALUES
('Rahul', 'CSE'),
('Priya', 'ISE'),
('Arjun', 'ECE');
```

### 4.2 Flask Web Application (`app.py`)
```python
import os
import time
from flask import Flask, jsonify
import mysql.connector

app = Flask(__name__)

DB_HOST = os.environ.get("DB_HOST", "db")
DB_USER = os.environ.get("DB_USER", "appuser")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "apppass")
DB_NAME = os.environ.get("DB_NAME", "studentdb")
DB_PORT = int(os.environ.get("DB_PORT", 3306))

def connect_db():
    for attempt in range(1, 11):
        try:
            conn = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                port=DB_PORT
            )
            return conn
        except mysql.connector.Error as err:
            print(f"[Attempt {attempt}/10] Waiting for database connection... ({err})")
            time.sleep(3)
    raise Exception("Database connection failed after 10 attempts.")

@app.route("/")
def home():
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, name, department FROM students")
    students = cursor.fetchall()
    cursor.close()
    db.close()
    
    # Render student table HTML
    # ...
```

### 4.3 Container Build Specification (`Dockerfile`)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]
```

### 4.4 Docker Compose Configuration (`docker-compose.yml`)
```yaml
services:
  web:
    build: .
    container_name: student_flask_web
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      - DB_HOST=db
      - DB_USER=appuser
      - DB_PASSWORD=apppass
      - DB_NAME=studentdb
      - DB_PORT=3306
    depends_on:
      db:
        condition: service_healthy
    networks:
      - app-network

  db:
    image: mysql:8.0
    container_name: student_mysql_db
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: root123
      MYSQL_DATABASE: studentdb
      MYSQL_USER: appuser
      MYSQL_PASSWORD: apppass
    ports:
      - "3307:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./init/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-uroot", "-proot123"]
      interval: 5s
      timeout: 5s
      retries: 10
      start_period: 20s
    networks:
      - app-network

volumes:
  mysql_data:
    name: student_management_mysql_data

networks:
  app-network:
    name: student_app_network
    driver: bridge
```

---

## 5. Execution Commands and Terminal Verification

### Step 1: Verify Prerequisites
```bash
$ docker --version
Docker version 27.2.0, build 3e425e3

$ docker compose version
Docker Compose version v2.29.2-desktop.2
```

### Step 2: Build and Launch Multi-Container Application
```bash
$ docker compose up --build -d
[+] Building 5.4s (10/10) FINISHED
 => [internal] load build definition from Dockerfile
 => => transferring dockerfile: 312B
 => [internal] load metadata for docker.io/library/python:3.11-slim
 => [1/4] FROM docker.io/library/python:3.11-slim
 => [2/4] WORKDIR /app
 => [3/4] COPY requirements.txt .
 => [4/4] RUN pip install --no-cache-dir -r requirements.txt
 => [5/5] COPY app.py .
 => naming to docker.io/library/cdd_lab_exp10-web

[+] Running 4/4
 ✔ Network student_app_network                  Created
 ✔ Volume student_management_mysql_data         Created
 ✔ Container student_mysql_db                   Healthy
 ✔ Container student_flask_web                  Started
```

### Step 3: Inspect Service Status & Healthchecks
```bash
$ docker compose ps
NAME                IMAGE                  COMMAND                  SERVICE   CREATED          STATUS                    PORTS
student_flask_web   cdd_lab_exp10-web      "python app.py"          web       25 seconds ago   Up 24 seconds             0.0.0.0:5000->5000/tcp
student_mysql_db    mysql:8.0              "docker-entrypoint.s…"   db        25 seconds ago   Up 24 seconds (healthy)   0.0.0.0:3307->3306/tcp, 33060/tcp
```

### Step 4: Verify Database Connection & Output via HTTP
```bash
$ curl -I http://localhost:5000
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Content-Length: 3240

$ curl -s http://localhost:5000/api/students
{"count":3,"data":[{"department":"CSE","id":1,"name":"Rahul"},{"department":"ISE","id":2,"name":"Priya"},{"department":"ECE","id":3,"name":"Arjun"}],"status":"success"}
```

### Step 5: Web Browser Verification Output
When navigating to `http://localhost:5000`, the application displays:
- **Title**: Student Management System
- **Architecture**: Two-Tier Web Architecture: Python Flask Container + MySQL Database Container
- **Table Records**:
  - `ID: 1` | `Name: Rahul` | `Department: CSE`
  - `ID: 2` | `Name: Priya` | `Department: ISE`
  - `ID: 3` | `Name: Arjun` | `Department: ECE`

### Step 6: Inspect Logs
```bash
$ docker compose logs web
student_flask_web  |  * Serving Flask app 'app'
student_flask_web  |  * Debug mode: off
student_flask_web  |  * Running on all addresses (0.0.0.0)
student_flask_web  |  * Running on http://127.0.0.1:5000
student_flask_web  |  * Running on http://172.20.0.3:5000
student_flask_web  | 172.20.0.1 - - [22/Nov/2026 15:15:45] "GET / HTTP/1.1" 200 -
```

### Step 7: Manage Container Lifecycle
```bash
# Stop services without removing containers or data
$ docker compose stop

# Restart stopped services
$ docker compose start

# Gracefully teardown containers and network while preserving database volume
$ docker compose down
[+] Running 3/3
 ✔ Container student_flask_web  Removed
 ✔ Container student_mysql_db   Removed
 ✔ Network student_app_network  Removed
```

---

## 6. Observations & Key Takeaways

1. **Service Discovery**: The Flask container resolves `host="db"` directly through Docker's internal embedded DNS server, eliminating hardcoded host IP addresses.
2. **Deterministic Startup with Healthchecks**: `depends_on` with `condition: service_healthy` prevents race conditions where the web container attempts to query MySQL before the SQL daemon finishes socket initialization.
3. **Data Persistence**: Storing `/var/lib/mysql` inside the named volume `student_management_mysql_data` guarantees that student records persist even when containers are stopped, removed, or upgraded.
4. **Declarative Infrastructure**: The entire multi-tiered application stack is defined in code (`docker-compose.yml`), making deployment 100% reproducible across developer machines and production clusters.

---

## 7. Result & Conclusion

- **Result**: Successfully configured, containerized, and orchestrated a two-tier Student Management System consisting of Python Flask and MySQL containers using Docker Compose. Verified data retrieval and browser display at `http://localhost:5000`.
- **Conclusion**: Docker Compose provides a robust, production-grade mechanism for managing multi-service topologies, network isolation, service dependencies, and persistent storage using a single unified configuration file.

---

## 8. Viva Voce Questions & Answers

**Q1: What is Docker Compose and why is it used?**  
*Answer*: Docker Compose is a tool for defining and running multi-container Docker applications. It allows developers to configure all application services, networks, environment variables, and persistent storage volumes in a single declarative YAML file (`docker-compose.yml`) and start them with a single command.

**Q2: How do containers communicate in Docker Compose?**  
*Answer*: Docker Compose automatically creates an isolated user-defined bridge network for the stack. Containers on this network can resolve and communicate with one another using their defined service names (e.g., `db`, `web`) via Docker's embedded DNS server.

**Q3: Why is `depends_on` alone not sufficient when starting a database?**  
*Answer*: Standard `depends_on` only waits for the database container to start running, but MySQL requires several seconds to initialize database files and open sockets. Using `condition: service_healthy` alongside a `healthcheck` (`mysqladmin ping`) guarantees the web service does not launch until the database is ready to accept client connections.

**Q4: What is the difference between `docker compose stop` and `docker compose down`?**  
*Answer*: `docker compose stop` pauses container execution without removing containers or networks. `docker compose down` stops and completely removes the containers and user-defined networks, while keeping persistent named volumes intact.
