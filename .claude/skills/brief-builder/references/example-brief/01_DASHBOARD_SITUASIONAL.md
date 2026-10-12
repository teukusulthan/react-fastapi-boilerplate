# Modul Dashboard Situasional

## 1. Gambaran Umum

Dashboard Situasional adalah **hub sentral** dari Sistem Intelijen Regional yang menyajikan gambaran kondisi daerah secara real-time dalam satu layar terintegrasi. Modul ini mengagregasi data dari seluruh modul lain dan menyajikannya dalam visualisasi yang mudah dipahami oleh pengambil keputusan, dari kepala daerah sampai kepala OPD.

Di dalam v1, dashboard ini menjadi command center harian. Pengguna tidak perlu membuka banyak menu untuk memahami kondisi daerah: cukup melihat ringkasan kondisi seluruh wilayah, menelusuri area atau isu yang perlu perhatian, lalu masuk ke detail untuk pengambilan keputusan.

### 1.1 Tujuan Modul

| Tujuan | Deskripsi |
|--------|-----------|
| Single Source of Truth | Menyediakan satu sumber data terpercaya untuk kondisi daerah, mengurangi konflik data antar OPD |
| Real-time Monitoring | Pemantauan kondisi aktual tanpa keterlambatan, terutama untuk indikator kritis |
| Early Detection | Identifikasi isu dan risiko sebelum eskalasi, melalui status warna dan alert |
| Decision Support | Informasi cepat dan kontekstual untuk pengambilan keputusan strategis |

### 1.2 Target Pengguna

| Pengguna | Kebutuhan |
|----------|-----------|
| Kepala Daerah | Overview eksekutif untuk pengambilan keputusan strategis dan briefing media |
| Sekda | Koordinasi lintas OPD, monitoring kinerja, persiapan rapat koordinasi |
| Kepala OPD | Monitoring kondisi di domain OPD masing-masing, akses cepat ke modul detail |
| Tim Asisten / Staf Perencana | Analisis detail dan rekomendasi kebijakan untuk eksekutif |

---

## 2. Fitur Utama

### 2.1 Ringkasan Kondisi Daerah (Executive View)

**Deskripsi**: Tampilan ringkas untuk eksekutif tinggi (kepala daerah, sekda) dengan indikator kunci yang mencerminkan kondisi keseluruhan daerah dalam satu layar.

**Komponen Visual**:

| Komponen | Tipe | Data | Update |
|----------|------|------|--------|
| Indeks Kondisi Daerah | Kartu ringkasan dengan angka utama | Skor komposit 0-100 dari agregasi semua modul | Real-time |
| Status Early Warning | Indikator status warna | Hijau/Kuning/Merah dari Modul Early Warning | Real-time |
| Jumlah Pengaduan Aktif | Kartu ringkasan dengan trend arrow | Jumlah aduan + arah perubahan dari minggu lalu | Real-time |
| Sentimen Publik | Grafik garis tren | Persentase positif/negatif media sosial 7 hari | Per jam |
| Realisasi APBD | Indikator progres | Persentase realisasi vs target tahunan | Harian |
| Pertumbuhan Ekonomi | Mini-trend | PDRB triwulan terakhir | Per triwulan |
| Top 5 Isu Viral | Daftar urutan prioritas | 5 isu tertinggi dari Modul Persepsi Publik | Per jam |
| Top 5 Aduan Domain | Daftar urutan prioritas | 5 domain aduan terbanyak hari ini | Real-time |

**Interaksi**:

- Klik kartu Indeks Kondisi Daerah untuk membuka penjelasan komposisi indeks (modul mana saja yang berkontribusi).
- Klik kartu Pengaduan Aktif untuk masuk ke Modul Manajemen Pengaduan dengan filter "active".
- Klik salah satu Top 5 Isu Viral untuk masuk ke detail isu di Modul Persepsi Publik.
- Klik kartu Realisasi APBD untuk masuk ke Modul Program & Kontrol Fiskal.
- Toggle tampilan antara mode "ringkas eksekutif" dan "detail lengkap dengan semua modul".

