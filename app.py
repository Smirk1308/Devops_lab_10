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
    try:
        db = connect_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, name, department FROM students")
        students = cursor.fetchall()
        cursor.close()
        db.close()

        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Student Management System</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f8fafc;
                    color: #0f172a;
                    margin: 0;
                    padding: 40px 20px;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                }
                .container {
                    background: #ffffff;
                    border: 1px solid #e2e8f0;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    padding: 32px;
                    max-width: 650px;
                    width: 100%;
                }
                .badge {
                    display: inline-block;
                    background: #dbeafe;
                    color: #1e40af;
                    font-size: 12px;
                    font-weight: 600;
                    padding: 4px 10px;
                    border-radius: 9999px;
                    margin-bottom: 12px;
                }
                h1 {
                    font-size: 24px;
                    color: #1e3a8a;
                    margin: 0 0 8px 0;
                }
                p.subtitle {
                    color: #64748b;
                    font-size: 14px;
                    margin-bottom: 24px;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 10px;
                }
                th, td {
                    padding: 12px 16px;
                    text-align: left;
                }
                th {
                    background-color: #f1f5f9;
                    color: #334155;
                    font-size: 13px;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    border-bottom: 2px solid #cbd5e1;
                }
                td {
                    border-bottom: 1px solid #e2e8f0;
                    font-size: 14px;
                }
                tr:hover {
                    background-color: #f8fafc;
                }
                .tag {
                    display: inline-block;
                    padding: 2px 8px;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 500;
                    background: #e0f2fe;
                    color: #0369a1;
                }
                .footer {
                    margin-top: 24px;
                    padding-top: 16px;
                    border-top: 1px solid #f1f5f9;
                    font-size: 12px;
                    color: #94a3b8;
                    display: flex;
                    justify-content: space-between;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <span class="badge">Docker Compose • Multi-Container</span>
                <h1>Student Management System</h1>
                <p class="subtitle">Two-Tier Web Architecture: Python Flask Container + MySQL Database Container</p>
                
                <table>
                    <thead>
                        <tr>
                            <th>Student ID</th>
                            <th>Student Name</th>
                            <th>Department</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        for s in students:
            html += f"""
                        <tr>
                            <td><strong>#{s[0]}</strong></td>
                            <td>{s[1]}</td>
                            <td><span class="tag">{s[2]}</span></td>
                        </tr>
            """
        html += """
                    </tbody>
                </table>
                <div class="footer">
                    <span>Course: 1BCS303 (DevOps Lab)</span>
                    <span>Backend Status: Connected to MySQL (db:3306)</span>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    except Exception as e:
        return f"<h1>Database Connection Error</h1><p>{str(e)}</p>", 500

@app.route("/api/students")
def get_students_json():
    try:
        db = connect_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id, name, department FROM students")
        students = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify({"status": "success", "count": len(students), "data": students})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "web", "tier": "flask-frontend"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
