# Command: /add-sprint

**Menambah** satu atau lebih sprint ke struktur yang **sudah ada** — perilaku **append-only**. Dipakai ketika brief **direvisi**, **fitur baru** ditambahkan (`brief/NN_*.md` baru), atau scope berubah setelah sprint awal sudah direncanakan.

Ini **bukan** mengganti baris sprint lama tanpa jejak: sprint yang dibatalkan mendapat status **`❌ Cancelled`** dengan alasan satu baris (per sprint-builder).

## Trigger

`/add-sprint`

Prasyarat: **`sprint/`** sudah ter-bootstrap (`01-sprint-planning.md` berisi tabel, dan/atau sudah ada folder di **`backlog/`**, **`active/`**, atau **`archive/`**).

> Kalau belum ada apa pun di **`sprint/`**, gunakan **`/setup-sprint`**.

---

## Mandatory reads

1. **`.claude/skills/sprint-builder/SKILL.md`** — Step 2 (draft sprint), naming, workforce/foundation, append-only rules.
2. Brief yang **berubah atau baru** — baca diff / file penuh **`brief/00_OVERVIEW.md`**, **`brief/NN_*.md`**, dan **`brief/project-brief.md`** jika masih dipakai sebagai sumber.

---

## Step 1 — Reconcile dengan brief terbaru

1. Identifikasi **apa yang berubah** dibanding baseline sprint terakhir:
   - revisi **`00_OVERVIEW.md`** / overview surrogate;
   - penambahan **`NN_FEATURE.md`**;
   - penghapusan atau penggabungan fitur (flag dampak ke sprint backlog aktif).
2. **Jangan** menghapus sprint folders atau baris tabel untuk sprint yang sudah pernah direncanakan — gunakan status **`❌ Cancelled`** atau **`⏸ Paused`** + **`## Revision <date>`** pada **`sprint.md`** yang relevan jika scope sprint lama tidak lagi valid (jelaskan di ringkasan user).

---

## Step 2 — Tentukan nomor sprint berikutnya (`NN`)

Hitung **`NN`** dari **semua** folder sprint yang ada di:

- `sprint/backlog/*`
- `sprint/active/*`
- `sprint/archive/*`

Ambil **nomor numerik prefix tertinggi** (`00`, `01`, …), lalu increment untuk sprint baru: misalnya `03-dashboard` jika yang tertinggi adalah `02`.

- Slug: **`NN-<kebab-slug>`**, ≤ ~3 kata, konsisten dengan **`sprint-builder`**.
- Pastikan tidak bentrok dengan nama folder yang sudah ada.

---

## Step 3 — Buat sprint backlog baru (append)

Untuk setiap **paket kerja baru** yang harus mengakomodasi perubahan brief:

1. Buat **`sprint/backlog/NN-<slug>/sprint.md`** dari **`.claude/skills/sprint-builder/references/sprint-template.md`** — jelaskan di overview **mengapa** sprint ini ada (revisi brief X, fitur Y baru, dll.).
2. Tambahkan task per stack (**task-template.md**) dengan **`Depends on:`** ke foundation / sprint lain bila perlu.
3. **Append** baris baru di **`sprint/01-sprint-planning.md`**:
   - Status default **`📋 Planned`**
   - **`Brief`**: link ke file brief yang menjadi pemicu perubahan
   - **`References`**: `./backlog/NN-<slug>/`
   - **`Depends On`**: sprint lain jika ada urutan keras (mis. setelah foundation workforce)

**Jangan** memindahkan sprint lain antar **`backlog` / `active` / `archive`** kecuali user meminta eksplisit.

---

## Step 4 — Konflik dengan sprint yang sedang aktif

Jika **`sprint/active/`** berisi sprint dan brief baru **mengubah kontrak** yang sama:

- Tambahkan catatan di **`sprint.md`** sprint baru atau di sprint aktif (append **`## Revision`**) — jangan menghapus task yang sudah `[x]`.
- Beri **peringatan satu paragraf** ke user: pekerjaan aktif mungkin perlu sinkron manual atau task tambahan di sprint baru.

---

## Output & checklist

- [ ] Nomor **`NN`** unik, tidak tabrak folder/archive  
- [ ] Folder baru hanya di **`sprint/backlog/`** (kecuali user minta promote)  
- [ ] **`01-sprint-planning.md`** mendapat **baris baru** (append); tidak menghapus histori  
- [ ] Link brief di kolom **Brief** menunjuk file yang direvisi / ditambahkan  
- [ ] Ringkasan untuk user: sprint baru apa, pemicu perubahan apa, dependency apa  

---

## References

- `.claude/skills/sprint-builder/SKILL.md`
- `.claude/skills/brief-builder/SKILL.md` (jika brief perlu dilengkapi sebelum task konkret)
- `.claude/skills/sprint-builder/references/sprint-planning-template.md`
- `.claude/skills/sprint-builder/references/sprint-template.md`
- `.claude/skills/sprint-builder/references/task-template.md`