### 2.2 Peta Interaktif Kondisi Daerah

**Deskripsi**: Visualisasi geospasial kondisi daerah berdasarkan lokasi — menunjukkan distribusi aduan, zona risiko, lokasi proyek, dan fasilitas publik di peta wilayah.

**Komponen Visual**:

| Komponen | Tipe | Data | Update |
|----------|------|------|--------|
| Peta wilayah dasar | Peta lokasi interaktif | Polygon kabupaten/kecamatan/kelurahan | Statis |
| Layer aduan per area | Overlay intensitas | Jumlah aduan per kecamatan dari Modul Pengaduan | Real-time |
| Layer zona risiko | Overlay status warna | Hijau/Kuning/Merah per wilayah dari EWS | Real-time |
| Layer titik infrastruktur | Penanda lokasi | Jalan, jembatan, drainase dari SIPD | Per minggu |
| Layer lokasi proyek | Penanda dengan status | Status realisasi proyek dari SIPD | Harian |
| Layer fasilitas publik | Penanda kategori | Puskesmas, sekolah, kantor pelayanan | Statis |
| Pengatur layer | Sidebar filter | Toggle on/off per layer | Real-time |

**Interaksi**:

- Filter berdasarkan jenis layer (aduan / risiko / infrastruktur / proyek / fasilitas) — tampilkan yang relevan saja.
- Zoom in/out untuk lihat dari level provinsi sampai kelurahan.
- Klik area di peta untuk melihat ringkasan kondisi area tersebut di panel detail samping.
- Klik penanda lokasi (proyek, fasilitas) untuk membuka modal detail item tersebut.
- Filter berdasarkan periode (hari ini, minggu ini, bulan ini, kustom).

### 2.3 Panel Trend & Analitik

**Deskripsi**: Bagian bawah dashboard untuk menampilkan tren historis dan perbandingan periode — mendukung analisis pola dan evaluasi kebijakan.

**Komponen Visual**:

| Komponen | Tipe | Data | Update |
|----------|------|------|--------|
| Tren 30 hari indikator utama | Grafik garis tren | Indeks kondisi 30 hari terakhir | Harian |
| Perbandingan periode | Grafik batang side-by-side | Periode ini vs periode lalu | Harian |
| Distribusi aduan per kategori | Diagram donat | Top 8 kategori aduan + Lainnya | Per jam |
| Rangking kinerja OPD | Tabel daftar dengan filter | Skor kinerja per OPD | Bulanan |

**Interaksi**:

- Pilih rentang waktu (7/30/90/365 hari atau kustom).
- Klik kategori di diagram donat untuk filter aduan kategori tersebut.
- Klik OPD di tabel rangking untuk masuk ke Modul Kualitas Pelayanan dengan filter OPD tersebut.
- Export tampilan saat ini ke PDF untuk briefing materi.

---

## 3. Navigasi & Interaksi

### 3.1 Peta Navigasi

| Dari Layar / Komponen | User Klik / Aksi | Menuju Ke | Context yang Dibawa |
|----------------------|------------------|-----------|---------------------|
| Ringkasan Kondisi Daerah (2.1) | Klik kartu Indeks Kondisi Daerah | Modal penjelasan komposisi indeks | Breakdown modul mana yang berkontribusi |
| Ringkasan Kondisi Daerah (2.1) | Klik kartu Pengaduan Aktif | Modul `02_MANAJEMEN_PENGADUAN` halaman utama | Filter status = "aktif" pre-set |
| Ringkasan Kondisi Daerah (2.1) | Klik salah satu Top 5 Isu Viral | Modul `03_PERSEPSI_PUBLIK` detail isu | Isu ID dari item yang diklik |
| Ringkasan Kondisi Daerah (2.1) | Klik kartu Realisasi APBD | Modul `06_PROGRAM_KONTROL_FISKAL` halaman utama | Tahun anggaran berjalan |
| Ringkasan Kondisi Daerah (2.1) | Klik kartu Status Early Warning | Modul `08_EARLY_WARNING_RISIKO` halaman utama | Filter status warna saat ini |
| Peta Interaktif (2.2) | Klik area di peta | Panel detail samping muncul | Area ID + ringkasan kondisi area |
| Peta Interaktif (2.2) | Klik penanda lokasi proyek | Modal detail proyek | Proyek ID + status realisasi |
| Peta Interaktif (2.2) | Klik tombol "Lihat Detail" di panel area | Modul terkait area (Pengaduan / EWS / Layanan) | Area ID |
| Panel Trend & Analitik (2.3) | Klik kategori di diagram donat | Modul `02_MANAJEMEN_PENGADUAN` | Filter kategori aduan |
| Panel Trend & Analitik (2.3) | Klik OPD di tabel rangking | Modul `04_KUALITAS_PELAYANAN` | Filter OPD ID |
| Panel Trend & Analitik (2.3) | Klik tombol Export PDF | Modal preview PDF | Tampilan dashboard saat ini |

