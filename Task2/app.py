from flask import Flask
from prometheus_client import Counter, generate_latest
import socket

app = Flask(__name__)
http_requests_total = Counter('http_requests_total', 'Number of HTTP requests')

@app.route('/')
def index():
    http_requests_total.inc()
    return f"Hello from pod {socket.gethostname()}"

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
