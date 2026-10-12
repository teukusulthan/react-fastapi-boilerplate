# Bridge Depth Guide — Cara Propose Detail Modul tanpa Technical Leakage

Fase 5 (Deep-Dive Loop) adalah fase paling banyak konten per modulnya. Tantangan utama: **propose dengan cukup detail untuk derive task downstream tanpa ambiguitas, tapi tetap readable untuk klien non-teknis** — tanpa SQL, tanpa library, tanpa endpoint YAML, tanpa wireframe ASCII.

**Aturan utama:** Anda yang propose draft lengkap, user koreksi yang salah. Brief adalah **jembatan bisnis-teknis**, bukan dokumen bisnis murni atau dokumen teknis murni.

File ini berisi pattern library yang Anda pakai sebagai modal untuk propose tiap section feature brief.

---

## 1. Cara propose Komponen Visual (Section 2 — Fitur Utama)

User non-teknis tidak bisa kasih wireframe. **Tapi Anda juga tidak boleh kasih wireframe ASCII layout** karena itu technical leakage. Yang Anda kasih: **tabel "Komponen Visual" deskriptif** yang menjelaskan apa saja yang ada di setiap menu/fitur.

### Modal yang Anda butuhkan
- Storyline yang sudah ter-validate (langkah-langkah konkret user)
- Decision authority + POV
- KPI utama yang mau ditampilkan
- Domain isu (apa yang dimonitor / dianalisis)

### Vocabulary yang dipakai (deskriptif, BUKAN technical library)

✅ **Pakai vocabulary ini:**
- Kartu ringkasan (untuk angka KPI besar)
- Grafik garis tren (untuk timeseries)
- Indikator status warna (untuk traffic light hijau/kuning/merah)
- Tabel daftar dengan filter (untuk tabular data dengan sort/filter)
- Peta lokasi interaktif (untuk visualisasi geospatial)
- Modal detail (untuk popup detail saat klik)
- Sidebar filter (untuk panel filter di samping)
- Panel notifikasi (untuk feed alert/notif)
- Daftar urutan prioritas (untuk top-N list)
- Diagram pohon hierarki (untuk tree structure)
- Linimasa kronologis (untuk timeline view)
- Galeri kartu (untuk grid view dengan card)

❌ **JANGAN pakai vocabulary ini (technical leakage):**
- Card component, Line chart, Gauge Chart, Big Number widget
- TanStack Table, Recharts, Apache ECharts
- Mapbox layer, Leaflet marker, Heatmap layer
- React modal, Dialog component
- Tailwind CSS class, Material UI badge
- WebSocket-driven feed, polling endpoint

### Pattern: dashboard eksekutif tinggi (kepala daerah, C-level)

Komponen yang biasanya ada:
- **Indikator komposit** (1 angka utama yang merangkum kondisi keseluruhan, cth: "Indeks Kondisi Daerah 78/100")
- **Indikator status warna** (traffic light untuk kondisi kritis, cth: "EWS Status: Hijau/Kuning/Merah")
- **3-5 kartu ringkasan** (angka kunci dengan trend arrow, cth: "Pengaduan Aktif: 1,247 ↓ 12%")
- **Grafik garis tren** (timeseries 1-2 metric utama)
- **Daftar prioritas top-5** (cth: "Top 5 Isu Viral")
- **Peta lokasi interaktif** (kalau ada dimensi geografis)

### Pattern: dashboard operator harian (Kabid, manajer menengah)

Komponen yang biasanya ada:
- **Sidebar filter / filter bar atas** (filter berdasarkan domain, periode, lokasi)
- **Tabel daftar utama** (data yang bisa di-sort, di-filter, di-klik per row)
- **Indikator status warna per row** (kondisi per item di tabel)
- **Panel detail samping atau modal** (drill-down saat klik row)
- **Action bar** (tombol: export, tag, eskalasi, catat)
- **Kartu ringkasan kecil di atas tabel** (jumlah total, status counter)

### Pattern: dashboard layanan publik (RSUD, kantor pelayanan)

Komponen yang biasanya ada:
- **Kartu ringkasan kondisi keseluruhan** (total antrean, jumlah unit overload)
- **Indikator status warna per unit** (hijau/kuning/merah per poli/loket)
- **Tabel antrean live** (daftar pasien aktif dengan durasi tunggu, status, prioritas)
- **Detail unit saat dipilih** (drill-down per poli/loket)
- **Grafik tren mini** (60 menit terakhir untuk monitoring real-time)

### Template proposal Komponen Visual

```markdown
**Deskripsi**: [1-2 kalimat tentang fungsi sub-fitur ini]

**Komponen Visual**:

| Komponen | Tipe | Data | Update |
|----------|------|------|--------|
| [Kartu ringkasan total X] | Kartu ringkasan | [Sumber data deskriptif] | [Real-time / Per menit / Per jam] |
| [Indikator status keseluruhan] | Indikator status warna | [Sumber data] | Real-time |
| [Daftar X terlama] | Tabel daftar dengan filter | [Sumber data] | [Frekuensi update] |

**Interaksi**:
- [Aksi user 1: filter berdasarkan X, Y, Z]
- [Aksi user 2: sort berdasarkan W tertinggi]
- [Aksi user 3: klik baris untuk membuka detail di modal/halaman lain]
- [Aksi user 4: toggle tampilan antara mode A dan mode B]
```