### 3.2 Decision Branch

- **Klik kartu Pengaduan Aktif**:
  - Kalau user role kepala daerah/sekda → masuk ke Modul Pengaduan view ringkasan eksekutif
  - Kalau user role kepala OPD → masuk ke Modul Pengaduan dengan filter aduan domain OPD tersebut

- **Klik area di peta**:
  - Kalau zoom level provinsi → tampilkan ringkasan tingkat kabupaten
  - Kalau zoom level kabupaten → tampilkan ringkasan tingkat kecamatan
  - Kalau zoom level kecamatan → tampilkan detail aduan + proyek + fasilitas

- **Klik kartu Status Early Warning kalau warna Merah**:
  - Tampilkan modal peringatan dengan detail isu kritis dan rekomendasi langkah
  - Tombol "Eskalasi" → trigger notif WhatsApp ke tim krisis
  - Tombol "Lihat Detail" → masuk ke Modul Early Warning

### 3.3 Navigasi Masuk dari Modul Lain

- Dari **Modul `02_MANAJEMEN_PENGADUAN`** halaman ringkasan, ada tombol "Lihat di Dashboard" → masuk ke Dashboard Situasional dengan kartu Pengaduan Aktif highlighted.
- Dari **Modul `08_EARLY_WARNING_RISIKO`** alert detail, ada tombol "Lihat Konteks Daerah" → masuk ke Dashboard Situasional dengan peta zoomed ke wilayah affected.
- Dari **Modul `06_PROGRAM_KONTROL_FISKAL`** halaman fiskal, ada tombol "Lihat di Dashboard" → masuk ke Dashboard Situasional dengan kartu Realisasi APBD highlighted.

---

## 4. Alur Bisnis

### 4.1 Alur Pemantauan Rutin Pagi (Happy Path)

```
┌──────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
│ Kepala Daerah    │────▶│ Buka aplikasi mobile │────▶│ Lihat Indeks Kondisi │
│ pukul 07:00      │     │ atau dashboard web   │     │ Daerah (skor utama)  │
└──────────────────┘     └──────────────────────┘     └──────────────────────┘
                                                              │
                                                              ▼
                                                  ┌────────────────────────┐
                                                  │ Indeks bagus (>75)?    │
                                                  └────────────────────────┘
                                                       │              │
                                                  Ya: lanjut    Tidak: drill
                                                       │              │
                                                       ▼              ▼
                                          ┌──────────────────┐  ┌────────────────────┐
                                          │ Skim Top 5 Viral │  │ Klik kartu kritis  │
                                          │ untuk briefing   │  │ (EWS/Aduan/Sentimen)│
                                          │ media            │  └────────────────────┘
                                          └──────────────────┘            │
                                                                          ▼
                                                              ┌────────────────────────┐
                                                              │ Masuk ke modul detail  │
                                                              │ untuk konteks lengkap   │
                                                              └────────────────────────┘
                                                                          │
                                                                          ▼
                                                              ┌────────────────────────┐
                                                              │ Catat untuk rapat      │
                                                              │ koordinasi pukul 09:00 │
                                                              └────────────────────────┘
```

**Penjelasan singkat:** Eksekutif buka dashboard pagi sebelum agenda hari. Kalau kondisi normal, cukup skim top 5 isu viral untuk briefing media. Kalau ada indikator kritis, langsung drill-down ke modul detail untuk konteks dan persiapan rapat.

