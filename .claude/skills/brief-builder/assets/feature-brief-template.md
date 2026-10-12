# Modul [Nama Modul]

> Template feature brief — jembatan bisnis-teknis. Tidak ada SQL, tidak ada library version, tidak ada wireframe ASCII layout dashboard, tidak ada REST endpoint YAML. Cukup detail untuk derive task downstream tanpa ambiguitas, tapi tetap readable untuk klien non-teknis.

## 1. Gambaran Umum

[1-2 paragraf — apa modul ini, perannya di sistem keseluruhan, dan kenapa modul ini ada. Bahasa bisnis, bukan teknis.]

### 1.1 Tujuan Modul

| Tujuan | Deskripsi |
|--------|-----------|
| [Tujuan 1] | [Penjelasan singkat dari perspektif value yang dihasilkan] |
| [Tujuan 2] | [...] |
| [Tujuan 3] | [...] |
| [Tujuan 4] | [...] |

### 1.2 Target Pengguna

| Pengguna | Kebutuhan |
|----------|-----------|
| [Jabatan / Role 1] | [Apa yang mereka cari di modul ini] |
| [Jabatan / Role 2] | [...] |
| [Jabatan / Role 3 — opsional] | [...] |

---

## 2. Fitur Utama

[Pecah modul ini menjadi 2-4 sub-fitur. Setiap sub-fitur punya: deskripsi, tabel komponen visual deskriptif, dan list interaksi UX. **TIDAK ADA wireframe ASCII layout.**]

### 2.1 [Nama Sub-Fitur 1]

**Deskripsi**: [1-2 kalimat tentang apa yang ditampilkan/dilakukan di sub-fitur ini.]

**Komponen Visual**:

| Komponen | Tipe | Data | Update |
|----------|------|------|--------|
| [Nama komponen 1] | [Kartu ringkasan / Grafik garis tren / Indikator status warna / Tabel daftar / Peta lokasi / Modal detail / Filter bar] | [Data yang ditampilkan, deskriptif] | [Real-time / Per menit / Per jam / Per hari / Manual refresh] |
| [Nama komponen 2] | [...] | [...] | [...] |

> Catatan vocabulary: pakai bahasa deskriptif, BUKAN istilah teknis library. Contoh:
> - ✅ "kartu ringkasan", "grafik garis tren", "indikator status warna", "tabel daftar dengan filter", "peta lokasi interaktif", "modal detail"
> - ❌ "Card component", "Line chart", "Gauge Chart", "TanStack Table", "Mapbox layer"

**Interaksi**:

- [Aksi user 1 yang konkret — apa yang user lakukan di komponen ini]
- [Aksi user 2]
- [Aksi user 3 — kalau ada filter, sebut filter berdasarkan apa]
- [Aksi user 4 — kalau ada sort, sebut sort berdasarkan apa]

### 2.2 [Nama Sub-Fitur 2]

[Format sama dengan 2.1]

### 2.3 [Nama Sub-Fitur 3 — opsional]

[Format sama dengan 2.1]

---

## 3. Navigasi & Interaksi

> Section ini menjawab pertanyaan: **"User klik X di mana, mengarah ke mana, bawa context apa?"** Wajib ada untuk setiap modul. Tanpa ini, sprint-builder akan tanya balik atau improvise.

### 3.1 Peta Navigasi

| Dari Layar / Komponen | User Klik / Aksi | Menuju Ke | Context yang Dibawa |
|----------------------|------------------|-----------|---------------------|
| [Nama layar / komponen sumber] | [Tombol / baris / kartu / link yang diklik] | [Layar tujuan: modul lain, modal, halaman detail, dst] | [Filter aktif / ID record / parameter yang ikut] |
| [...] | [...] | [...] | [...] |
| [...] | [...] | [...] | [...] |

### 3.2 Decision Branch (kalau ada)

[Kalau ada navigasi yang bercabang berdasarkan kondisi, jelaskan di sini. Contoh: "Klik tombol Eskalasi → kalau status modul Alert WhatsApp aktif, langsung kirim notif; kalau tidak, tampilkan modal konfirmasi penerima dulu."]

- [Decision 1]: [Kondisi A → flow X; Kondisi B → flow Y]
- [Decision 2]: [...]

### 3.3 Navigasi Masuk dari Modul Lain (kalau ada)