### Aturan
- Komponen yang ditampilkan harus terkait langsung ke storyline yang ter-validate
- Maksimal 6-8 elemen visual utama per layar — lebih dari itu cluttered
- **JANGAN** sertakan ASCII layout diagram. Tabel komponen visual cukup.
- **JANGAN** sebut framework atau library spesifik di kolom Tipe

---

## 2. Cara propose Navigasi & Interaksi (Section 3 — BARU)

Section ini menjawab pertanyaan: **"Klik X di mana, mengarah ke mana, bawa context apa?"** Tanpa ini, sprint-builder akan tanya balik atau improvise. Section ini **wajib ada** di setiap feature brief.

### Modal yang Anda butuhkan
- Daftar komponen visual dari Section 2
- List interaksi dari Section 2
- Daftar modul lain di sistem (untuk identifikasi cross-module navigation)

### Tiga jenis navigasi yang harus dipertimbangkan

**1. Navigasi internal modul** — antar layar / sub-fitur dalam modul yang sama
- Cth: dari Ringkasan → klik baris poli → buka Detail Poli
- Cth: dari Detail Poli → klik tombol Pasien → buka Modal Detail Pasien

**2. Navigasi keluar modul** — ke modul lain di sistem
- Cth: dari Detail Poli → klik tombol "Eskalasi" → masuk ke Modul Alert WhatsApp dengan context poli ID + status
- Cth: dari Daftar Aduan → klik link nama pelapor → masuk ke Modul Manajemen Pengguna dengan filter pelapor

**3. Navigasi masuk dari modul lain** — modul ini di-link dari mana
- Cth: Modul Dashboard Eksekutif punya tombol "Lihat Detail Pengaduan" → masuk ke Modul Manajemen Pengaduan
- Wajib disebut di Section 3.3 "Navigasi Masuk dari Modul Lain"

### Template proposal Peta Navigasi (Section 3.1)

```markdown
| Dari Layar / Komponen | User Klik / Aksi | Menuju Ke | Context yang Dibawa |
|----------------------|------------------|-----------|---------------------|
| Ringkasan Dashboard | Klik kartu poli "Poli Penyakit Dalam" | Detail Poli (Section 2.3 modul ini) | Filter poli ID = 1 |
| Daftar Antrean Live | Klik baris pasien "Siti Aisyah" | Modal Detail Pasien | Pasien ID + nomor antrean |
| Detail Poli | Klik tombol "Eskalasi" | Modul Alert WhatsApp | Poli ID + status warna + nama dokter jaga |
| Modal Detail Pasien | Klik tombol "Tutup" | Kembali ke Daftar Antrean Live | Filter sebelumnya dipertahankan |
```

### Decision Branch — kalau ada navigasi bercabang

```markdown
- **Klik tombol Eskalasi**:
  - Kalau status modul Alert WhatsApp aktif → langsung kirim notif ke nomor PIC poli
  - Kalau status modul Alert WhatsApp tidak aktif → tampilkan modal konfirmasi penerima
- **Klik baris pasien**:
  - Kalau status pasien "menunggu" → buka modal dengan opsi "Panggil"
  - Kalau status pasien "dilayani" → buka modal dengan opsi "Selesai" / "Batal"
```

### Aturan
- Setiap **tombol penting** wajib ada di Peta Navigasi — jangan tinggalkan generic "klik untuk detail"
- **Cross-module navigation** wajib detail bawa context apa (ID, filter, parameter)
- Konsistensi dengan modul lain: kalau Modul A bilang "klik X mengarah ke Modul B halaman Y", maka Modul B harus punya halaman Y yang konsisten
- **JANGAN** sebut route URL spesifik (cth: `/poli/{id}/detail`) — itu domain sprint-builder

---

## 3. Cara propose Alur Bisnis (Section 4)

Section 4 punya 2 fungsi: (1) workflow bisnis end-to-end, (2) mapping aktor → aksi → outcome. **Format default: ASCII flow diagram untuk UX flow penting.** Numbered list boleh untuk alur linear sederhana.

### Modal yang Anda butuhkan
- Storyline yang sudah ter-validate
- Komponen Visual + Navigasi yang sudah didefinisikan
- User type dari Section 1.2

### Aturan format

**Pakai ASCII flow diagram untuk:**
- Alur UX dengan branching (kondisi A → flow X, kondisi B → flow Y)
- Alur happy path utama yang menjadi tulang punggung modul
- Alur edge case dengan error handling

**Pakai numbered list untuk:**
- Alur linear sederhana tanpa decision branch
- Alur background system (sinkronisasi data, scheduled job)

### Pattern: ASCII flow diagram dengan branching