### 4.2 Alur Respons Krisis (UX flow penting)

```
┌────────────────────┐     ┌──────────────────────┐     ┌─────────────────────────┐
│ Status EWS berubah │────▶│ Notif push ke mobile │────▶│ Eksekutif buka dashboard│
│ jadi Merah         │     │ eksekutif + sekda    │     │ langsung ke alert       │
└────────────────────┘     └──────────────────────┘     └─────────────────────────┘
                                                                   │
                                                                   ▼
                                                       ┌─────────────────────────┐
                                                       │ Modal alert tampil      │
                                                       │ dengan detail isu       │
                                                       │ + rekomendasi langkah    │
                                                       └─────────────────────────┘
                                                                   │
                                                       ┌───────────┴───────────┐
                                                       ▼                       ▼
                                          ┌────────────────────┐  ┌──────────────────────┐
                                          │ Klik "Eskalasi"    │  │ Klik "Lihat Detail"  │
                                          │ → trigger WhatsApp │  │ → masuk Modul EWS    │
                                          │ ke tim krisis      │  │ untuk konteks penuh  │
                                          └────────────────────┘  └──────────────────────┘
                                                       │                       │
                                                       └───────────┬───────────┘
                                                                   ▼
                                                       ┌─────────────────────────┐
                                                       │ Eksekutif kasih instruksi│
                                                       │ langsung ke kepala OPD   │
                                                       │ via aplikasi atau WA     │
                                                       └─────────────────────────┘
                                                                   │
                                                                   ▼
                                                       ┌─────────────────────────┐
                                                       │ Tindak lanjut tracked    │
                                                       │ di intervention log      │
                                                       └─────────────────────────┘
```

**Penjelasan:** Saat status EWS berubah merah, sistem push notif ke eksekutif. Eksekutif buka dashboard, lihat detail isu di modal alert, dan punya 2 jalur cepat: (a) eskalasi langsung ke tim krisis via WhatsApp, atau (b) drill-down ke Modul EWS untuk konteks penuh sebelum kasih instruksi. Tindak lanjut tercatat untuk audit dan evaluasi.

### 4.3 Alur Edge Case — Sumber Data Tidak Sinkron

```
┌──────────────────────┐     ┌──────────────────────┐     ┌─────────────────────────┐
│ Salah satu sumber    │────▶│ Sistem detect data    │────▶│ Banner peringatan       │
│ data eksternal       │     │ stale (> 1 jam tidak  │     │ muncul di dashboard:    │
│ (LAPOR/SIPD/SIKD)    │     │ update)               │     │ "Data X terakhir update│
│ down                 │     └──────────────────────┘     │ pukul 06:30 — sumber    │
└──────────────────────┘                                  │ sedang gangguan"        │
                                                          └─────────────────────────┘
                                                                   │
                                                                   ▼
                                                       ┌─────────────────────────┐
                                                       │ User tetap bisa lihat   │
                                                       │ data snapshot terakhir  │
                                                       │ tapi tahu ini stale     │
                                                       └─────────────────────────┘
                                                                   │
                                                       ┌───────────┴───────────┐
                                                       ▼                       ▼
                                          ┌────────────────────┐  ┌──────────────────────┐
                                          │ Klik "Coba Sinkron"│  │ Lanjut dengan data   │
                                          │ → sistem retry     │  │ snapshot, notif tim  │
                                          │ koneksi            │  │ IT untuk investigasi │
                                          └────────────────────┘  └──────────────────────┘
                                                       │
                                                       ▼
                                          ┌────────────────────┐
                                          │ Kalau berhasil →   │
                                          │ banner hilang,     │
                                          │ data refresh.      │
                                          │ Kalau gagal →      │
                                          │ notif tim IT.      │
                                          └────────────────────┘
```

**Penjelasan:** Edge case kritis untuk modul yang tergantung sumber eksternal. Sistem harus jujur ke user kalau data stale, tapi tetap usable dengan snapshot terakhir. User punya 2 opsi: retry sinkronisasi atau lanjut dengan acknowledgment.

