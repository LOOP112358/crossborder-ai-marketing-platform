import io
import os
from pathlib import Path

os.environ["MATTE_MOCK_MODE"] = "1"

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from app.main import app


client = TestClient(app)


def sample_image() -> bytes:
    image = Image.new("RGB", (180, 180), "white")
    ImageDraw.Draw(image).rectangle((45, 30, 135, 150), fill=(40, 90, 210))
    buf = io.BytesIO(); image.save(buf, "PNG")
    return buf.getvalue()


def test_health():
    body = client.get("/api/matte/health").json()
    assert body["code"] == 0 and body["data"]["status"] == "ready"


def test_process_history_download():
    response = client.post("/api/matte/process", data={"user_id": 7, "edge_smoothing": 1},
                           files={"file": ("shoe.png", sample_image(), "image/png")})
    assert response.status_code == 200
    item = response.json()["data"]
    assert item["matted_url"].endswith(".png")
    assert item["attributes"]["color"]
    history = client.get("/api/matte/history", params={"user_id": 7}).json()["data"]
    assert any(x["id"] == item["id"] for x in history)
    assert client.get(f"/api/matte/download/{item['id']}").status_code == 200