```
┌──────────────┐     ┌────────────────┐     ┌──────────────────┐
│ [Aktor]      │────▶│ [Aksi konkret] │────▶│ [Hasil di sistem]│
└──────────────┘     └────────────────┘     └──────────────────┘
                                                     │
                                                     ▼
                                          ┌──────────────────────┐
                                          │ [Decision Point?]    │
                                          └──────────────────────┘
                                              │            │
                                  Ya: lanjut  │            │  Tidak: alternatif
                                              ▼            ▼
                              ┌────────────────────┐  ┌──────────────────┐
                              │ [Flow utama]       │  │ [Flow alternatif]│
                              └────────────────────┘  └──────────────────┘
```

### Pattern: numbered list (linear)

```
1. [Aktor] [aksi pembuka].
2. Sistem [respons / hasil].
3. [Aktor] [aksi berikutnya].
4. Sistem [hasil akhir].
```

### Edge case wajib

Setiap feature brief WAJIB punya minimal 1 alur edge case di Section 4.3. Kandidat edge case yang umum:

- **Data tidak masuk** — sumber data eksternal down, integrasi gagal, klien belum input data
- **User mistake** — klik salah, batal di tengah proses, input invalid
- **System failure** — koneksi putus, server down, timeout
- **Pasien/customer tidak hadir** — antrean dipanggil tapi tidak ada
- **Konflik data** — duplicate, race condition, status tidak sinkron

### Counter gap yang sering terjadi

Brief yang lemah biasanya punya:
- ❌ Step generic seperti "follow-up ke unit", "koordinasi via WhatsApp" tanpa detail
- ❌ Linear flow tanpa branching
- ❌ User type yang di-claim di Section 1.2 tapi tidak ada flow coverage di Section 4

Counter ini saat propose:
- ✅ Detail step: "Petugas klik tombol Eskalasi di header detail poli → modal konfirmasi penerima muncul → petugas pilih PIC dari daftar → klik Kirim → notif WhatsApp terkirim ke PIC"
- ✅ Tambahkan minimal 1 decision branch di alur utama
- ✅ Pastikan setiap user type di Section 1.2 punya minimal 1 alur di Section 4

---

## 4. Cara propose Data yang Dikelola Modul (Section 5 — CONDITIONAL)

Section ini muncul **kalau modul mengelola entity bisnis sendiri**. SKIP kalau modul agentic backend, pure passthrough, atau utility generic.

**Format ringkas, readable, BUKAN SQL DDL.** Cukup buat klien validasi "ya data ini memang ada di kami" dan sprint-builder bisa derive schema downstream.

### Modal yang Anda butuhkan
- Domain isu modul
- Storyline yang sudah ter-validate
- Komponen Visual yang menampilkan data tertentu

### Format tabel readable

```markdown
**[Nama entity bisnis, cth: "Antrean Pasien"]**

| Field | Deskripsi | Contoh Nilai |
|-------|-----------|---------------|
| Nomor Antrean | Identitas unik antrean per poli per hari | A-014 |
| No Rekam Medis | Identitas pasien dari sistem RS | RM-12345 |
| Nama Pasien | Nama lengkap pasien | Siti Aisyah |
| Poli | Lokasi layanan tujuan | Poli Penyakit Dalam |
| Waktu Daftar | Jam pasien daftar di kios/pendaftaran | 11:58 |
| Status | Status pelayanan pasien | menunggu / dipanggil / dilayani / selesai / batal |
| Durasi Tunggu | Selisih waktu daftar dengan jam saat ini (auto-hitung) | 52 menit |
| Prioritas | Penanda layanan khusus | normal / prioritas |
```

### Sample data — wajib disertakan

Minimal 3 baris contoh data realistis:

```markdown
| Nomor Antrean | Nama Pasien | Poli | Durasi Tunggu | Status |
|---|---|---|---|---|
| A-014 | Siti Aisyah | Poli Penyakit Dalam | 52 menit | menunggu |
| A-015 | Ahmad Fauzi | Poli Penyakit Dalam | 47 menit | dipanggil |
| B-008 | Lina Marlina | Poli Anak | 42 menit | menunggu |
```

### Catatan untuk tim downstream

Kalau ada hal yang perlu diperhatikan tim engineering:

```markdown
**Catatan:**
- Status pasien punya transisi state machine: menunggu → dipanggil → dilayani → selesai/batal. Tidak boleh skip state.
- Durasi tunggu dihitung otomatis dari Waktu Daftar ke jam saat ini (live counter).
- Setiap perubahan status pasien tercatat untuk audit (timestamp + by user).
```

### Aturan
- ❌ **JANGAN tulis SQL CREATE TABLE** atau DDL apapun
- ❌ **JANGAN sebut tipe data teknis** seperti VARCHAR(50), BIGSERIAL, TIMESTAMP DEFAULT NOW()
- ✅ **Pakai bahasa bisnis** untuk deskripsi (bukan "INT NOT NULL", tapi "wajib diisi")
- ✅ **Sample data realistis** dengan nama, nilai, jam yang masuk akal
- ✅ **Highlight state machine** kalau ada (pengaduan, antrean, transaksi)

---