---

## 5. Data yang Dikelola Modul

> Modul Dashboard Situasional **tidak mengelola entity bisnis sendiri** — modul ini agregator dan presenter dari modul-modul lain. Data yang ditampilkan ditarik real-time dari modul terkait (Pengaduan, Persepsi, Layanan, Fiskal, dst).
>
> Yang dikelola modul ini adalah **cache agregasi** untuk akses cepat dan **konfigurasi tampilan per user role** — tapi keduanya bersifat utility, bukan entity bisnis utama.

### 5.1 Konfigurasi Tampilan per Role

| Field | Deskripsi | Contoh Nilai |
|-------|-----------|---------------|
| Role | Jabatan user yang menentukan layout default | kepala_daerah / sekda / kepala_opd / staf |
| Komponen Aktif | Daftar komponen visual yang tampil di dashboard role tersebut | Indeks, EWS, Aduan, Sentimen, Top 5 Viral |
| Filter Default | Filter yang otomatis aktif saat user login | Periode = hari ini, area = seluruh wilayah |
| Frekuensi Refresh | Setting refresh otomatis dashboard | 30 detik / 1 menit / 5 menit |

### 5.2 Catatan untuk Tim Downstream

- **Dashboard tidak punya database transaksi sendiri** — semua data dari modul lain via integrasi.
- **Cache agregasi** dibutuhkan untuk performance (Indeks Kondisi Daerah dihitung dari banyak modul, mahal kalau dihitung on-the-fly setiap render).
- **Konfigurasi tampilan per role** disimpan terpisah dari user data — kalau user pindah role, tampilan langsung berubah tanpa data hilang.

---

## 6. Kebutuhan Data Eksternal

> Modul ini **tidak konsumsi data eksternal langsung** — semua data datang dari modul lain via internal integration. Sumber data eksternal yang relevan adalah dari modul-modul yang feed ke Dashboard ini.
>
> Lihat Section 4 (Konsolidasi Kebutuhan Data Eksternal) di `00_OVERVIEW.md` untuk daftar lengkap sumber data sistem keseluruhan.

### Catatan Khusus

Modul Dashboard Situasional bergantung pada **kualitas data dari modul lain**. Kalau Modul Pengaduan delay 1 jam, kartu "Pengaduan Aktif" di dashboard juga akan stale 1 jam. Section 4.3 (Alur Edge Case) sudah cover skenario ini.

---

## 7. Stack Agent Modul

> Modul Dashboard Situasional adalah agregator yang tidak ingest data eksternal sendiri — dia konsumsi insight dari modul lain. Stack agent-nya **minimal** (2 agent) sesuai prinsip "agent stack mengikuti kebutuhan modul, bukan template".

### 7.1 Daftar Agent

| Agent Type | Peran di Modul Ini | Trigger | Output |
|------------|---------------------|---------|--------|
| Orchestrator Agent | Koordinasi tarik insight dari modul-modul lain (Pengaduan, Persepsi, EWS, Fiskal) untuk render dashboard agregat. Saat status EWS critical, coordinate juga modal alert + notification ke eksekutif. | System-level | Routing decision ke modul-modul sumber data, aggregate state untuk Reporting |
| Reporting Agent | Render dashboard agregat dengan layout per role (kepala daerah / sekda / kepala OPD / staf), termasuk peta interaktif, panel trend, dan top 5 viral. | Manual / scheduled | Dashboard rendering up-to-date dengan filter dan refresh otomatis |

### 7.2 Catatan Pattern Adaptive

- Modul ini **tidak punya** Data Collection sendiri — agregator pure. Counter-rule "Project dengan data internal sudah lengkap" apply: data sudah ada di modul-modul sumber yang punya pipeline ingest sendiri.
- Modul ini **tidak butuh** Analysis Agent sendiri — insight sudah di-analisis di modul-modul sumber. Dashboard cuma display ulang.
- Saat status EWS critical (severity HIGH dari Modul 08), Orchestrator Modul Dashboard **coordinate dengan Orchestrator Modul EWS** untuk consistent state dan eskalasi terkoordinasi.

