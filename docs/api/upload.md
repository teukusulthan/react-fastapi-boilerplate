# API — Upload (`/upload`)

Code: `apps/backend/router/upload.py`, `service/upload.py`, `dto/upload.py`, `util/s3.py`.
The envelope, `FindDTO` and error codes are described in [`../api-spec.md`](../api-spec.md).

Files are stored in S3-compatible storage (AWS S3, MinIO or Supabase Storage via `BE_S3_*`). The
metadata goes in the `uploads` collection or table.

**Access:**
- Signed-in **users** only; an `X-Internal-Token` gets 403.
- Users see and delete **their own** files. Other users' files return 404.
- Admins see and delete everything.
- `createdBy` always comes from the token.

## Response — `UploadResponse`

```json
{
  "id": "uuid", "objectKey": "uploads/general/<uuid>-report.pdf", "filename": "report.pdf",
  "mimeType": "application/pdf", "filesize": 18234, "folder": "general", "tags": ["q3", "finance"],
  "widgetId": null, "dashboardId": null, "workspaceId": null, "connectionId": null,
  "createdBy": "uuid", "createdAt": "…", "updatedAt": "…",
  "downloadUrl": "https://…presigned…"
}
```

`downloadUrl` is a short-lived presigned URL (`BE_S3_PRESIGN_TTL`), served as an attachment. It is only
set by `upload-file` and `get-one`, and it is `null` when S3 is not configured.

## Endpoints

### `POST /upload/upload-file` → 201

`multipart/form-data`. Field names are camelCase; unknown fields return 422.

| Field | Type | Notes |
|---|---|---|
| `file` | file, required | Streamed. Over `BE_UPLOAD_MAX_SIZE_MB` → **413**; empty → 422 |
| `folder` | string | Default `general`; 1–5 segments of `[A-Za-z0-9_-]` separated by `/` |
| `filename` | string | Display-name override (the extension comes from the detected type) |
| `tags` | string | Comma-separated, ≤ 20 tags of `[A-Za-z0-9_.:-]{1,50}` |
| `widgetId`, `dashboardId`, `workspaceId`, `connectionId` | string | Free references (≤ 64 chars) |
| `extractFile` | `"true"`/`"false"` | Publish a Kafka event to `BE_KAFKA_TOPIC_FILE_EXTRACTION` (503 if Kafka is not configured) |
| `rescaleFile` | `"true"`/`"false"` | Images only (otherwise 422): downscale, keeping the format |
| `scaleFactor` | number in (0, 1] | With `rescaleFile`: multiply both sides by this factor |

The MIME type is detected from the file **content** (libmagic), not from the client header. Types
outside `BE_UPLOAD_ALLOWED_TYPES` return **415**. HTML, SVG, XML and JS are blocked unless you list them
explicitly. Images are only resized when `rescaleFile=true`: they are scaled by `scaleFactor` and capped
at `BE_UPLOAD_IMAGE_MAX_DIMENSION`, keeping the format. The object key is
`{BE_UPLOAD_KEY_PREFIX}/{folder}/{uuid}-{safe-name}`, and files over 8 MiB use multipart upload.
Returns 503 `CONFIGURATION_ERROR` when S3 (or libmagic) is unavailable, and 503 `SERVICE_UNAVAILABLE`
when storage errors.

```bash
curl -b cookies.txt -F file=@report.pdf -F folder=reports -F tags=q3,finance \
  http://localhost:8020/upload/upload-file
```

### `POST /upload/get-all`

Body: `FindDTO`. The results are scoped to your own files unless you are a superuser.

| | Fields |
|---|---|
| search | `filename`, `folder` |
| filter | `id`, `filename`, `mimeType`, `filesize`, `folder`, `tags` (list), `widgetId`, `dashboardId`, `workspaceId`, `connectionId`, `createdBy`, `createdAt`, `updatedAt` |
| sort | `filename`, `mimeType`, `filesize`, `createdAt`, `updatedAt` |

### `GET /upload/get-one?id=`

200 `UploadResponse` with `downloadUrl`; 404 for unknown or other users' files.

### `DELETE /upload/delete?id=`

Deletes the stored object and its metadata. 200 `{message: "File deleted"}`; 404 for unknown or other
users' files.
