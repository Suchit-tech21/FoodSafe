import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from app import app

@pytest.fixture()
def client():
    app.config["TESTING"]=True
    with app.test_client() as c: yield c

def test_health(client): assert client.get("/api/health").status_code==200
def test_restaurant_search(client): assert client.get("/api/restaurants?q=Green").status_code==200
def test_restaurant_exact(client): assert client.get("/api/restaurants/1").status_code==200
def test_restaurant_risk(client): assert client.get("/api/restaurants/1/risk").status_code==200
def test_provenance(client): assert client.get("/api/restaurants/1/provenance").status_code==200
def test_binary_search(client):
    r=client.get("/api/restaurants/binary-search?q=green leaf restaurant")
    assert r.status_code==200 and r.json["found"]
def test_complaints_get(client): assert client.get("/api/complaints").status_code==200
def test_inventory_get(client): assert client.get("/api/inventory").status_code==200
def test_inventory_heap(client): assert client.get("/api/inventory/heap").status_code==200
def test_visits_get(client): assert client.get("/api/visits").status_code==200
def test_ocr_requires_image(client): assert client.post("/api/ocr").status_code==400
def test_admin_requires_auth(client): assert client.get("/api/admin/dashboard").status_code==401
def test_auth_me_anonymous(client): assert client.get("/api/auth/me").json["authenticated"] is False
def test_login_bad_password(client): assert client.post("/api/auth/login",json={"username":"admin","password":"wrong"}).status_code==401
def test_login_admin(client):
    r=client.post("/api/auth/login",json={"username":"admin","password":"admin123"})
    assert r.status_code==200 and r.json["user"]["role"]=="ADMIN"
def test_admin_dashboard_after_login(client):
    client.post("/api/auth/login",json={"username":"admin","password":"admin123"})
    assert client.get("/api/admin/dashboard").status_code==200
def test_logout(client):
    client.post("/api/auth/login",json={"username":"admin","password":"admin123"})
    assert client.post("/api/auth/logout").status_code==200
def test_moderator_login(client):
    r=client.post("/api/auth/login",json={"username":"moderator","password":"mod123"})
    assert r.status_code==200 and r.json["user"]["role"]=="MODERATOR"
def test_reviews_requires_auth(client): assert client.get("/api/admin/complaints/CMP-1001/reviews").status_code==401
def test_reviews_authenticated(client):
    client.post("/api/auth/login",json={"username":"admin","password":"admin123"})
    assert client.get("/api/admin/complaints/CMP-1001/reviews").status_code==200
def test_dashboard_shape(client):
    client.post("/api/auth/login",json={"username":"admin","password":"admin123"})
    d=client.get("/api/admin/dashboard").json
    assert "stats" in d and "priority_complaints" in d and "inventory_alerts" in d