## 5. Cara propose Kebutuhan Data Eksternal (Section 6 — CONDITIONAL)

Section ini muncul **kalau modul butuh data dari luar sistem klien**. SKIP kalau modul tidak butuh data luar.

Konteks penting: **ada agent crawler downstream yang akan ambil data ini**. Cukup state sumber + breakdown poin data, bukan technical detail integrasi.

### Modal yang Anda butuhkan
- Domain isu modul
- Pengetahuan domain tentang sumber data per sektor

### Pattern: sumber data per domain

**Domain pemerintahan / kebijakan publik:**
- **BPS (Badan Pusat Statistik)** — data sensus, statistik ekonomi makro, indikator sosial, IPM, kemiskinan
- **Kemendagri** — data administratif daerah, SIPD (data pembangunan), DTKS (data terpadu kesejahteraan sosial)
- **Kemenkeu** — data fiskal, SIKD (data keuangan daerah), realisasi APBD
- **Bappenas** — data perencanaan, RPJMN, indikator SDGs
- **OPD lokal klien** — data internal pemerintah daerah klien
- **LAPOR! / SP4N** — data pengaduan masyarakat
- **BNPB** — data bencana, peringatan dini

**Domain kesehatan / RSUD / klinik:**
- **Kemenkes** — data fasyankes, indikator kesehatan, SIRS Online (Sistem Informasi Rumah Sakit)
- **BPJS Kesehatan** — data kepesertaan, klaim, rujukan
- **Dukcapil** — verifikasi NIK pasien
- **Sistem RS internal klien** — RM (rekam medis), antrean, billing existing

**Domain lingkungan / pertanian:**
- **BMKG** — data cuaca, curah hujan, prakiraan iklim
- **Kementerian LHK** — data hutan, kualitas udara, lingkungan
- **Kementerian Pertanian** — data komoditas, harga pasar, produksi
- **Bulog** — stok pangan strategis

**Domain ekonomi / perdagangan:**
- **Kemendag** — data harga komoditas, distribusi, ekspor-impor
- **Bank Indonesia** — data inflasi, kurs, sektor moneter
- **Kemenperin** — data industri, kawasan industri
- **OJK** — data sektor keuangan

**Domain sosial / media:**
- **Media monitoring** (Awantos, Talkwalker, Brand24) — data sentimen media sosial
- **Twitter/X API, Facebook Graph** — data media sosial real-time
- **Google Trends** — data popularitas pencarian

### Template proposal

```markdown
### 6.1 Sumber Data

| Sumber | Instansi | Jenis Data | Frekuensi |
|--------|----------|------------|-----------|
| Data Sensus Penduduk | BPS | Angka kelahiran per kabupaten | Tahunan |
| Data Cuaca Wilayah | BMKG | Curah hujan harian per kecamatan | Harian |
| Data Internal Aduan | LAPOR! Klien | Aduan masuk dari masyarakat | Real-time |

### 6.2 Breakdown Data yang Diperlukan

**Dari BPS:**
- Angka kelahiran per kabupaten 2020-2026
- Distribusi usia per kecamatan
- Jumlah penduduk per kelurahan

**Dari BMKG:**
- Curah hujan harian per kecamatan
- Prakiraan cuaca 7 hari ke depan

**Dari Data Internal (LAPOR! klien):**
- Aduan masuk dengan kategori, lokasi, status
- Untuk POC, akan dipakai dummy data sesuai struktur Section 5.

### 6.3 Catatan untuk Crawler Agent

- BPS API public via webapi.bps.go.id, butuh API key terdaftar instansi.
- BMKG public via openweather.bmkg.go.id, free tier 1000 req/hari.
- LAPOR! tidak punya public API — perlu negosiasi MoU atau setup integrasi langsung dengan tim IT KemenPAN-RB.
```

### Aturan
- ❌ **JANGAN sebut detail integrasi teknis** (rate limit spesifik, OAuth flow, JSON schema)
- ✅ **Pakai konteks tingkat tinggi** — "butuh API key terdaftar", "perlu MoU institusional", "free tier cukup untuk POC"
- ✅ **Sebut explicit** kalau modul butuh dummy data untuk POC (dengan referensi ke Section 5 modul ini)
- ✅ **Konsolidasi balik** ke OVERVIEW Section 4 (Konsolidasi Kebutuhan Data Eksternal)

---

## 6. Cara propose Konfigurasi Alert (Section 7 — CONDITIONAL)

Section ini muncul **kalau modul punya alerting / threshold logic**. SKIP kalau modul tidak punya alert.

### Modal yang Anda butuhkan
- Domain isu modul
- Threshold standar industri/sektor

### Threshold (business rule, bukan technical)

```markdown
| Kondisi | Threshold | Aksi |
|---------|-----------|------|
| Waktu tunggu pasien normal | < 20 menit | Tampilkan hijau di dashboard |
| Waktu tunggu mulai antri | 20-40 menit | Tampilkan kuning + badge peringatan |
| Waktu tunggu bermasalah | > 40 menit | Tampilkan merah + pin di atas + trigger alert WhatsApp |
```

