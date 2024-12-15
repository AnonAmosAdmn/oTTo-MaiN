from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import subprocess
import json
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='../frontend/build')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({'success': 'File uploaded successfully'})

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

def read_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            return json.load(file)
    return []

def write_json(filepath, data):
    with open(filepath, 'w') as file:
        json.dump(data, file, indent=4)

@app.route('/api/shell', methods=['POST'])
def run_shell():
    command = request.json.get('command')
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return jsonify({'output': result.stdout, 'error': result.stderr})

@socketio.on('input')
def handle_input(data):
    command = data['command']
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    emit('output', {'output': result.stdout + result.stderr})

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

ollama_process = None

@app.route('/api/start', methods=['POST'])
def start_ollama():
    global ollama_process
    if ollama_process is None:
        ollama_process = subprocess.Popen(["ollama", "serve"])
        return jsonify({"status": "started"})
    else:
        return jsonify({"status": "already running"}), 400

@app.route('/api/stop', methods=['POST'])
def stop_ollama():
    global ollama_process
    if ollama_process is not None:
        ollama_process.terminate()
        ollama_process = None
        return jsonify({"status": "stopped"})
    else:
        return jsonify({"status": "not running"}), 400

@app.route('/api/models', methods=['GET'])
def list_models():
    result = subprocess.run(["ollama", "list"], stdout=subprocess.PIPE, text=True)
    models = result.stdout.splitlines()
    return jsonify({"models": models})

@app.route('/api/pull', methods=['POST'])
def pull_model():
    data = request.json
    model_name = data.get("model_name")
    result = subprocess.run(["ollama", "pull", model_name], stdout=subprocess.PIPE, text=True)
    return jsonify({"result": result.stdout})

@app.route('/api/save', methods=['POST'])
def save_model():
    data = request.json
    original_model = data.get("original_model")
    new_model_name = data.get("new_model_name")
    # Implement your model saving logic here
    return jsonify({"status": "saved"})

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        model = data.get("model")
        messages = data.get("messages")
        stream = data.get("stream", False)
        
        url = f"http://localhost:11434/api/chat"
        headers = {"Content-Type": "application/json"}
        payload = {"model": model, "messages": messages, "stream": stream}
        
        response = requests.post(url, headers=headers, json=payload, stream=stream)
        response.raise_for_status()
        
        if stream:
            def generate():
                for line in response.iter_lines():
                    if line:
                        yield line.decode('utf-8') + "\n"
            return Response(generate(), content_type='application/json')
        else:
            return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/config', methods=['GET'])
def config():
    config_data = {
        "model": "Mistral",
        "status": "running",
        "version": "1.0.0"
    }
    return jsonify(config_data)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"})    
    
if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=5001, debug=True)