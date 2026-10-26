
import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.get_json() == {
        "message": "Product Service is running!",
        "status": "healthy",
    }


def test_products_endpoint(client):
    response = client.get("/products")
    assert response.status_code == 200

    products = response.get_json()
    assert len(products) == 3
    assert products[0]["name"] == "Laptop"
    assert products[1]["name"] == "Keyboard"
    assert products[2]["name"] == "Mouse"