[Kalau modul ini di-link dari modul lain, sebut di sini. Contoh: "Modul Manajemen Pengaduan punya tombol 'Lihat di Dashboard' yang masuk ke layar 2.1 Ringkasan modul ini dengan filter pre-set ke kategori aduan."]

- Dari [Modul X], [aksi Y] → masuk ke [layar di modul ini]
- [...]

---

## 4. Alur Bisnis

[Default format: ASCII flow diagram untuk UX flow penting. Numbered list boleh untuk alur linear sederhana. Minimal 3 alur, salah satunya WAJIB edge case.]

### 4.1 Alur [Nama Alur Utama / Happy Path]

```
┌──────────────┐     ┌────────────────┐     ┌──────────────────┐
│ [Aktor]      │────▶│ [Aksi konkret] │────▶│ [Hasil di sistem]│
└──────────────┘     └────────────────┘     └──────────────────┘
                                                     │
                                                     ▼
                                          ┌──────────────────────┐
                                          │ [Step berikutnya]    │
                                          └──────────────────────┘
                                                     │
                                                     ▼
                                          ┌──────────────────────┐
                                          │ [Outcome / hasil]    │
                                          └──────────────────────┘
```

**Penjelasan singkat:** [1-2 kalimat tentang flow ini.]

### 4.2 Alur [Nama Alur 2]

[Format sama atau numbered list kalau alur linear]

### 4.3 Alur Edge Case — [Nama Edge Case]

> Section ini WAJIB. Edge case yang umum: data tidak masuk dari sumber, user mistake (klik salah / batal), system failure (koneksi putus / sumber data down), patient/customer tidak hadir / dibatalkan.

```
[ASCII flow untuk edge case dengan branching, tunjukkan apa yang user lihat saat error]
```

**Penjelasan:** [Apa yang terjadi, bagaimana sistem respons, apa fallback untuk user.]

---

## 5. Data yang Dikelola Modul

> **CONDITIONAL** — section ini ada **kalau modul memang mengelola entity bisnis sendiri** (cth: pengaduan, antrean pasien, pengguna, transaksi). SKIP kalau modul agentic backend (cth: AI Assistant), pure passthrough integration (cth: Notifikasi Gateway), atau utility layer generic (cth: Auth).
>
> Format ringkas, readable, BUKAN SQL DDL. Cukup buat klien validasi "ya data ini memang ada di kami" dan sprint-builder bisa derive schema downstream.

### 5.1 Entity Bisnis Utama

**[Nama entity, cth: "Antrean Pasien"]**

| Field | Deskripsi | Contoh Nilai |
|-------|-----------|---------------|
| [Field 1] | [Penjelasan dalam bahasa bisnis] | [Contoh nilai realistis] |
| [Field 2] | [...] | [...] |
| [Field 3] | [...] | [...] |

**[Nama entity 2, kalau ada]**

| Field | Deskripsi | Contoh Nilai |
|-------|-----------|---------------|
| [...] | [...] | [...] |

### 5.2 Sample Data atau Dummy Data

> Tabel readable dengan minimal 3 baris contoh data realistis. Bukan SQL, bukan JSON. Format tabel markdown yang siap dibaca klien.

| [Kolom 1] | [Kolom 2] | [Kolom 3] | [Kolom 4] |
|-----------|-----------|-----------|-----------|
| [data realistis 1] | [...] | [...] | [...] |
| [data realistis 2] | [...] | [...] | [...] |
| [data realistis 3] | [...] | [...] | [...] |

### 5.3 Catatan untuk Tim Downstream

[Hal-hal yang perlu diperhatikan tim engineering / sprint-builder. Contoh: "Status pasien punya transisi state machine: menunggu → dipanggil → dilayani → selesai/batal. Tidak boleh skip state."]

---

## 6. Kebutuhan Data Eksternal

> **CONDITIONAL** — section ini ada **kalau modul butuh konsumsi data dari luar sistem klien**. SKIP kalau modul tidak butuh data luar (AI Assistant agentic, Auth, internal-only modules).
>
> Konteks: ada agent crawler downstream yang akan ambil data ini. Cukup state sumber + breakdown poin data yang perlu, bukan technical detail integrasi.

### 6.1 Sumber Data

