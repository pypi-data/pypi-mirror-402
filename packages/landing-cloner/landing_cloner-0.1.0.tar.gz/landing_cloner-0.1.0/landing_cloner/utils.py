import os


server_source = """from flask import Flask, request, render_template_string
import sqlite3

app = Flask(__name__)
DB_PATH = "./data.db"


# Initialize database
with sqlite3.connect(DB_PATH) as conn:
    conn.execute('CREATE TABLE IF NOT EXISTS entries (id INTEGER PRIMARY KEY AUTOINCREMENT, email Text, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)')

@app.route('/')
def index():
    page = open("./templates/index.html").read()
    return page

@app.route('/submit', methods=['POST'])
def submit():
    email = request.form.get('email')
    data = request.form.get('data')
    if data and email:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('INSERT INTO messages (email, content) VALUES (?, ?)', (email, data))
    return "OK"


if __name__ == '__main__':
    # Run on all interfaces, port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
"""


def create_server(folder_path, html_content):
    """Create the Flask app files (app.py, requirements.txt, templates)."""
    # Create app.py
    with open(os.path.join(folder_path, "app.py"), "w") as f:
        f.write(server_source)
    
    # Create requirements.txt
    with open(os.path.join(folder_path, "requirements.txt"), "w") as f:
        f.write("flask\ngunicorn\n")
    templates_dir = os.path.join(folder_path, "templates")
    os.makedirs(templates_dir, exist_ok=True)
    
    with open(os.path.join(templates_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return True


def create_dockerfile(folder_path):
    """Create a Dockerfile for the Flask app."""
    dockerfile_content = '''FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
'''
    
    with open(os.path.join(folder_path, "Dockerfile"), "w") as f:
        f.write(dockerfile_content)



def get_folder_name(url):
    """Generate a safe folder name from URL."""
    # Remove protocol and special characters
    clean_name = url.replace("https://", "").replace("http://", "")
    clean_name = clean_name.replace("/", "_").replace(".", "_")
    return f"{clean_name}_clone"
