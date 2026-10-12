"""/upload: validation (size, magic-byte MIME, names, folders), storage, resize, scoping, Kafka."""

from __future__ import annotations

import io
import re

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import service.upload as upload_module

MISSING = "00000000-0000-4000-8000-000000000000"


def png_bytes(size=(40, 20), fmt="PNG", color=(200, 10, 10)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, format=fmt)
    return buffer.getvalue()


def _upload(client, headers, content=b"hello world\n", name="notes.txt", ctype="text/plain", **data):
    return client.post("/upload/upload-file", files={"file": (name, content, ctype)}, data=data, headers=headers)


# ------------------------------------------------------------- happy path
def test_upload_stores_object_and_metadata(client, fake_storage, user_headers, regular_user, uploads_repo):
    response = _upload(client, user_headers, name="../../My Report (final).txt", folder="reports/2024", tags="a, b,a")
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["filename"] == "My-Report-final.txt"
    assert data["mimeType"] == "text/plain" and data["filesize"] == 12
    assert data["folder"] == "reports/2024" and data["tags"] == ["a", "b"]
    assert data["createdBy"] == regular_user["id"]
    assert re.fullmatch(rf"uploads/reports/2024/{data['id']}-My-Report-final\.txt", data["objectKey"])
    assert data["downloadUrl"].startswith("https://s3.test/test-bucket/uploads/")

    stored = fake_storage.objects[data["objectKey"]]
    assert stored["body"] == b"hello world\n"
    assert stored["ContentType"] == "text/plain"
    assert stored["ContentDisposition"].startswith("attachment;")
    assert uploads_repo.get_by_id(data["id"])["bucket"] == "test-bucket"


def test_created_by_cannot_be_spoofed(client, fake_storage, user_headers):
    response = _upload(client, user_headers, createdBy="someone-else")
    assert response.status_code == 422
    assert response.json()["data"][0]["field"] == "createdBy"


def test_content_type_comes_from_magic_bytes(client, fake_storage, user_headers):
    # PNG bytes disguised as HTML: stored as image/png with a .png key (never served as HTML)
    response = _upload(client, user_headers, content=png_bytes(), name="evil.html", ctype="text/html")
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["mimeType"] == "image/png" and data["filename"] == "evil.png"
    assert fake_storage.objects[data["objectKey"]]["ContentType"] == "image/png"
    # CSV detected as text, refined by the extension within the text family
    csv = _upload(client, user_headers, content=b"a,b\n1,2\n", name="data.csv", ctype="application/octet-stream")
    assert csv.status_code == 201 and csv.json()["data"]["mimeType"] == "text/csv"
    # text named .exe -> text/plain with a .txt name
    exe = _upload(client, user_headers, content=b"just text\n", name="setup.exe")
    assert exe.json()["data"]["filename"] == "setup.txt"