| Sumber | Instansi | Jenis Data | Frekuensi Update yang Diharapkan |
|--------|----------|------------|----------------------------------|
| [Nama sumber, cth: "Data Sensus Penduduk"] | [Instansi, cth: "BPS"] | [Jenis data, cth: "Angka kelahiran per kabupaten"] | [Tahunan / Bulanan / Harian / Real-time] |
| [...] | [...] | [...] | [...] |

### 6.2 Breakdown Data yang Diperlukan

**Dari [Sumber 1, cth: BPS]:**
- [Poin data 1, cth: "Angka kelahiran per kabupaten 2020-2026"]
- [Poin data 2, cth: "Distribusi usia per kecamatan"]
- [Poin data 3, cth: "Jumlah penduduk per kelurahan"]

**Dari [Sumber 2, cth: BMKG]:**
- [Poin data 1]
- [Poin data 2]

**Dari [Sumber 3, cth: Data internal — sumber yang sudah ada di klien]:**
- [Poin data internal yang akan dipakai modul ini, cth: "Data aduan dari sistem LAPOR! klien"]
- [Catatan: kalau perlu dummy data untuk dev/POC, sebut: "Untuk POC, akan dipakai dummy data sesuai struktur Section 5."]

### 6.3 Catatan untuk Crawler Agent

[Hal-hal yang perlu diperhatikan crawler agent. Contoh: "BPS API rate-limit 100 req/menit, butuh API key terdaftar instansi.", atau "Data SIPD Kemendagri butuh credential SSO Kemendagri.", atau "LAPOR! tidak punya public API — perlu negosiasi MoU."]

- [Catatan 1]
- [Catatan 2]

---

## 7. Stack Agent Modul

> **CONDITIONAL** — section ini ada **kalau modul memang butuh agent stack untuk operasionalnya**. SKIP kalau modul utility murni (cth: modul Auth/RBAC pure CRUD) atau modul yang tidak punya agent sendiri.
>
> Section ini menjawab: "Modul ini butuh agent apa, dengan trigger apa, untuk fungsi apa, dengan dependency apa?" Pakai vocabulary 18 canonical agent dari `references/agent-catalog.md`. Untuk rules antar-agent dan kapan agent wajib/skip, baca `references/agent-rules.md`.

### 7.1 Daftar Agent

| Agent Type | Peran di Modul Ini | Trigger | Output |
|------------|---------------------|---------|--------|
| [Canonical agent name dari catalog] | [Peran spesifik di modul ini, 1 kalimat] | [Vocabulary trigger canonical: Scheduler / Event-driven / On-demand / dst — boleh kombinasi] | [Output umum yang dihasilkan untuk dikonsumsi agent atau output downstream] |
| [...] | [...] | [...] | [...] |
| [...] | [...] | [...] | [...] |

### 7.2 Alur Eksekusi Pipeline Agent (opsional, kalau pipeline kompleks)

> Section ini opsional. Tampilkan ASCII flow diagram **kalau pipeline agent kompleks** (3+ agent dengan dependency atau ada branching). Kalau pipeline sederhana 1-2 agent linear, cukup tabel di 7.1 saja.

```
[Trigger awal: data masuk / user action / scheduled]
  ↓
[Agent 1] (trigger spesifik)
  ↓ (event yang dihasilkan)
[Agent 2] (trigger spesifik)
  ↓ (event)
  ├─ Kondisi A → [Agent 3a] → [output A]
  └─ Kondisi B → [Agent 3b] → [output B]
```

**Penjelasan singkat:** [1-2 kalimat menjelaskan flow + branching kalau ada.]

### 7.3 Catatan Pattern Adaptive (kalau ada)

> Kalau modul punya pattern non-linear (mid-flow trigger reverse, agent yang trigger upstream agent, dst), state di sini.

- [Catatan pattern 1, cth: "Analysis Agent yang detect data gap boleh trigger Data Collection mid-flow untuk refresh data sumber X."]
- [Catatan pattern 2]

### 7.4 Agent Shared dengan Modul Lain (kalau ada)

> Kalau modul ini pakai agent yang juga dipakai modul lain, state di sini. Konsistensi dengan OVERVIEW Section "Konsolidasi Stack Agent" wajib.

- [Notification Agent — shared dengan Modul X dan Modul Y untuk eskalasi alert]
- [...]

---

## 8. Konfigurasi Alert

> **CONDITIONAL** — section ini ada **kalau modul punya alerting/threshold logic**. SKIP kalau modul tidak punya alert (cth: modul AI Assistant murni, modul Auth).

