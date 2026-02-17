import time
import uuid
import json
from flask import Flask, request, g, jsonify

app = Flask(__name__)
SERVICE_NAME = "catalog"

@app.before_request
def _before():
    g.start_time = time.time()
    rid = request.headers.get("X-Request-Id")
    if not rid:
        rid = str(uuid.uuid4())
    g.request_id = rid

@app.after_request
def _after(response):
    latency_ms = int((time.time() - g.start_time) * 1000)
    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "level": "INFO",
        "service": SERVICE_NAME,
        "request_id": g.request_id,
        "method": request.method,
        "path": request.path,
        "status": response.status_code,
        "latency_ms": latency_ms,
        "query": (request.query_string.decode("utf-8")[:200] if request.query_string else ""),
    }
    print(json.dumps(record), flush=True)
    response.headers["X-Request-Id"] = g.request_id
    return response

@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/')
def index():
    return "Catalog Service Ready"

@app.route('/search')
def search():
    return jsonify({"results": []}), 200

# Route pour l'attaque Command Injection
@app.route('/debug/run')
def debug_run():
    return jsonify({"output": "fake output"}), 200

# Route pour l'attaque Path Traversal
@app.route('/report')
def report():
    return jsonify({"content": "fake file content"}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)