### Severity levels (deskriptif, bukan technical)

```markdown
| Level | Warna | Tampilan di UI | Notifikasi |
|-------|-------|---------------|------------|
| Hijau / Normal | Hijau | Tampil normal di dashboard | Tidak ada |
| Kuning / Perlu Perhatian | Kuning | Ditandai dengan badge peringatan | Notif internal di dashboard |
| Merah / Kritis | Merah | Ditampilkan paling atas dashboard, dengan kartu khusus | Memicu alert ke modul WhatsApp / email PIC |
```

### Aturan
- ❌ **JANGAN tulis JSON config** dengan struktur `{ "level": "merah", "rule": "waiting_minutes >= 40" }`
- ❌ **JANGAN sebut implementation detail** seperti polling interval, webhook URL
- ✅ **Pakai tabel readable** dengan kolom Kondisi / Threshold / Aksi
- ✅ **Tampilan UI deskriptif** — bukan "z-index: 999, position: sticky", tapi "ditampilkan paling atas dashboard"

---

## 7. Cara propose Standar Layanan yang Diharapkan (Section 8)

Reframe dari "Spesifikasi Teknis" lama. **Deskriptif, BUKAN angka p95/Lighthouse/latency ms.**

Tujuan: klien validasi ekspektasi service level, sprint-builder paham target qualitative untuk derive performance budget.

### Pattern proposal

```markdown
### 8.1 Kecepatan Tampil Data

| Aspek | Standar Diharapkan |
|-------|---------------------|
| Tampil halaman pertama | Cepat |
| Pembaruan data ringkasan | Cepat |
| Respons interaksi (klik, filter, sort) | Cepat |

### 8.2 Frekuensi Pembaruan Data

| Jenis Data | Frekuensi |
|-----------|-----------|
| Ringkasan dashboard | Real-time |
| Daftar antrean live | Real-time |
| Tren 60 menit | Per menit |
| Statistik harian | Per jam |

### 8.3 Ketersediaan Layanan

| Aspek | Standar Diharapkan |
|-------|---------------------|
| Jam operasional | Jam kerja (08:00-17:00) |
| Toleransi downtime | Rendah |
| Konteks bisnis | Layanan rawat jalan beroperasi 08:00-14:00 — di luar jam ini boleh maintenance terjadwal |
```

### Vocabulary kecepatan (deskriptif)

| Tingkat | Implikasi qualitative |
|---------|----------------------|
| Cepat | User merasa instan / hampir tidak ada delay yang dirasakan |
| Sedang | User merasa ada loading tapi masih dalam toleransi |
| Toleran | User OK menunggu loading lebih lama (cth: report generation, batch process) |

### Vocabulary frekuensi (deskriptif)

| Tingkat | Implikasi |
|---------|-----------|
| Real-time | Data update otomatis tanpa user perlu refresh manual |
| Per menit | Data update setiap 1 menit (cth: monitoring antrean) |
| Per jam | Data update setiap jam (cth: aggregasi analitik) |
| Harian | Data update sekali sehari (cth: laporan harian) |
| Manual refresh | User klik refresh untuk update terbaru |

### Vocabulary ketersediaan (deskriptif)

| Tingkat | Implikasi |
|---------|-----------|
| Jam kerja | 08:00-17:00 weekday, weekend offline OK |
| Diperpanjang | 06:00-22:00 atau jam pelayanan klien |
| 24-7 | Selalu aktif, downtime minimal |

### Aturan
- ❌ **JANGAN sebut metric teknis** — Lighthouse score, p50/p95/p99 latency, TTFB, RUM
- ❌ **JANGAN sebut SLA dengan angka 99.9%** — cukup deskriptif "rendah/sedang/tinggi"
- ✅ **Pakai vocabulary deskriptif** dengan implikasi qualitative

---

## 8. Cara propose Use Case Scenarios (Section 9)

Use case adalah **storytelling concrete** yang nunjukkin user pakai modul. Wajib minimal 2 skenario: 1 happy path + 1 edge case.

### Pattern: happy path

```markdown
### 9.1 Skenario [Nama yang Konkret, cth: "Pemantauan Rutin Pagi Hari"]

**Aktor**: [Jabatan, cth: "Super Admin RS"]
**Goal**: [Outcome bisnis, cth: "Mengetahui kondisi antrean semua poli sebelum jam puncak"]

```
1. Super Admin membuka dashboard pada awal jam layanan (07:30).
2. Sistem menampilkan ringkasan semua poli dengan indikator status warna.
3. Super Admin scan kartu ringkasan, melihat 2 poli sudah kuning dan 1 poli merah.
4. Super Admin klik kartu poli merah untuk masuk ke detail.
5. Sistem menampilkan daftar pasien terlama menunggu di poli tersebut.
6. Super Admin klik tombol Eskalasi → modal konfirmasi muncul → pilih PIC.
7. Sistem mengirim notif WhatsApp ke PIC dengan context poli + status.
8. Super Admin lanjut ke poli kuning, mencatat di feature notes untuk dipantau lebih lanjut.
```
```

