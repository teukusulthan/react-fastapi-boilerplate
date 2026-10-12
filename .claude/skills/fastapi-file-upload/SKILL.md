---
name: fastapi-file-upload
description: "The apps/backend upload module and how to extend it: POST /upload/upload-file (multipart, field `file`) with streaming size cap, magic-byte MIME detection (libmagic) against BE_UPLOAD_ALLOWED_TYPES, sanitized object keys, optional Pillow downscale, boto3 managed (multipart) transfer to S3/MinIO/Supabase Storage via util/s3.py S3Storage, metadata rows in the `uploads` entity, presigned download URLs, optional Kafka extraction event via util/kafka.py, owner scoping. Use when touching uploads, S3 storage, attachments, file type rules, or adding file attachments to another resource."
---

# fastapi-file-upload — Upload service, S3 storage, extraction events

The upload feature is complete in the boilerplate. Read the code before changing it:

| File (under `apps/backend/`) | Contents |
|---|---|
| `router/upload.py` | `UploadLimitRoute` (413 while streaming), `router = APIRouter(prefix="/upload", dependencies=[Depends(require_auth)], route_class=UploadLimitRoute)`, 4 endpoints |
| `dto/upload.py` | `UploadFileForm` (multipart form model), `FindUploadDTO(FindDTO)`, `UploadResponse` |
| `service/upload.py` | pure helpers (`sanitize_folder`, `safe_stem`, `extension_for`, `detect_mime`, `check_allowed`, `resize_image`), `UploadService(CrudService)`, `get_storage_factory`, `get_upload_service`, `UploadServiceDep` |
| `util/s3.py` | `S3Storage` (`put_object`, `upload_fileobj`, `get_object`, `delete_object`, `presigned_get_url`), `get_s3_storage(settings)` |
| `util/kafka.py` | `get_kafka_producer`, `publish(settings, topic, value, key=)`, `close_kafka_producer` |
| `db/schema.py` | `UPLOADS` entity (`object_key` unique) |
| `tests/modules/test_upload.py`, `tests/modules/conftest.py` | behaviour spec + `FakeS3Client`, `with_storage`, `fake_storage` fixtures |

Web client: `apps/web/src/services/upload.service.ts` (`uploadFile(file, options, onProgress)`).

## Use this skill when

- Changing upload rules (types, size, folder/key layout, resize).
- Pointing storage at AWS S3, MinIO or Supabase Storage.
- Attaching uploaded files to another entity, or emitting extraction events.
- Writing tests that involve files.

## Endpoints

