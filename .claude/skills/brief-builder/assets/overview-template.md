# [Nama Sistem] — Dokumentasi Implementasi

> Template OVERVIEW — jembatan bisnis-teknis. Tidak ada tech stack spesifik (React, PostgreSQL, dst), tidak ada OpenAPI YAML, tidak ada library list. Komponen sistem dijelaskan deskriptif dari sisi peran/fungsi, bukan teknologi.

## Ringkasan Eksekutif

[1-2 paragraf — apa sistem ini, untuk siapa, value proposisi utama. Bahasa bisnis untuk klien & internal user.]

---

## 1. Visi dan Tujuan Sistem

### 1.1 Visi

[1-2 kalimat tentang vision sistem — outcome jangka panjang yang ingin dicapai.]

### 1.2 Tujuan Utama

| Tujuan | Deskripsi |
|--------|-----------|
| [Tujuan 1] | [Penjelasan dari perspektif value bisnis] |
| [Tujuan 2] | [...] |
| [Tujuan 3] | [...] |
| [Tujuan 4] | [...] |
| [Tujuan 5] | [...] |
| [Tujuan 6 — opsional] | [...] |

---

## 2. Komponen Sistem Level Tinggi

> Deskripsi peran/fungsi setiap komponen, BUKAN teknologi spesifik. Tech stack ditentukan oleh sprint-builder atau tim engineering downstream.

### 2.1 Layer Sistem

```
┌─────────────────────────────────────────────────────────────────┐
│                     LAYER ANTARMUKA PENGGUNA                    │
│  [Aplikasi web admin] [Aplikasi mobile] [Portal publik]         │
├─────────────────────────────────────────────────────────────────┤
│                     LAYER LOGIKA APLIKASI                       │
│  [Engine Modul 1] [Engine Modul 2] [Engine Modul 3] ...         │
├─────────────────────────────────────────────────────────────────┤
│                     LAYER KECERDASAN BUATAN (kalau ada)         │
│  [Klasifikasi teks] [Analisis sentimen] [Prediksi] ...          │
├─────────────────────────────────────────────────────────────────┤
│                     LAYER DATA                                  │
│  [Data lake / warehouse internal] [Data eksternal yang ditarik] │
├─────────────────────────────────────────────────────────────────┤
│                     LAYER INTEGRASI                             │
│  [Integrasi sumber X] [Integrasi sumber Y] [Integrasi sumber Z] │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Peran Komponen Utama

| Komponen | Peran |
|----------|-------|
| [Antarmuka Pengguna] | [Apa yang user lihat dan lakukan, bahasa deskriptif] |
| [Layer Logika Aplikasi] | [Memproses logika bisnis tiap modul, mengorkestrasi alur] |
| [Layer Kecerdasan Buatan] | [Kalau ada — fungsi AI yang dipakai, cth: klasifikasi otomatis aduan, deteksi anomali] |
| [Layer Data] | [Menyimpan dan mengelola data yang masuk dan diproses] |
| [Layer Integrasi] | [Menghubungkan ke sumber data eksternal dan sistem lain] |

> **CATATAN PENTING**: Brief ini sengaja tidak menyebut teknologi spesifik (framework frontend, database engine, dst). Penentuan teknologi adalah tugas sprint-builder atau tim engineering — bukan brief.

---

## 3. Modul Sistem

### 3.1 Daftar Modul

| No | Modul | Kode | Prioritas |
|----|-------|------|-----------|
| 1 | [Nama Modul 1] | `[KODE_MODUL_1]` | [Tinggi / Sedang / Rendah] |
| 2 | [Nama Modul 2] | `[KODE_MODUL_2]` | [...] |
| 3 | [...] | [...] | [...] |
| ... | ... | ... | ... |

### 3.2 Integrasi Antar Modul

```
                    ┌────────────────────┐
                    │  [MODUL HUB]       │
                    │  (Pusat Integrasi) │
                    └─────────┬──────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ [MODUL 2]     │   │ [MODUL 3]     │   │ [MODUL 4]     │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                   │                   │
        └───────────┬───────┴───────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ [MODUL DOWNSTREAM]    │
        └───────────────────────┘