### Pattern: edge case

```markdown
### 9.2 Skenario Edge Case — [Nama, cth: "Sumber Data Antrean Tidak Sinkron"]

**Aktor**: [Jabatan, cth: "Petugas Monitoring"]
**Goal**: [Apa yang dia mau tetap capai dalam kondisi tidak ideal, cth: "Tetap bisa monitor antrean walau ada gangguan integrasi"]

```
1. Petugas membuka dashboard di shift siang.
2. Sistem menampilkan banner peringatan "Data terakhir tersinkron 15 menit lalu — sumber RS sedang gangguan".
3. Petugas tetap melihat data yang ada (snapshot terakhir) tapi tahu ini tidak fresh.
4. Petugas klik tombol "Coba Sinkron Ulang" → sistem retry koneksi.
5. Kalau berhasil → banner hilang, data refresh.
6. Kalau gagal → modal muncul dengan opsi:
   - Lanjut dengan data snapshot terakhir + notif tim IT
   - Stop monitoring sampai integrasi pulih
```
```

### Counter gap yang sering terjadi

Brief lemah biasanya punya:
- ❌ Step generic seperti "follow-up ke unit", "koordinasi via WhatsApp"
- ❌ User type yang di Section 1.2 tidak punya skenario di Section 9
- ❌ Tidak ada edge case sama sekali
- ❌ Outcome abstrak ("data-driven decision")

Counter:
- ✅ Detail step dengan UI affordance: tombol apa yang diklik, modal apa yang muncul, notif ke siapa
- ✅ Coverage minimum: 2 dari 3 user type di Section 1.2 punya skenario
- ✅ Wajib minimal 1 edge case
- ✅ Outcome konkret: tindakan yang muncul, decision yang diambil, output yang dihasilkan

---

## 9. Cara propose Referensi Implementasi (Section 10)

Section ini bukan teknis. Tujuannya: kasih klien dan tim downstream **inspirasi sistem serupa** yang sudah jalan, untuk benchmark fitur dan pola.

### Pattern: 2-3 referensi per modul

```markdown
### 10.1 [Nama Sistem Serupa]

**URL**: https://...

**Fitur yang Diadaptasi**:
- [Pola yang relevan diambil dari sistem ini]
- [Pola lain]
```

### Sumber referensi yang umum

**Sistem nasional (Indonesia):**
- Jakarta Smart City — pola dashboard real-time, citizen reporting
- SP4N-LAPOR! — multi-channel complaint handling
- SIPD Kemendagri — data pembangunan daerah
- SIRS Online — sistem informasi RS

**Sistem internasional:**
- Alberta Economic Dashboard (Kanada) — custom dashboard builder
- Decision Lens (US) — budget execution tracking
- UNDP Crisis Risk Dashboard — crisis monitoring

### Aturan
- 2-3 referensi cukup, tidak perlu lebih
- Sebut **fitur yang diadaptasi**, bukan tech stack mereka
- Kalau tidak yakin URL valid, web search sebelum tulis (Tool Usage Protocol Step 2 — web search boleh)

---

## 11. Cara propose Stack Agent Modul (Section 7 — CONDITIONAL)

Section ini muncul **kalau modul butuh agent stack untuk operasionalnya**. SKIP kalau modul utility murni tanpa agent (cth: Auth/RBAC pure CRUD).

**Prinsip kunci**: Adaptive, bukan template. Stack agent reasoning **dari kebutuhan modul**, bukan apply pipeline pre-defined. Pakai vocabulary 18 canonical agent dari `agent-catalog.md` dan rules dari `agent-rules.md`.

### Modal yang Anda butuhkan

- Konteks modul lengkap dari Section 1-6 (Gambaran Umum, Fitur Utama, Navigasi, Alur Bisnis, Data Dikelola, Kebutuhan Data Eksternal)
- Kondisi project: ada HUMINT lengkap atau tidak? Data internal sudah cukup atau perlu eksternal?

### Step reasoning untuk propose stack agent

**Step 1 — Identifikasi "apa yang dilakukan modul":**
Untuk setiap sub-fitur di Section 2, mapping ke agent canonical. Contoh:
- Modul "scrape data Twitter, IG, FB" → Data Collection Agent
- Modul "klasifikasi sentiment" → Analysis Agent
- Modul "kirim alert WhatsApp ke kepala OPD" → Notification Agent
- Modul "render dashboard real-time" → Reporting Agent
- Modul "Talk-to-Data interface" → Interactive Agent + Knowledge Retrieval Agent

**Step 2 — Apply rules basic (per-agent):**
Untuk setiap agent yang ter-identify, cek rules dasar:
- Data Collection → wajib pasangan Data Processing setelahnya (Rule DC-2). Kecuali eksplisit alasan.
- Analysis → wajib upstream data ter-validate (Rule AN-1). Kalau tidak, propose Data Processing dulu.
- Reporting → wajib data structured upstream (Rule RP-1). Bukan tempat analyze.
- Notification → wajib trigger event valid (Rule NT-1). Bukan stand-alone.

