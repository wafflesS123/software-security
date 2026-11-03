"""
Tiny sample web app for Week 1 threat modeling.
You will NOT exploit this in Week 1 — you will draw a data-flow diagram
and apply STRIDE to its components (web client, app, SQLite DB, /upload).
"""
from flask import Flask, request, jsonify, send_from_directory
import sqlite3, os
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
DB = "notes.db"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def init_db():
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, owner TEXT, body TEXT)")
    con.commit(); con.close()

@app.route("/notes", methods=["GET", "POST"])
def notes():
    con = sqlite3.connect(DB)
    if request.method == "POST":
        owner = request.json.get("owner", "anon")
        body = request.json.get("body", "")
        con.execute("INSERT INTO notes (owner, body) VALUES (?, ?)", (owner, body))
        con.commit()
    rows = con.execute("SELECT id, owner, body FROM notes").fetchall()
    con.close()
    return jsonify(rows)

@app.route("/upload", methods=["POST"])
def upload():
    f = request.files["file"]
    if not f.filename:
        return {"error": "No filename provided"}, 400
    safe_name = secure_filename(f.filename)
    if not safe_name:
        return {"error": "Invalid filename"}, 400
    # Allow only specific file extensions
    allowed_extensions = {"txt", "pdf", "png", "jpg", "jpeg"}
    extension = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
    if extension not in allowed_extensions:
        return {"error": "File type not allowed"}, 400
    # Generate a server-side filename
    new_filename = f"{uuid.uuid4().hex}.{extension}"
    save_path = os.path.abspath(os.path.join(UPLOAD_DIR, new_filename))
    # Ensure the final path stays inside UPLOAD_DIR
    if os.path.commonpath([os.path.abspath(UPLOAD_DIR), save_path]) != os.path.abspath(UPLOAD_DIR):
        return {"error": "Invalid file path"}, 400
    f.save(save_path)
    return {"saved": new_filename}, 200

@app.route("/files/<name>")
def files(name):
    return send_from_directory(UPLOAD_DIR, name)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