### 7.3 Agent Shared dengan Modul Lain

- **Orchestrator Agent** — instance terpisah dari Orchestrator di Modul `03_PERSEPSI_PUBLIK` dan `08_EARLY_WARNING_RISIKO`. Tidak shared single instance. Tapi protocol koordinasi konsisten di OVERVIEW Section "Konsolidasi Stack Agent".
- **Reporting Agent** — shared technical pattern dengan modul lain yang generate report, tapi instance per modul.

---

## 8. Konfigurasi Alert

### 8.1 Threshold

| Kondisi | Threshold | Aksi |
|---------|-----------|------|
| Indeks Kondisi Daerah normal | Skor >= 75 | Tampilkan hijau, tidak ada notif |
| Indeks Kondisi Daerah perhatian | Skor 60-74 | Tampilkan kuning + badge peringatan di dashboard |
| Indeks Kondisi Daerah kritis | Skor < 60 | Tampilkan merah + push notif ke eksekutif + kepala OPD relevan |
| Status EWS berubah jadi Merah | Trigger dari Modul EWS | Push notif mobile ke eksekutif + sekda + tim krisis |
| Lonjakan aduan sehari | > 200% rata-rata 7 hari | Push notif ke kepala OPD domain aduan + sekda |

### 8.2 Severity Levels

| Level | Warna | Tampilan di UI | Notifikasi |
|-------|-------|---------------|------------|
| Hijau / Normal | Hijau | Tampil normal di dashboard, tanpa highlight khusus | Tidak ada |
| Kuning / Perlu Perhatian | Kuning | Ditandai dengan badge peringatan di kartu terkait | Notif internal di panel notifikasi dashboard |
| Merah / Kritis | Merah | Ditampilkan paling atas dashboard dengan kartu khusus, blink animasi sementara | Push notif mobile + memicu alert ke modul WhatsApp untuk tim krisis |

---

## 9. Standar Layanan yang Diharapkan

### 9.1 Kecepatan Tampil Data

| Aspek | Standar Diharapkan |
|-------|---------------------|
| Tampil halaman pertama dashboard | Cepat |
| Pembaruan kartu ringkasan | Cepat |
| Respons interaksi (klik, filter, drill-down) | Cepat |
| Render peta interaktif dengan layer aktif | Sedang (peta wajar lebih lambat dari kartu) |

### 9.2 Frekuensi Pembaruan Data

| Jenis Data | Frekuensi |
|-----------|-----------|
| Kartu ringkasan eksekutif | Real-time |
| Status EWS | Real-time |
| Aduan aktif | Real-time |
| Sentimen publik | Per jam |
| Realisasi APBD | Harian |
| PDRB / pertumbuhan ekonomi | Per triwulan |
| Layer peta (aduan, EWS) | Real-time |
| Layer peta (infrastruktur, fasilitas) | Per minggu |

### 9.3 Ketersediaan Layanan

| Aspek | Standar Diharapkan |
|-------|---------------------|
| Jam operasional | 24-7 |
| Toleransi downtime | Rendah |
| Konteks bisnis | Dashboard adalah tools utama eksekutif untuk monitoring harian dan respons krisis. Status EWS yang real-time tidak boleh terinterupsi karena bencana atau krisis tidak mengenal jam kerja. |

---

## 10. Use Case Scenarios

### 10.1 Skenario Pemantauan Rutin Pagi Eksekutif

**Aktor**: Kepala Daerah
**Goal**: Mengetahui kondisi daerah keseluruhan sebelum agenda harian dan rapat koordinasi pukul 09:00