**Step 3 — Apply rules antar-agent:**
Cek dependency dan pasangan agent. Contoh:
- Kalau ada Data Collection → otomatis ada Data Processing (kecuali alasan eksplisit)
- Kalau ada 3+ agent dengan dependency → Orchestrator wajib (Rule OR-1)
- Kalau ada output ke decision-maker → Validation/Guardrail wajib (Rule VG-2)
- Kalau Talk-to-Data → Interactive + Knowledge Retrieval pasangan (Rule IA-1)

**Step 4 — Apply counter-rules untuk fleksibilitas:**
Cek edge case dari `agent-rules.md` Bagian 3:
- Project punya HUMINT lengkap → Data Collection bisa skip
- Data internal cukup → Data Collection skip
- Modul minimal 1-2 agent → Orchestrator overkill
- Mid-flow trigger reverse — pattern adaptive valid (cth: Analysis trigger Data Collection refresh)

**Step 5 — Tabel + reasoning + (opsional) flow diagram:**
Format final di brief.

### Vocabulary trigger canonical (jangan invent)

✅ **Pakai vocabulary ini:**
- `Scheduler / event` (untuk Data Collection)
- `Event (post-collection)` / `Event-driven`
- `Event / batch` (untuk Analysis)
- `Manual / event` / `Manual / scheduled` (untuk Planning, Reporting)
- `User-triggered` (untuk Interactive)
- `System-level` (untuk Orchestrator)
- `Continuous` (untuk Memory, Monitoring)
- `On-demand` (untuk Knowledge Retrieval, Simulation, Tool Integration)
- `Post-process` / `Pre/Post process` (untuk Validation, Security)
- `Offline / periodic` (untuk Learning)

✅ **Boleh kombinasi natural**: `Scheduler + on-demand`, `Event / batch`, dst

❌ **Jangan invent label baru**: "Auto-triggered", "Auto-batch", "Reactive", "Proactive" — pakai canonical saja.

### Template proposal stack agent (modul minimal)

Untuk modul yang butuh 2-3 agent linear sederhana (cth: modul Reporting agregator):

```markdown
## 7. Stack Agent Modul

### 7.1 Daftar Agent

| Agent Type | Peran di Modul Ini | Trigger | Output |
|------------|---------------------|---------|--------|
| Orchestrator Agent | Koordinasi tarik data dari modul lain untuk render dashboard | System-level | Routing decision ke agent atau sumber data |
| Reporting Agent | Render dashboard agregat dari data modul lain | Manual / scheduled | Dashboard rendering yang up-to-date |

### 7.2 Catatan untuk Tim Downstream

- Modul ini bersifat agregator — tidak punya agent yang ingest data sendiri
- Orchestrator query ke modul lain via internal integration, bukan external data source
```

### Template proposal stack agent (modul kompleks)

Untuk modul agent-heavy (cth: modul Persepsi Publik dengan multi-agent pipeline):

```markdown
## 7. Stack Agent Modul

### 7.1 Daftar Agent

| Agent Type | Peran di Modul Ini | Trigger | Output |
|------------|---------------------|---------|--------|
| Data Collection Agent | Scrape data Twitter/X, Instagram, Facebook, TikTok, news, forum | Scheduler (per platform punya cadence beda) + on-demand | Raw posts dengan metadata author, engagement, timestamp |
| Data Processing Agent | Clean text, normalize slang, dedupe lintas-platform, convert emoji | Event (post-collection) | Clean structured posts siap analisis |
| Analysis Agent (sentiment) | Klasifikasi sentiment per post + emotion detection | Event | Sentiment label + score + emotion per post |
| Analysis Agent (topic) | Topic clustering dan entity extraction | Event (sequential setelah sentiment) | Topic cluster + entity list per post |
| Analysis Agent (viral) | Viral score calculation aggregate lintas-post | Batch (per 15 menit) | Viral score per topik dengan trend metric |
| Validation/Guardrail Agent | Validate output sentiment + viral score sebelum jadi recommendation | Post-process | Verified output atau flag untuk manual review |
| Planning Agent | Generate strategi komunikasi berbasis insight + viral analysis | Event-driven (saat viral score breach threshold) | Action plan dengan priority, channel, key messages |
| Task Automation Agent | Trigger alert ketika sentiment drop, viral, atau crisis potential terdeteksi | Event-driven | Action result, downstream trigger ke Notification |
| Notification Agent | Kirim alert ke humas, sekda, kepala daerah via WhatsApp/email | Event-driven (dipanggil Task Automation) | Notification log dengan delivery status |
| Orchestrator Agent | Coordinate multi-agent saat crisis flow (severity HIGH branching) | System-level | Routing decision untuk parallel execution agent |

### 7.2 Alur Eksekusi Pipeline Agent

```
[Scheduler trigger atau humas request refresh]
  ↓
Data Collection Agent (per platform paralel)
  ↓ (post-collection event)
Data Processing Agent (normalize + dedupe)
  ↓ (clean data event)
Analysis Agent — sentiment + emotion (per post)
  ↓