```

[Penjelasan singkat alur integrasi — modul mana feed data ke modul mana, modul mana sebagai pusat orkestrasi.]

---

## 4. Konsolidasi Kebutuhan Data Eksternal

> Section ini wajib ada **kalau ada modul yang butuh data eksternal**. SKIP kalau semua modul cuma pakai data internal klien.
>
> Ini matriks tingkat sistem yang konsolidasi semua kebutuhan data eksternal dari semua modul. Memberikan bird-eye view ke klien dan tim downstream tentang dependency data luar.

### 4.1 Matriks Modul × Sumber Data Eksternal

| Modul | Sumber Data | Instansi | Jenis Data | Frekuensi |
|-------|-------------|----------|------------|-----------|
| [Modul 1, cth: "01_DEMOGRAFI_PENDUDUK"] | [Sumber, cth: "Data Sensus"] | [Instansi, cth: "BPS"] | [Jenis data, cth: "Angka kelahiran per kabupaten"] | [Tahunan / Bulanan / Harian / Real-time] |
| [Modul 1] | [Sumber 2] | [Instansi 2] | [...] | [...] |
| [Modul 2] | [Sumber] | [Instansi] | [...] | [...] |
| [...] | [...] | [...] | [...] | [...] |

### 4.2 Sumber Data Eksternal Unik

> Daftar sumber data eksternal yang dipakai sistem secara unique, untuk memudahkan tim downstream (terutama crawler agent) plan koneksi.

**[Sumber 1, cth: BPS — Badan Pusat Statistik]**
- Dipakai modul: [Modul X, Modul Y]
- Akses: [Public API / Butuh API key terdaftar / Butuh MoU institusional]
- Catatan: [Hal-hal yang perlu diperhatikan tim integrasi]

**[Sumber 2, cth: BMKG — Badan Meteorologi Klimatologi dan Geofisika]**
- Dipakai modul: [Modul X]
- Akses: [...]
- Catatan: [...]

**[Sumber N — Data Internal Klien]**
- Dipakai modul: [Modul X, Modul Y]
- Akses: [Direct database / API internal yang sudah ada / Perlu setup baru]
- Catatan: [Cth: "Perlu integrasi dengan sistem LAPOR! existing klien — koordinasi dengan tim IT klien.", "Untuk POC, akan dipakai dummy data dengan struktur sesuai brief modul."]

---

## 5. Konsolidasi Stack Agent

> Section ini wajib ada **kalau ada modul yang punya agent stack**. SKIP kalau semua modul utility murni tanpa agent.
>
> Ini matriks tingkat sistem yang konsolidasi semua agent yang dipakai sistem keseluruhan. Memberikan bird-eye view tentang ekosistem agent yang dibutuhkan, plus identifikasi agent shared lintas modul.
>
> Pakai vocabulary 18 canonical agent dari `references/agent-catalog.md`. Untuk rules antar-agent, baca `references/agent-rules.md`.

### 5.1 Matriks Modul × Agent

| Modul | Agent yang Dipakai | Trigger Utama | Output ke |
|-------|-------------------|---------------|-----------|
| [Modul 1, cth: "01_DASHBOARD_SITUASIONAL"] | [Agent canonical, cth: "Reporting Agent, Orchestrator Agent"] | [Trigger: Manual / scheduled / System-level] | [Output ke: dashboard rendering, agregasi modul lain] |
| [Modul 2] | [...] | [...] | [...] |
| [Modul 3] | [...] | [...] | [...] |
| [...] | [...] | [...] | [...] |

### 5.2 Agent Shared Lintas Modul

> Daftar agent yang dipakai oleh lebih dari 1 modul. Konsistensi dengan tiap feature brief wajib.

**[Agent canonical, cth: Notification Agent]**
- Dipakai modul: [Modul X, Modul Y, Modul Z]
- Peran: [Peran umum agent ini di sistem]
- Catatan koordinasi: [Hal yang perlu disinkronkan antar modul kalau pakai agent ini]

**[Agent canonical 2]**
- Dipakai modul: [...]
- Peran: [...]
- Catatan: [...]

### 5.3 Agent Lintas-Sistem (Shared Infrastructure)

> Agent yang berperan sebagai shared infrastructure untuk seluruh sistem, bukan per-modul. Default-nya: Monitoring, Security/Compliance, Learning/Improvement, Memory (kalau ada AI Assistant lintas modul), Tool Integration. Skip kalau project tidak butuh.

**[Monitoring Agent]**
- Peran: [Observability lintas semua agent di sistem]
- Catatan: [Track failure rate, latency, throughput tiap agent]

**[Security / Compliance Agent]**
- Peran: [Kontrol akses dan compliance untuk data sensitif]
- Catatan: [Modul yang butuh tier ekstra]

**[Learning / Improvement Agent]**
- Peran: [Continuous improvement untuk agent yang pakai LLM]
- Catatan: [Periodic eval dan auto-tune]

### 5.4 Catatan Koordinasi untuk Tim Downstream

[Hal-hal yang perlu diperhatikan tim engineering / sprint-builder saat implementasi agent ecosystem. Contoh:]

- Konsistensi event schema antar agent — semua agent pakai event format yang sama untuk pipeline koordinasi
- Konfigurasi trigger threshold di-config terpusat, bukan hardcoded per agent
- Crisis response coordinator (Orchestrator Agent) wajib uji integrasi sebelum go-live
- Agent shared (Notification, Validation) di-implement sebagai shared service, bukan duplicate per modul

---

## 6. Standar Layanan

> Deskriptif, BUKAN angka p95/Lighthouse/latency ms. Tujuannya: klien validasi ekspektasi service level, sprint-builder paham target qualitative.

### 6.1 Standar Pengalaman Pengguna

| Aspek | Standar Diharapkan |
|-------|---------------------|
| Kecepatan tampil halaman | [Cepat / Sedang / Toleran] |
| Pembaruan data | [Real-time / Per menit / Per jam / Harian] |
| Respons interaksi | [Cepat / Sedang / Toleran] |

### 6.2 Standar Keamanan dan Akses

| Aspek | Standar Diharapkan |
|-------|---------------------|
| Pengamanan data | [Standar industri — enkripsi data sensitif] |
| Otentikasi user | [Login dengan akun internal / SSO instansi / OTP] |
| Pengaturan akses | [Berbasis peran/jabatan dengan tingkat akses berbeda per modul] |
| Audit log | [Aktivitas user tercatat untuk akuntabilitas] |
| Backup data | [Backup berkala dengan retensi minimal X bulan] |

### 6.3 Standar Ketersediaan

| Aspek | Standar Diharapkan |
|-------|---------------------|
| Jam operasional | [Jam kerja / 24-7 / Sesuai jam layanan klien] |
| Toleransi downtime | [Rendah / Sedang / Tinggi] |
| Konteks bisnis | [Cth: "Layanan untuk operasional harian Pemkot — downtime saat jam kerja sangat tidak diinginkan"] |

---

## 7. Roadmap Implementasi

### Fase 1: Fondasi (Bulan 1-3)

- [Aktivitas fase 1]
- [Aktivitas fase 1]
- [Aktivitas fase 1]

### Fase 2: Core Features (Bulan 4-6)

- [Aktivitas fase 2]
- [...]

### Fase 3: Advanced Features (Bulan 7-9)

- [...]

### Fase 4: Optimisasi & Go-Live (Bulan 10-12)

- [...]

---

## 8. Struktur Dokumen

Dokumentasi ini terdiri dari [N] file Markdown yang saling terhubung:

| File | Deskripsi |
|------|-----------|
| `00_OVERVIEW.md` | Dokumen ini — gambaran umum sistem |
| `01_[NAMA_MODUL_1].md` | [Deskripsi singkat modul 1] |
| `02_[NAMA_MODUL_2].md` | [...] |
| `03_[NAMA_MODUL_3].md` | [...] |
| ... | ... |
| `NN_[NAMA_MODUL_N].md` | [...] |

---

## 9. Blind Spot Review

### 9.1 Gap Teridentifikasi

[List gap yang teridentifikasi selama discovery — parameter Tier 1 yang masih kosong / dangkal / hanya diisi asumsi agent.]

- [Gap 1]
- [Gap 2]
- [Gap 3]

### 9.2 Asumsi Belum Tervalidasi

[List asumsi yang diambil agent yang user belum confirm secara eksplisit.]

| Asumsi | Dampak Kalau Salah |
|--------|---------------------|
| [Asumsi 1] | [Dampak ke desain sistem] |
| [Asumsi 2] | [...] |

### 9.3 Risiko yang Ditandai

[Risiko strategis yang perlu diangkat ke klien / tim eksekutif.]

- [Risiko 1]
- [Risiko 2]

### 9.4 Tingkat Kepercayaan Agent

**Confidence Level**: [high | medium-high | medium | low]

[1-2 kalimat penjelasan kenapa confidence di level itu.]

### 9.5 Status Brief

**Status**: [`ready_for_execution` | `incomplete_pending_clarification`]

[Kalau incomplete, list kekurangan yang perlu di-clarify dulu.]

---

## 10. Kontak dan Dukungan

| Tim | Email | Tanggung Jawab |
|-----|-------|----------------|
| [Tim 1] | [email] | [Tanggung jawab] |
| [Tim 2] | [email] | [...] |
| [Tim 3] | [email] | [...] |

---

*Dokumen ini merupakan bagian dari Dokumentasi Implementasi [Nama Sistem]*
*Versi: 1.0.0 | Terakhir diperbarui: [Tanggal]*