@pytest.mark.parametrize(
    ("content", "name"),
    [
        (b"<!DOCTYPE html><html><body><script>alert(1)</script></body></html>", "page.html"),
        (b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>', "img.svg"),
        (bytes(range(256)) * 8, "blob.bin"),  # application/octet-stream
        (b"\x7fELF\x02\x01\x01" + b"\x00" * 64, "a.png"),  # executable disguised as an image
    ],
)
def test_disallowed_types_are_rejected(client, fake_storage, user_headers, content, name):
    response = _upload(client, user_headers, content=content, name=name, ctype="image/png")
    assert response.status_code == 415
    assert response.json()["metaData"]["errorCode"] == "UNSUPPORTED_MEDIA_TYPE"
    assert fake_storage.objects == {}


def test_octet_stream_never_allowed_even_if_configured(make_app, make_settings, with_storage, user_headers):
    settings = make_settings(UPLOAD_ALLOWED_TYPES="application/octet-stream,text/plain")
    with TestClient(with_storage(make_app(settings))) as client:
        assert _upload(client, user_headers, content=bytes(range(256)) * 8, name="x.bin").status_code == 415


def test_active_content_only_when_explicitly_allowed(make_app, make_settings, with_storage, fake_s3, user_headers):
    settings = make_settings(UPLOAD_ALLOWED_TYPES="text/html")
    with TestClient(with_storage(make_app(settings))) as client:
        response = _upload(client, user_headers, content=b"<!DOCTYPE html><html></html>", name="p.html")
        assert response.status_code == 201
        assert fake_s3.objects[response.json()["data"]["objectKey"]]["ContentDisposition"].startswith("attachment")


@pytest.mark.parametrize(
    ("data", "field"),
    [
        ({"folder": "../etc"}, "folder"),
        ({"folder": "a/../../b"}, "folder"),
        ({"folder": "a/b/c/d/e/f"}, "folder"),
        ({"folder": "with space"}, "folder"),
        ({"tags": "ok,bad tag"}, "tags"),
        ({"scaleFactor": "2"}, "scaleFactor"),
        ({"unknownField": "1"}, "unknownField"),
    ],
)
def test_form_validation(client, fake_storage, user_headers, data, field):
    response = _upload(client, user_headers, **data)
    assert response.status_code == 422
    assert response.json()["data"][0]["field"] == field


def test_missing_file_part(client, fake_storage, user_headers):
    response = client.post("/upload/upload-file", data={"folder": "x"}, headers=user_headers)
    assert response.status_code == 422 and response.json()["data"][0]["field"] == "file"


def test_empty_file(client, fake_storage, user_headers):
    response = _upload(client, user_headers, content=b"")
    assert response.status_code == 422


def test_size_limits(make_app, make_settings, with_storage, user_headers, fake_s3):
    with TestClient(with_storage(make_app(make_settings(UPLOAD_MAX_SIZE_MB=1)))) as client:
        just_over = b"a" * (1024 * 1024 + 1)  # under the streaming cap (overhead), caught by the exact check
        response = _upload(client, user_headers, content=just_over)
        assert response.status_code == 413
        assert response.json()["metaData"]["errorCode"] == "PAYLOAD_TOO_LARGE"

        huge = b"a" * (2 * 1024 * 1024)  # rejected while streaming, before multipart parsing finishes
        response = _upload(client, user_headers, content=huge)
        assert response.status_code == 413 and response.json()["metaData"]["errorCode"] == "PAYLOAD_TOO_LARGE"

        def chunks():
            for _ in range(40):
                yield b"x" * 65536

        streamed = client.post(
            "/upload/upload-file",
            content=chunks(),
            headers={**user_headers, "content-type": "multipart/form-data; boundary=zzz"},
        )
        assert streamed.status_code == 413
        assert _upload(client, user_headers).status_code == 201
    assert len(fake_s3.objects) == 1


def test_s3_not_configured(client, user_headers, uploads_repo):
    response = _upload(client, user_headers)
    assert response.status_code == 503
    assert response.json()["metaData"]["errorCode"] == "CONFIGURATION_ERROR"
    assert uploads_repo.count() == 0
    # listing still works without S3
    assert client.post("/upload/get-all", json={}, headers=user_headers).status_code == 200


# ------------------------------------------------------------------ resize
@pytest.mark.parametrize(("fmt", "mime", "ext"), [("PNG", "image/png", "png"), ("JPEG", "image/jpeg", "jpg")])
def test_rescale_keeps_format(client, fake_storage, user_headers, fmt, mime, ext):
    content = png_bytes((400, 200), fmt=fmt)
    response = _upload(client, user_headers, content=content, name=f"pic.{ext}", rescaleFile="true", scaleFactor="0.5")
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["mimeType"] == mime
    stored = fake_storage.objects[data["objectKey"]]["body"]
    with Image.open(io.BytesIO(stored)) as image:
        assert image.size == (200, 100) and image.format == fmt
    assert data["filesize"] == len(stored)


def test_rescale_caps_dimension_and_rejects_non_images(make_app, make_settings, with_storage, fake_s3, user_headers):
    with TestClient(with_storage(make_app(make_settings(UPLOAD_IMAGE_MAX_DIMENSION=100)))) as client:
        response = _upload(client, user_headers, content=png_bytes((400, 200)), name="a.png", rescaleFile="true")
        stored = fake_s3.objects[response.json()["data"]["objectKey"]]["body"]
        with Image.open(io.BytesIO(stored)) as image:
            assert image.size == (100, 50)
        not_image = _upload(client, user_headers, rescaleFile="true")
        assert not_image.status_code == 422 and not_image.json()["data"][0]["field"] == "rescaleFile"


def test_without_rescale_image_is_untouched(client, fake_storage, user_headers):
    content = png_bytes((400, 200))
    data = _upload(client, user_headers, content=content, name="a.png").json()["data"]
    assert fake_storage.objects[data["objectKey"]]["body"] == content


# ------------------------------------------------------------- read/delete
def test_scoping_and_delete(
    client, fake_storage, user_headers, admin_headers, auth_headers, user_factory, uploads_repo
):
    mine = _upload(client, user_headers).json()["data"]
    stranger = auth_headers(user_factory())
    theirs = _upload(client, stranger, name="other.txt").json()["data"]

    listed = client.post("/upload/get-all", json={}, headers=user_headers).json()
    assert [u["id"] for u in listed["data"]] == [mine["id"]]
    assert listed["metaData"]["pagination"]["totalElements"] == 1
    assert (
        client.post("/upload/get-all", json={}, headers=admin_headers).json()["metaData"]["pagination"]["totalElements"]
        == 2
    )

    # other users' files are invisible (404, not 403)
    assert client.get("/upload/get-one", params={"id": theirs["id"]}, headers=user_headers).status_code == 404
    assert client.delete("/upload/delete", params={"id": theirs["id"]}, headers=user_headers).status_code == 404
    assert theirs["objectKey"] in fake_storage.objects

    got = client.get("/upload/get-one", params={"id": mine["id"]}, headers=user_headers).json()["data"]
    assert got["downloadUrl"] and got["objectKey"] == mine["objectKey"]

    assert client.delete("/upload/delete", params={"id": mine["id"]}, headers=user_headers).status_code == 200
    assert mine["objectKey"] not in fake_storage.objects and uploads_repo.get_by_id(mine["id"]) is None
    assert client.delete("/upload/delete", params={"id": mine["id"]}, headers=user_headers).status_code == 404
    assert client.delete("/upload/delete", params={"id": MISSING}, headers=user_headers).status_code == 404

    # admins can delete anyone's file
    assert client.delete("/upload/delete", params={"id": theirs["id"]}, headers=admin_headers).status_code == 200
    assert fake_storage.deleted == [mine["objectKey"], theirs["objectKey"]]


def test_get_all_filters(client, fake_storage, user_headers):
    _upload(client, user_headers, tags="x,y", widgetId="w1")
    _upload(client, user_headers, content=png_bytes(), name="p.png", tags="y")
    body = {"filters": [{"field": "tags", "operator": "all", "value": {"isOneOf": ["x", "y"]}}]}
    assert len(client.post("/upload/get-all", json=body, headers=user_headers).json()["data"]) == 1
    body = {"filters": [{"field": "mimeType", "operator": "is", "value": {"is": "image/png"}}], "orderBy": "filesize"}
    assert len(client.post("/upload/get-all", json=body, headers=user_headers).json()["data"]) == 1
    bad = {"filters": [{"field": "objectKey", "operator": "is", "value": {"is": "x"}}]}
    assert client.post("/upload/get-all", json=bad, headers=user_headers).status_code == 422
    created_by_scope = {"filters": [{"field": "createdBy", "operator": "is not", "value": {"is": "me"}}]}
    data = client.post("/upload/get-all", json=created_by_scope, headers=user_headers).json()
    assert data["metaData"]["pagination"]["totalElements"] == 2  # client filter cannot widen the owner scope


def test_metadata_failure_removes_object(client, fake_storage, user_headers, monkeypatch):
    def boom(self, data):
        raise RuntimeError("db down")

    from db.mongo.repository import MongoRepository

    monkeypatch.setattr(MongoRepository, "insert", boom)
    try:
        from db.supabase.repository import PostgresRepository

        monkeypatch.setattr(PostgresRepository, "insert", boom)
    except ImportError:  # pragma: no cover
        pass
    response = _upload(client, user_headers)
    assert response.status_code == 500
    assert fake_storage.objects == {} and len(fake_storage.deleted) == 1


# ------------------------------------------------------------------- kafka
def test_extract_requires_kafka(client, fake_storage, user_headers):
    response = _upload(client, user_headers, extractFile="true")
    assert response.status_code == 503 and response.json()["metaData"]["errorCode"] == "CONFIGURATION_ERROR"
    assert fake_storage.objects == {}


def test_extract_publishes_event(make_app, make_settings, with_storage, fake_s3, user_headers, monkeypatch):
    sent = []
    monkeypatch.setattr(upload_module, "publish", lambda settings, topic, value, key=None: sent.append((topic, value)))
    settings = make_settings(KAFKA_BOOTSTRAP_SERVERS="kafka:9092", KAFKA_TOPIC_FILE_EXTRACTION="file-extraction")
    with TestClient(with_storage(make_app(settings))) as client:
        data = _upload(client, user_headers, extractFile="true").json()["data"]
    assert sent == [
        (
            "file-extraction",
            {
                "uploadId": data["id"],
                "bucket": "test-bucket",
                "objectKey": data["objectKey"],
                "filename": "notes.txt",
                "mimeType": "text/plain",
                "filesize": 12,
                "folder": "general",
                "tags": [],
                "createdBy": data["createdBy"],
            },
        )
    ]


def test_extract_failure_does_not_fail_upload(make_app, make_settings, with_storage, user_headers, monkeypatch):
    def fail(*args, **kwargs):
        raise ConnectionError("broker down")

    monkeypatch.setattr(upload_module, "publish", fail)
    settings = make_settings(KAFKA_BOOTSTRAP_SERVERS="kafka:9092", KAFKA_TOPIC_FILE_EXTRACTION="t")
    with TestClient(with_storage(make_app(settings))) as client:
        assert _upload(client, user_headers, extractFile="true").status_code == 201


# ------------------------------------------------------------ pure helpers
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("../../etc/passwd", "passwd"),
        ("C:\\Users\\x\\évil name.PHP.jpg", "evil-name.PHP"),
        ("...", "file"),
        ("a\x00b.txt", "ab"),
        ("", "file"),
    ],
)
def test_safe_stem(raw, expected):
    assert upload_module.safe_stem(raw) == expected