Analysis Agent — topic clustering + entity (per post)
  ↓ (batch trigger per 15 menit)
Analysis Agent — viral score aggregate
  ↓ (insight ready event)
Validation/Guardrail Agent (post-process)
  ↓
  ├─ Severity LOW → Reporting Agent (update dashboard) → END
  ├─ Severity MEDIUM → Planning Agent → Notification (humas only)
  └─ Severity HIGH → Orchestrator Agent
                       ├─ Planning Agent (generate crisis strategy)
                       ├─ Validation (extra check untuk eksekutif)
                       └─ Notification (multi-channel: WhatsApp + email + SMS)
```

### 7.3 Catatan Pattern Adaptive

- Analysis Agent yang detect topik baru muncul (out of monitoring keyword) boleh trigger Data Collection mid-flow untuk fokus scrape topik tersebut
- Humas yang punya HUMINT (info isu yang belum ke-detect sistem) bisa trigger Interactive Agent → langsung trigger Data Collection + Analysis untuk topik spesifik

### 7.4 Agent Shared dengan Modul Lain

- **Notification Agent** — shared dengan Modul `02_MANAJEMEN_PENGADUAN` dan `08_EARLY_WARNING_RISIKO` untuk eskalasi alert
- **Validation/Guardrail Agent** — shared dengan modul lain yang produce output ke decision-maker
```

### Aturan
- ❌ **JANGAN invent agent name** — pakai 18 canonical dari `agent-catalog.md` saja
- ❌ **JANGAN invent trigger label** — pakai vocabulary canonical
- ❌ **JANGAN apply pipeline template** — reasoning dari konteks modul, bukan dari pattern pre-defined
- ❌ **JANGAN sebut framework implementation** (LangChain, CrewAI, dst) — itu domain sprint-builder/engineering
- ✅ **Pakai reasoning adaptive** — agent bisa muncul di mana saja di flow, branching valid, mid-flow reverse trigger valid
- ✅ **Konsistensi cross-section** — agent shared muncul di OVERVIEW dan tiap feature brief yang pakai
- ✅ **Apply rules dari `agent-rules.md`** — tapi bisa override dengan alasan eksplisit (counter-rules)

---

## 12. Closing — checklist sebelum submit draft fitur ke user

Sebelum submit draft fitur ke user di Fase 5 untuk koreksi, jalankan internal check ini:

- [ ] Section 1 (Gambaran Umum) — Tujuan + Target Pengguna terisi
- [ ] Section 2 (Fitur Utama) — minimal 2 sub-fitur, masing-masing punya tabel Komponen Visual + Interaksi list
- [ ] Section 2 — **TIDAK ADA wireframe ASCII layout dashboard**
- [ ] Section 3 (Navigasi & Interaksi) — Peta Navigasi terisi minimal 3 baris
- [ ] Section 4 (Alur Bisnis) — minimal 3 alur, salah satunya edge case (4.3)
- [ ] Section 4 — UX flow penting pakai ASCII diagram
- [ ] Section 5 (Data yang Dikelola) — terisi kalau modul mengelola entity bisnis, SKIP kalau tidak
- [ ] Section 5 — **TIDAK ADA SQL DDL** kalau ada
- [ ] Section 6 (Kebutuhan Data Eksternal) — terisi kalau modul butuh data luar, SKIP kalau tidak
- [ ] Section 7 (Stack Agent Modul) — terisi kalau modul butuh agent stack, SKIP kalau tidak
- [ ] Section 7 — vocabulary 18 canonical agent dari `agent-catalog.md`
- [ ] Section 7 — vocabulary trigger canonical (Scheduler / Event-driven / On-demand / dst)
- [ ] Section 7 — rules dari `agent-rules.md` di-apply (Data Collection + Data Processing pasangan, Analysis butuh upstream data, dst)
- [ ] Section 7 — **TIDAK ADA framework implementation** (LangChain, CrewAI, dst)
- [ ] Section 8 (Konfigurasi Alert) — terisi kalau modul punya alert, SKIP kalau tidak
- [ ] Section 8 — **TIDAK ADA JSON config** kalau ada
- [ ] Section 9 (Standar Layanan) — Kecepatan + Frekuensi + Ketersediaan terisi deskriptif
- [ ] Section 9 — **TIDAK ADA angka p95 / Lighthouse / latency ms**
- [ ] Section 10 (Use Case) — minimal 1 happy path + 1 edge case
- [ ] Section 10 — coverage user type minimal 2 dari 3 yang di Section 1.2
- [ ] Section 11 (Referensi Implementasi) — 2-3 sistem serupa
- [ ] Vocabulary scan — tidak ada: SQL, library version, REST endpoint, framework name, Lighthouse, p95, JSON config, ASCII wireframe layout, agent framework name (LangChain dst)
- [ ] Konsistensi — agent shared lintas modul muncul konsisten di OVERVIEW Section "Konsolidasi Stack Agent"

Kalau semua check pass, submit draft fitur ke user dengan pertanyaan tertutup: "Brief fitur ini OK, atau ada section yang perlu dikoreksi?"
