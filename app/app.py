
from datetime import datetime, timezone
from flask import Flask, jsonify

app = Flask(__name__)

@app.get("/")
def home():
    return jsonify(
        message="DevOps Kubernetes demo is running",
        timestamp=datetime.now(timezone.utc).isoformat()
    )

@app.get("/health")
def health():
    return jsonify(status="healthy"), 200
