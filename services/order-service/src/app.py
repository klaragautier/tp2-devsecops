from flask import Flask
app = Flask(__name__)

@app.route("/health")
def health():
    return {"status": "ok", "service": "order-service"}

@app.route("/create", methods=["POST"])
def create_order():
    return {"order_id": 12345, "status": "confirmed"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000) # nosemgrep