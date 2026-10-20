import io

from PIL import Image


def test_text_clip_round_trip(client):
    res = client.post("/api/clip", json={"clip_text": "hello"})
    assert res.status_code == 201
    clip_id = res.json()["clip_id"]

    clips = client.get("/api/clips").json()["clips"]
    assert [(c["clip_id"], c["clip_text"]) for c in clips] == [(clip_id, "hello")]

    assert client.delete(f"/api/clip/{clip_id}").status_code == 200
    assert client.get("/api/clips").json()["clips"] == []


def test_image_clip_round_trip(client, backend):
    png = io.BytesIO()
    Image.new("RGB", (800, 600), "red").save(png, "PNG")

    res = client.post("/api/clip/file", files={"file": ("photo.png", png.getvalue(), "image/png")})
    assert res.status_code == 201
    clip_id = res.json()["clip_id"]

    [clip] = client.get("/api/clips").json()["clips"]
    assert clip["file"] == {"name": "photo.png", "mime_type": "image/png", "size_bytes": len(png.getvalue()), "has_thumb": True}

    thumb = client.get(f"/api/clip/{clip_id}/thumb")
    assert thumb.headers["content-type"] == "image/jpeg"
    assert max(Image.open(io.BytesIO(thumb.content)).size) == backend.THUMB_SIZE

    download = client.get(f"/api/clip/{clip_id}/file")
    assert download.content == png.getvalue()

    # Deleting the clip removes the stored file and its thumbnail
    assert client.delete(f"/api/clip/{clip_id}").status_code == 200
    assert [p for p in backend.FILES_PATH.rglob("*") if p.is_file()] == []
