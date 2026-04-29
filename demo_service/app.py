import os
import logging
from flask import Flask, request, jsonify

app = Flask(__name__)

LOG_PATH = os.environ.get("LOG_PATH", "demo_service/logs/error.log")

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


@app.route("/api/user", methods=["GET"])
def get_user():
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id")
    if user_id is None:
        return jsonify({"error": "user_id is required"}), 400
    users = {
        "1": {"name": "Alice", "age": 30},
        "2": {"name": "Bob", "age": 25},
    }
    user = users.get(user_id)
    if user is None:
        return jsonify({"error": "user not found"}), 404
    return jsonify(user)


@app.route("/api/calculate", methods=["POST"])
def calculate():
    payload = request.get_json(silent=True) or {}
    try:
        a = float(payload.get("a", 0))
        b = float(payload.get("b", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "invalid number input"}), 400
    if b == 0:
        return jsonify({"error": "division by zero"}), 400
    result = "Result: " + str(a / b)
    return jsonify({"result": result})


@app.route("/api/discount", methods=["POST"])
def apply_discount():
    payload = request.get_json(silent=True) or {}
    price = payload.get("price")
    discount = payload.get("discount", 0)
    final_price = (price or 0) - discount
    return jsonify({"final_price": final_price})


@app.route("/api/greet", methods=["GET"])
def greet():
    payload = request.get_json(silent=True) or {}
    name = payload.get("name")
    greeting = (name or "").upper()
    return jsonify({"greeting": greeting})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
