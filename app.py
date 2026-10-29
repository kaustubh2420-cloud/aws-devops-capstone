
from flask import Flask, jsonify, request

app = Flask(__name__)

products = [
    {"id": 1, "name": "Laptop", "price": 55000},
    {"id": 2, "name": "Keyboard", "price": 1500},
    {"id": 3, "name": "Mouse", "price": 700}
]


@app.route("/")
def home():
    return jsonify({
        "message": "Product Service is running!",
        "status": "healthy"
    })


@app.route("/products")
def get_products():
    return jsonify(products)
@app.route("/products/search")
def search_products():
    name = request.args.get("name", "").strip().lower()

    if not name:
        return jsonify({"error": "Please provide a product name"}), 400

    results = [
        product for product in products
        if name in product["name"].lower()
    ]

    return jsonify(results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