All require an authenticated **user** (`require_auth`; `X-Internal-Token` → 403). Non-admins see and
delete only their own files (others' → 404); superusers see all.

| Method | Path | Notes |
|---|---|---|
| POST | `/upload/upload-file` | `multipart/form-data` → 201 `UploadResponse` (+ `downloadUrl`) |
| POST | `/upload/get-all` | `FindUploadDTO`; scoped with `extra_where` `created_by == me` for non-admins |
| GET | `/upload/get-one?id=` | includes a presigned `downloadUrl` (null if S3 is not configured) |
| DELETE | `/upload/delete?id=` | deletes the S3 object, then the row |

Form fields (`UploadFileForm`, camelCase, unknown fields → 422): `file` (required),
`folder` (default `general`; 1–5 segments of `[A-Za-z0-9_-]` joined by `/`), `filename`
(display-name override), `tags` (CSV, ≤20, `[A-Za-z0-9_.:-]{1,50}`), `widgetId`, `dashboardId`,
`workspaceId`, `connectionId` (free-form refs, metadata only), `extractFile` (bool), `rescaleFile`
(bool, images only), `scaleFactor` (0 < x ≤ 1, with `rescaleFile`). Booleans arrive as strings
(`"true"`). `createdBy` is never accepted — it is the caller.

## Pipeline (`UploadService.upload`)

1. Body cap while streaming in `UploadLimitRoute`: `Content-Length` or streamed bytes >
   `upload_max_bytes + 256 KiB` → 413 `PAYLOAD_TOO_LARGE` before spooling to disk.
2. `extractFile` without Kafka configured → 503 `CONFIGURATION_ERROR` (checked first).
3. Exact size: empty → 422, > `BE_UPLOAD_MAX_SIZE_MB` → 413.
4. `detect_mime(first 8 KiB, client name)` via libmagic; the extension may only refine within the
   same family (text → csv/json/markdown, zip → OOXML, OLE → legacy Office). `check_allowed`:
   `application/octet-stream`/empty are **never** accepted; anything not in
   `BE_UPLOAD_ALLOWED_TYPES` → 415 `UNSUPPORTED_MEDIA_TYPE`; active content (HTML, SVG, XML, JS) only
   when listed explicitly (logged as a warning). libmagic missing → 503 `CONFIGURATION_ERROR`.
5. `storage = self.storage()` → 503 `CONFIGURATION_ERROR` if S3 is not configured (before any work).
6. Optional `resize_image` (format preserved, EXIF orientation applied, longest side ≤
   `BE_UPLOAD_IMAGE_MAX_DIMENSION`, animated images skipped; non-image → 422).
7. Key `{BE_UPLOAD_KEY_PREFIX}/{folder}/{uuid}-{safe_stem}{ext}`; the extension always matches the
   detected type.
8. `storage.upload_fileobj(key, body, mime, content_disposition='attachment; filename="…"',
   metadata={...}, transfer_config=TransferConfig(multipart_threshold=8 MiB, …))` — boto3 managed
   transfer, multipart above 8 MiB, streamed from the spooled file (never fully in memory). boto
   errors → 503 `SERVICE_UNAVAILABLE`.
9. Insert the `uploads` row (`created_by` = caller); if that fails the object is deleted again.
10. `extractFile` → `publish(settings, KAFKA_TOPIC_FILE_EXTRACTION, {uploadId, bucket, objectKey,
    filename, mimeType, filesize, folder, tags, createdBy}, key=id)` — best effort, logged on failure.

## Settings (`core/config.py`, `.env.example`)

Everything is optional — the app boots without S3/Kafka and the upload endpoints answer 503
`CONFIGURATION_ERROR` until configured.

| Env | Default | Meaning |
|---|---|---|
| `BE_UPLOAD_MAX_SIZE_MB` | 25 | per-file cap (`settings.upload_max_bytes`) |
| `BE_UPLOAD_ALLOWED_TYPES` | images, pdf, txt, csv, json, zip, Office (see `Settings`) | CSV or JSON list of MIME types |
| `BE_UPLOAD_IMAGE_MAX_DIMENSION` | 2048 | resize cap |
| `BE_UPLOAD_KEY_PREFIX` | `uploads` | object key prefix |
| `BE_S3_ENDPOINT_URL` / `BE_S3_REGION` / `BE_S3_ACCESS_KEY_ID` / `BE_S3_SECRET_ACCESS_KEY` / `BE_S3_BUCKET` | — / `us-east-1` | `s3_configured` needs bucket + both keys |
| `BE_S3_FORCE_PATH_STYLE` | true | path-style addressing (MinIO, Supabase) |
| `BE_S3_PRESIGN_TTL` | 900 | presigned URL lifetime (s) |
| `BE_KAFKA_BOOTSTRAP_SERVERS` / `BE_KAFKA_CLIENT_ID` / `BE_KAFKA_TOPIC_FILE_EXTRACTION` | — | `kafka_configured` needs bootstrap servers |

Supabase Storage: `BE_S3_ENDPOINT_URL=https://<ref>.supabase.co/storage/v1/s3`, region = project
region, keys from Storage → S3 Connection, `BE_S3_FORCE_PATH_STYLE=true`.
The Docker image installs `libmagic1` (`apps/backend/Dockerfile`); on a dev machine install
libmagic (`apt install libmagic1`, `brew install libmagic`) or MIME detection returns 503.

## Rules

MUST
- Keep S3/Kafka access in `util/s3.py` / `util/kafka.py`; services receive storage through the
  `get_storage_factory` dependency (lazy, so non-upload routes work without S3).
- Call boto3/Kafka only from sync code (they block). Upload routes are sync `def`.
- Detect the type from content, not from the client's `Content-Type` or extension.
- Serve files as attachments (`Content-Disposition: attachment`) via presigned URLs; never proxy
  bytes through the API unless a feature truly needs it.
- Raise `ConfigurationError` for missing configuration and `ServiceUnavailableError` for storage
  outages; never surface boto/Kafka exception text to clients.

MUST NOT
- Trust `filename`/`folder` for paths (always `sanitize_folder` + `safe_stem`).
- Accept `application/octet-stream` or active content by default.
- Read the whole upload into memory (`await file.read()`) for large files.
- Take `createdBy` (or bucket/key) from the request.
- Create a boto3 client per request (`get_s3_storage` caches per configuration).

## Extending

- **Allow a new type:** add the MIME to `BE_UPLOAD_ALLOWED_TYPES` (env) or the `Settings` default; if
  libmagic reports a generic parent type (zip, OLE, text/plain), add the refinement to the matching
  `_*_REFINEMENTS` set in `service/upload.py`, and a canonical extension to `_CANONICAL_EXT` if
  `mimetypes` lacks one. Add a test in `tests/modules/test_upload.py`.
- **Attach files to another entity** (e.g. a `note`): keep `/upload/upload-file` as the only write
  path, store the returned upload `id` on your entity (`attachment_ids` `LIST` field or a
  `<x>_id` field on `UPLOADS` + migration), validate ids with `uploads_repo.get_many_by_ids(...)`
  and ownership (`created_by == actor.id` unless superuser) in your service, and decide what happens on
  delete (detach or delete objects through `UploadService.delete_for`).
- **Different storage backend:** keep the `S3Storage` method surface (`upload_fileobj`,
  `delete_object`, `presigned_get_url`, `bucket`) and return your implementation from
  `get_storage_factory`; nothing else in the service changes.
- **Other async processing:** publish an event with `util.kafka.publish` after the row is stored;
  check `settings.kafka_configured` if it is best effort.

## Testing

The module tests never touch S3: `tests/modules/conftest.py` defines `FakeS3Client` and the fixtures
`fake_s3`, `with_storage(app)` and `fake_storage` (it installs
`app.dependency_overrides[get_storage_factory] = lambda: lambda: storage`). Example:

```python
def test_upload(client, fake_storage, user_headers):
    r = client.post("/upload/upload-file", files={"file": ("a.txt", b"hello\n", "text/plain")},
                    data={"folder": "reports", "tags": "a,b"}, headers=user_headers)
    assert r.status_code == 201
    assert fake_storage.objects[r.json()["data"]["objectKey"]]["ContentType"] == "text/plain"
```

Settings variants: `with TestClient(with_storage(make_app(make_settings(UPLOAD_MAX_SIZE_MB=1)))) as c:`.
Without `fake_storage` the endpoint returns 503 `CONFIGURATION_ERROR` (also tested).

## Checklist

- [ ] Type rules changed → tests for accepted + rejected (415) cases
- [ ] New settings in `core/config.py` + `.env.example`
- [ ] No boto3/Kafka import outside `util/` and `service/upload.py`
- [ ] Owner scoping kept for every read/delete path
- [ ] Web `upload.service.ts` updated if form fields change

## Common mistakes

- Sending the file under a field other than `file` → 422.
- Expecting `downloadUrl` in `get-all` items (only `upload-file` and `get-one` presign).
- Forgetting libmagic locally and debugging a 503 as an S3 problem.
- Assuming the `.env.example` value of `BE_UPLOAD_ALLOWED_TYPES` equals the `Settings` default — it is
  shorter (no Office types); an env value replaces the default entirely.