```
1. Pukul 07:00, Kepala Daerah buka aplikasi mobile RIS dari rumah.
2. Sistem tampilkan Ringkasan Kondisi Daerah dengan indeks skor 78/100 (hijau).
3. Kepala Daerah skim Top 5 Isu Viral untuk konteks media briefing — lihat 1 isu kenaikan PBB sedang trending.
4. Kepala Daerah klik isu tersebut → masuk Modul Persepsi Publik dengan detail sentiment + sample postingan.
5. Setelah baca konteks, Kepala Daerah kembali ke Dashboard, klik kartu Aduan Aktif → masuk Modul Pengaduan untuk lihat aduan terkait kebijakan PBB.
6. Kepala Daerah catat 2 poin di feature notes app — (a) klarifikasi PBB di rapat koordinasi, (b) instruksi ke Bapenda untuk siapkan FAQ.
7. Pukul 09:00, Kepala Daerah punya konteks data lengkap untuk rapat koordinasi.
```

### 10.2 Skenario Edge Case — Krisis di Tengah Malam

**Aktor**: Sekretaris Daerah
**Goal**: Respon cepat kalau ada peringatan dini bencana di luar jam kerja

```
1. Pukul 23:30, Modul Early Warning detect indikator banjir di 3 kecamatan (curah hujan ekstrem dari BMKG + ketinggian air dari sensor).
2. Sistem ubah Status EWS jadi Merah.
3. Push notif mobile dikirim ke Sekda + Kepala BPBD + Wali Kota.
4. Sekda buka aplikasi RIS dari notif → langsung masuk modal alert di Dashboard.
5. Modal alert tampilkan: detail isu (banjir 3 kecamatan), rekomendasi langkah (aktivasi posko, koordinasi tim SAR), peta wilayah affected.
6. Sekda klik "Eskalasi" → trigger broadcast WhatsApp ke tim krisis BPBD + Camat 3 kecamatan + tim Pol PP.
7. Sekda klik "Lihat Detail" → masuk Modul EWS untuk lihat data sensor + prakiraan BMKG 6 jam ke depan.
8. Sekda kasih instruksi via aplikasi RIS ke Camat affected: "Aktifkan posko, koordinasi dengan TNI/Polri."
9. Tindak lanjut tracked di intervention log Modul EWS untuk evaluasi pasca-kejadian.
```

### 10.3 Skenario Briefing Stakeholder Eksternal

**Aktor**: Tim Asisten Kepala Daerah
**Goal**: Siapkan materi briefing untuk pertemuan dengan stakeholder eksternal (DPRD, kementerian)

```
1. Tim Asisten buka Dashboard Situasional di laptop, mode "detail lengkap".
2. Tim Asisten pilih rentang waktu kustom: 90 hari terakhir.
3. Tim Asisten lihat Panel Trend & Analitik — tren indeks 90 hari, perbandingan periode lalu.
4. Tim Asisten klik tombol Export PDF → modal preview muncul dengan tampilan dashboard saat ini.
5. Tim Asisten pilih sections yang relevan untuk briefing (Indeks, EWS, Top 5 Viral, Realisasi APBD).
6. Tim Asisten klik Generate → sistem produksi PDF dengan watermark resmi pemkab.
7. Tim Asisten download PDF, share ke Kepala Daerah untuk review sebelum pertemuan.
```

---

## 11. Referensi Implementasi

### 11.1 Jakarta Smart City Dashboard

**URL**: https://smartcity.jakarta.go.id/

**Fitur yang Diadaptasi**:
- Pendekatan dashboard real-time dengan multi-modul terintegrasi
- Pola peta interaktif dengan layer toggle untuk berbagai dimensi data
- Pola escalation dari dashboard ke kanal komunikasi (CROP)

### 11.2 Alberta Economic Dashboard (Kanada)

**URL**: https://economicdashboard.alberta.ca/

**Fitur yang Diadaptasi**:
- Pendekatan custom dashboard builder per role/audience
- Pola visualisasi indikator regional dengan drill-down geospatial
- Pendekatan transparency portal untuk publik

### 11.3 UNDP Crisis Risk Dashboard

**URL**: https://www.undp.org/

**Fitur yang Diadaptasi**:
- Pola early warning visualization dengan status warna
- Pola crisis monitoring yang integrate ke action plan
- Pendekatan multi-stakeholder coordination untuk respons krisis

---

*Dokumen ini merupakan bagian dari Dokumentasi Brief Sistem Intelijen Regional (RIS)*
*Modul: Dashboard Situasional | Versi: 1.0.0*
