# Command: /setup-sprint

Bootstrap **`sprint/`** dari **`brief/`** ketika proyek **belum punya struktur sprint** yang sah (kosong atau hanya placeholder). Ini adalah jalur **awal**: pohon sprint + baris pertama di master planning table + satu atau lebih sprint di **`backlog/`**.

## Trigger

`/setup-sprint`

Gunakan command ini **bukan** `/add-sprint` ketika:

- `sprint/backlog/`, `sprint/active/`, `sprint/archive/` belum ada atau kosong **dan**
- `sprint/01-sprint-planning.md` kosong / tidak berisi tabel sprint aktual.

---

## Mandatory reads (urutan)

1. **`.claude/skills/sprint-builder/SKILL.md`** — seluruh workflow, naming, workforce scaffold (`00-workforce-scaffold`), foundation tasks, promote/archive.
2. **`.claude/skills/brief-builder/SKILL.md`** — hanya jika langkah **Phase A** di bawah memerlukan penyempurnaan atau pembuatan brief kanonis.

---

## Phase A — Pastikan bahan brief siap

Single source of truth fitur tingkat proyek: **`brief/`** — idealnya **`brief/00_OVERVIEW.md`** plus **`brief/NN_*.md`** per fitur besar (kontrak sprint-builder).

| Situasi | Tindakan |
|--------|----------|
| **`brief/00_OVERVIEW.md`** ada (dan feature briefs jelas atau tidak diperlukan) | Lanjut Phase B. |
| Hanya ada **`brief/project-brief.md`** atau gabungan lain | Gunakan itu sebagai input utama untuk menyusun sprint; **sarankan** ke user untuk menyelaraskan ke **`00_OVERVIEW.md`** + `NN_FEATURE.md` lewat **`brief-builder`** pada giliran berikutnya — **jangan blokir** `/setup-sprint` jika isinya cukup untuk derive sprint. |
| **`brief/`** kosong atau tidak memadai untuk derive sprint | Jalankan alur **`.claude/skills/brief-builder/SKILL.md`** dulu sampai ada blueprint tertulis; **hentikan** dan laporkan — baru lanjut Phase B setelah user mengonfirmasi brief ada. |

> Sprint-builder **tidak mengganti** brief; brief menjadi **read-only** untuk planning kecuali user secara eksplisit menyuruh revisi via **`brief-builder`**.

---

## Phase B — Inisialisasi pohon `sprint/`

1. Buat folder bila belum ada:

   ```text
   sprint/backlog/
   sprint/active/
   sprint/archive/
   ```

2. Isi **`sprint/01-sprint-planning.md`** dari template:
   **`.claude/skills/sprint-builder/references/sprint-planning-template.md`**  
   - Sesuaikan link blueprint di header/table → **`brief/00_OVERVIEW.md`** atau dokumen brief utama yang dipakai project ini.
   - Boleh tulis catatan satu baris jika naming canonical sedang dalam migrasi (mis. `project-brief.md`).

---

## Phase C — Generate sprint pertama dari brief

Ikuti **Step 2** pada **`sprint-builder/SKILL.md`**:

1. Baca **`brief/00_OVERVIEW.md`** (atau surrogate utama) dan **`brief/NN_*.md`**. Pertimbangkan **`design/`** + **`design/flow.json`** jika ada (task FE tokens / wire screens per skill).
2. Tentukan **sprint urutan `NN`**: mulai **`01-<slug>`** kecuali aturan **workforce** mengharuskan **`00-workforce-scaffold`** lebih dulu — **ikut sprint-builder § Workforce-aware**.
3. Untuk setiap sprint backlog baru:
   - Buat **`sprint/backlog/NN-<slug>/sprint.md`** dari **`.claude/skills/sprint-builder/references/sprint-template.md`**.
   - Buat subfolder stack (**hanya** yang relevan): `frontend/`, `backend/`, `agent/`, `mcp/`, `mobile/` dengan task **`NN-<task>.md`** dari **`.claude/skills/sprint-builder/references/task-template.md`**.
4. Perbarui **`sprint/01-sprint-planning.md`**: tambahkan baris per sprint dengan status **`📋 Planned`**, link ke brief beraksi, link **`./backlog/NN-<slug>/`**, **`Created At`**.
5. **Jangan** memindahkan apa pun ke **`active/`** — promote adalah langkah manual / command terpisah kecuali user meminta eksplisit.

---

## Output & checklist

- [ ] **`sprint/backlog/`**, **`active/`**, **`archive/`** ada  
- [ ] **`sprint/01-sprint-planning.md`** terisi dari template + minimal satu baris sprint  
- [ ] Setiap sprint punya **`sprint/backlog/NN-<slug>/sprint.md`**  
- [ ] Task stack konsisten dengan scope brief + dependency / foundation per sprint-builder  
- [ ] Ringkasan untuk user: sprint apa dibuat, stack apa saja, row apa ditambahkan di master table  
- [ ] Jika brief tidak kanonis: satu kalimat rekomendasi menyelaraskan ke **`00_OVERVIEW.md`**

---

## References

- `.claude/skills/sprint-builder/SKILL.md`
- `.claude/skills/brief-builder/SKILL.md`
- `.claude/skills/sprint-builder/references/sprint-planning-template.md`
- `.claude/skills/sprint-builder/references/sprint-template.md`
- `.claude/skills/sprint-builder/references/task-template.md`