### 8.1 Threshold

| Kondisi | Threshold | Aksi |
|---------|-----------|------|
| [Kondisi normal, cth: "waktu tunggu < 20 menit"] | [Threshold dalam unit bisnis] | [Aksi yang diambil: tampilkan hijau / tidak ada notif] |
| [Kondisi peringatan] | [...] | [Aksi: tampilkan kuning / notif internal] |
| [Kondisi kritis] | [...] | [Aksi: tampilkan merah / kirim alert ke pihak terkait] |

### 8.2 Severity Levels

| Level | Warna | Tampilan di UI | Notifikasi |
|-------|-------|---------------|------------|
| [Hijau / Normal] | [Hijau] | [Deskriptif: "tampil normal di dashboard"] | [Tidak ada] |
| [Kuning / Perlu Perhatian] | [Kuning] | [Deskriptif: "ditandai dengan badge peringatan"] | [Notif internal di dashboard] |
| [Merah / Kritis] | [Merah] | [Deskriptif: "ditampilkan paling atas dashboard"] | [Memicu alert ke modul WhatsApp / email / SMS] |

---

## 9. Standar Layanan yang Diharapkan

> Reframe dari "Spesifikasi Teknis". Deskriptif, BUKAN angka p95/Lighthouse/latency ms. Tujuannya: klien validasi ekspektasi service level, sprint-builder paham target performance secara kualitatif.

### 9.1 Kecepatan Tampil Data

| Aspek | Standar Diharapkan |
|-------|---------------------|
| Tampil halaman pertama | [Cepat / Sedang / Toleran] |
| Pembaruan data | [Cepat / Sedang / Toleran] |
| Respons interaksi user | [Cepat / Sedang / Toleran] |

### 9.2 Frekuensi Pembaruan Data

| Jenis Data | Frekuensi |
|-----------|-----------|
| [Data 1, cth: "Ringkasan dashboard"] | [Real-time / Per menit / Per jam / Harian] |
| [Data 2, cth: "Detail per item"] | [...] |
| [Data 3] | [...] |

### 9.3 Ketersediaan Layanan

| Aspek | Standar Diharapkan |
|-------|---------------------|
| Jam operasional | [Jam kerja (08:00-17:00) / Diperpanjang (06:00-22:00) / 24-7] |
| Toleransi downtime | [Rendah / Sedang / Tinggi] |
| Konteks bisnis | [Penjelasan kenapa standar ini diperlukan, cth: "Layanan rawat jalan beroperasi 08:00-14:00 — di luar jam ini boleh maintenance."] |

---

## 10. Use Case Scenarios

> Minimal 2 skenario: 1 happy path + 1 edge case. Skenario ke-3 opsional.

### 10.1 Skenario [Nama Happy Path]

**Aktor**: [Jabatan]
**Goal**: [Outcome yang diinginkan aktor]

```
1. [Aktor] [aksi pembuka].
2. Sistem [respons konkret yang ditampilkan].
3. [Aktor] [aksi berikutnya].
4. Sistem [respons].
5. [Aktor] [aksi pamungkas].
6. [Outcome bisnis tercapai.]
```

### 10.2 Skenario Edge Case — [Nama Edge Case]

**Aktor**: [Jabatan]
**Goal**: [Apa yang aktor mau capai dalam kondisi tidak ideal]

```
1. [Aktor] [aksi pembuka dalam konteks edge case].
2. Sistem [respons fallback / error handling].
3. [Aktor] [reaksi terhadap fallback].
4. [Outcome / resolusi.]
```

### 10.3 Skenario [Tambahan — opsional]

[Format sama dengan 9.1]

---

## 11. Referensi Implementasi

### 11.1 [Nama Sistem Serupa 1]

**URL**: [URL kalau ada]

**Fitur yang Diadaptasi**:
- [Pola yang relevan diambil dari sistem ini]
- [Pola lain]

### 11.2 [Nama Sistem Serupa 2]

**URL**: [URL kalau ada]

**Fitur yang Diadaptasi**:
- [...]

### 11.3 [Nama Sistem Serupa 3 — opsional]

**URL**: [URL kalau ada]

**Fitur yang Diadaptasi**:
- [...]

---

*Dokumen ini merupakan bagian dari Dokumentasi Brief [Nama Klien / Sistem]*
*Modul: [Nama Modul] | Versi: 1.0.0*
