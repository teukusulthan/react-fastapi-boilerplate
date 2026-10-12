# Modul Persepsi Publik & Komunikasi Strategis

## 1. Gambaran Umum

Modul Persepsi Publik & Komunikasi Strategis adalah sistem berbasis kecerdasan buatan untuk memantau, menganalisis, dan merespons persepsi masyarakat terhadap kinerja pemerintah daerah. Sistem ini mengagregasi data dari media sosial, portal berita, dan kanal komunikasi publik untuk menghasilkan insight komunikasi strategis yang dapat ditindaklanjuti tim humas dan eksekutif.

Modul ini paling **agent-heavy** di sistem RIS karena melibatkan multi-stage processing: dari ingestion data lintas-platform, cleaning text bahasa natural, analisis sentiment dan emotion, deteksi viral score, klasifikasi narrative, hingga generate strategi komunikasi dan eskalasi alert ke decision-maker.

### 1.1 Tujuan Modul

| Tujuan | Deskripsi |
|--------|-----------|
| Pemantauan Sentimen | Memantau sentimen publik terhadap pemerintah daerah secara real-time lintas platform |
| Deteksi Isu Viral | Mengidentifikasi isu yang sedang trending atau viral untuk respons cepat |
| Analisis Narasi | Memahami narasi yang berkembang di masyarakat (apresiasi, kritik, konspirasi, ajakan aksi) |
| Strategi Komunikasi | Memberikan rekomendasi action plan komunikasi yang data-driven |
| Antisipasi Krisis | Mendeteksi potensi krisis reputasi sebelum eskalasi |

### 1.2 Target Pengguna

| Pengguna | Kebutuhan |
|----------|-----------|
| Humas / Tim Komunikasi | Monitoring harian, drafting respons, koordinasi kampanye |
| Sekretaris Daerah | Briefing eksekutif, koordinasi lintas OPD untuk respons isu |
| Kepala Daerah | Awareness kondisi persepsi publik untuk decision strategis dan media briefing |
| Tim Crisis Response | Aktivasi saat isu critical, koordinasi multi-channel response |

---

## 2. Fitur Utama

### 2.1 Pemantauan Lintas Platform

**Deskripsi**: Sistem monitoring real-time untuk memantau pembicaraan tentang pemerintah daerah di berbagai platform digital.

**Komponen Visual**:

| Komponen | Tipe | Data | Update |
|----------|------|------|--------|
| Indikator status pemantauan per platform | Indikator status warna | Status koneksi 7 platform (aktif / gangguan / offline) | Real-time |
| Counter postingan ter-monitor hari ini | Kartu ringkasan dengan trend arrow | Total postingan masuk + perubahan dari kemarin | Real-time |
| Distribusi postingan per platform | Diagram batang | Jumlah postingan per Twitter/X, IG, FB, TikTok, YouTube, news, forum | Per jam |
| Daftar keyword yang dimonitor | Tabel daftar dengan filter | Keyword aktif: nama instansi, nama eksekutif, hashtag daerah, kategori OPD | Statis dengan editor manual |

**Platform yang Dimonitor**:

| Platform | Cakupan | Frekuensi Update |
|----------|---------|-------------------|
| Twitter / X | Postingan publik dengan keyword pemerintah daerah | Real-time |
| Instagram | Postingan publik + komentar di akun resmi pemerintah | Per jam |
| Facebook | Postingan publik + komentar di halaman resmi | Per jam |
| TikTok | Video publik dengan keyword | Per jam |
| YouTube | Komentar di video terkait pemerintah daerah | Per jam |
| Portal berita | 50+ situs berita lokal-nasional | Per jam |
| Forum publik | Forum diskusi tentang pemerintah daerah | Per 6 jam |

**Interaksi**:

- Filter berdasarkan platform spesifik untuk lihat aktivitas per kanal
- Klik counter postingan untuk masuk ke daftar postingan terbaru
- Edit daftar keyword (tambah/hapus/edit) dengan tombol aksi di tabel keyword
- Toggle indikator status untuk pause/resume monitoring per platform

### 2.2 Analisis Sentimen dan Emosi

**Deskripsi**: Klasifikasi otomatis sentimen dan emosi dari setiap postingan yang ter-monitor.

**Komponen Visual**:

| Komponen | Tipe | Data | Update |
|----------|------|------|--------|
| Distribusi sentimen overall | Diagram donat | Persentase positif / netral / negatif hari ini | Real-time |
| Tren sentimen 7 hari | Grafik garis tren | Persentase per kategori sentimen lintas waktu | Real-time |
| Distribusi emosi | Diagram batang | Persentase per emosi: marah, sedih, bahagia, takut, jijik, terkejut | Per jam |
| Skor net sentimen | Kartu ringkasan | Angka komposit -1.0 sampai +1.0 dengan trend arrow | Real-time |
| Sample postingan per sentimen | Galeri kartu | 3-5 postingan contoh per kategori sentimen | Real-time |

**Klasifikasi Sentimen**:

| Sentimen | Definisi | Contoh Indikator |
|----------|----------|------------------|
| Sangat Positif | Puas, mengapresiasi tinggi | "sangat bagus", "luar biasa", "terima kasih" |
| Positif | Cenderung puas | "baik", "lancar", "memuaskan" |
| Netral | Faktual, tanpa opini | "informasi", "pengumuman", "berita" |
| Negatif | Cenderung tidak puas | "lambat", "kurang", "mengecewakan" |
| Sangat Negatif | Marah, kecewa berat | "parah", "memalukan", "mengerikan" |

**Interaksi**:

- Filter tampilan berdasarkan rentang waktu (24 jam / 7 hari / 30 hari / kustom)
- Klik segmen di diagram donat untuk drill-down ke postingan kategori sentimen tersebut
- Klik kartu sample postingan untuk lihat detail postingan + thread komentar
- Toggle antara mode sentimen overall dan mode per platform

### 2.3 Deteksi Isu Viral

**Deskripsi**: Identifikasi isu yang sedang trending atau viral berdasarkan volume, growth rate, engagement, dan keterlibatan influencer.

**Komponen Visual**:

| Komponen | Tipe | Data | Update |
|----------|------|------|--------|
| Daftar viral issues hari ini | Tabel daftar dengan filter | Top 10 isu dengan viral score, mentions, sentiment, trend | Per 15 menit |
| Skor viral per isu | Indikator status warna | Hijau (emerging) / Kuning (trending) / Merah (highly viral) | Per 15 menit |
| Detail breakdown isu | Modal detail | Timeline mention, sample posts, top influencer, sentiment breakdown | On-demand saat klik |
| Distribusi platform per isu | Diagram batang | Mentions per platform untuk isu tertentu | Per 15 menit |
| Top influencer | Daftar urutan prioritas | 5 akun dengan engagement tertinggi mention isu | Per jam |

**Klasifikasi Viral**:

| Level | Skor Viral | Aksi UI |
|-------|-----------|---------|
| Emerging | 0.25 - 0.50 | Tampil di daftar dengan warna hijau muda |
| Trending | 0.50 - 0.75 | Ditandai dengan badge "Trending" warna kuning |
| Highly Viral | 0.75 - 1.00 | Pin di atas dengan warna merah, trigger alert |

**Kategori Isu**:

| Kategori | Contoh Isu |
|----------|-----------|
| Pelayanan | Antrean panjang di kantor pelayanan, proses perizinan lambat |
| Infrastruktur | Jalan rusak, banjir, listrik padam |
| Kebijakan | Kenaikan PBB, tarif retribusi, regulasi baru |
| Keuangan | Dugaan penyimpangan anggaran, transparansi APBD |
| Sosial | Bantuan tidak sampai, kesenjangan, diskriminasi |
| Lingkungan | Sampah menumpuk, polusi, deforestasi |

**Interaksi**:

- Filter berdasarkan kategori isu, rentang waktu, dan level viral
- Klik baris isu untuk buka modal detail breakdown
- Klik "Track Issue" untuk pin isu di dashboard untuk monitoring berkelanjutan
- Klik "Generate Recommendation" untuk trigger Planning Agent membuat strategi komunikasi

### 2.4 Analisis Narasi

**Deskripsi**: Klasifikasi narasi dan framing yang berkembang di masyarakat untuk paham bagaimana isu di-framed.

**Komponen Visual**:

| Komponen | Tipe | Data | Update |
|----------|------|------|--------|
| Distribusi narasi per isu | Diagram donat | Persentase per tipe narasi | Per jam |
| Daftar tipe narasi dominan | Tabel daftar | 6 tipe narasi dengan persentase prevalensi | Per jam |
| Sample postingan per narasi | Galeri kartu | 2-3 postingan contoh per tipe narasi | Per jam |

**Tipe Narasi**:

| Tipe | Karakteristik | Contoh |
|------|---------------|--------|
| Apresiasi Pencapaian | Mengakui keberhasilan program | "Program X berhasil menurunkan kemiskinan" |
| Narasi Kegagalan | Penekanan kegagalan implementasi | "Janji tidak ditepati, program tidak jalan" |
| Teori Konspirasi | Asumsi adanya kepentingan tersembunyi | "Ada kepentingan tertentu di balik kebijakan" |
| Posisi Korban | Klaim sebagai pihak yang dirugikan | "Rakyat yang dirugikan oleh kebijakan ini" |
| Ajakan Aksi | Ajakan protes atau gerakan | "Mari kita protes ke kantor pemerintah" |
| Laporan Faktual | Pemaparan data tanpa framing | "Data menunjukkan realisasi 65%" |

**Interaksi**:

- Klik segmen di diagram donat untuk drill-down ke postingan tipe narasi tersebut
- Filter berdasarkan isu spesifik untuk lihat narasi dominan per isu
- Klik kartu sample untuk lihat detail postingan dan thread

### 2.5 Rekomendasi Strategi Komunikasi

**Deskripsi**: Sistem rekomendasi action plan komunikasi berbasis analisis sentimen, viral, dan narasi.

**Komponen Visual**:

| Komponen | Tipe | Data | Update |
|----------|------|------|--------|
| Daftar rekomendasi prioritas | Tabel daftar dengan filter | Rekomendasi action dengan priority, channel, deadline | Event-driven (saat alert masuk) |
| Detail rekomendasi | Modal detail | Key messages, target audience, channel, timeline, format konten yang disarankan | On-demand |
| Status implementasi | Indikator status warna | Draft / In Approval / Published / Monitoring | Real-time |

**Tipe Rekomendasi**:

| Situasi | Rekomendasi | Aksi yang Disarankan |
|---------|-------------|----------------------|
| Sentimen negatif meningkat tajam | Komunikasi proaktif | Press release + klarifikasi |
| Misinformation viral | Respons fact-check | Infografis rebuttal + video klarifikasi |
| Narasi kegagalan dominan | Amplifikasi success story | Share data pencapaian |
| Tren keluhan layanan spesifik | Pengumuman perbaikan | Action plan publikasi |
| Potensi krisis terdeteksi | Pre-emptive messaging | Stakeholder engagement |

**Interaksi**:

- Klik baris rekomendasi untuk buka modal detail dengan key messages dan saran format
- Klik "Approve & Draft Content" untuk masuk ke editor konten dengan template pre-filled
- Klik "Reject" dengan alasan untuk feedback ke sistem (untuk Learning Agent improvement)
- Filter berdasarkan status implementasi atau priority

### 2.6 Dashboard Persepsi Komprehensif

**Deskripsi**: Dashboard utama yang konsolidasi semua sub-fitur untuk view holistik persepsi publik.

**Komponen Visual**:

| Komponen | Tipe | Data | Update |
|----------|------|------|--------|
| Skor persepsi keseluruhan | Kartu ringkasan dengan angka utama | Net sentimen score 0-100 + trend arrow | Real-time |
| Status alert aktif | Indikator status warna | Hijau / Kuning / Merah berdasarkan threshold breach terkini | Real-time |
| Top 5 viral issues | Daftar urutan prioritas | 5 isu paling viral dengan mini sparkline | Per 15 menit |
| Distribusi sentimen per platform | Diagram batang stacked | Sentimen per platform (Twitter, IG, FB, TikTok, YouTube, news) | Real-time |
| Geographic distribution | Peta lokasi interaktif | Sentimen ter-mention per wilayah daerah | Per jam |
| Word cloud topik populer | Visualisasi awan kata | Top 50 kata kunci hari ini dengan ukuran proporsional ke frekuensi | Per jam |

**Interaksi**:

- Pilih rentang waktu (24 jam / 7 hari / 30 hari / kustom)
- Klik area di peta untuk filter analisis ke wilayah tersebut
- Klik kata di word cloud untuk filter ke postingan dengan kata kunci tersebut
- Toggle tampilan antara mode "ringkasan eksekutif" dan "detail operator humas"
- Export tampilan dashboard ke PDF untuk briefing materi

---

## 3. Navigasi & Interaksi

### 3.1 Peta Navigasi

| Dari Layar / Komponen | User Klik / Aksi | Menuju Ke | Context yang Dibawa |
|----------------------|------------------|-----------|---------------------|
| Dashboard Persepsi (2.6) | Klik kartu Skor Persepsi | Modal breakdown komposisi skor | Detail kontribusi sentimen, viral, narasi |
| Dashboard Persepsi (2.6) | Klik salah satu Top 5 Viral | Modal Detail Isu Viral (di 2.3) | Isu ID + breakdown timeline |
| Dashboard Persepsi (2.6) | Klik area di peta | Tampilan dashboard ter-filter wilayah | Wilayah ID |
| Pemantauan Lintas Platform (2.1) | Klik counter postingan hari ini | Daftar postingan terbaru | Filter periode = hari ini |
| Analisis Sentimen (2.2) | Klik segmen diagram donat | Daftar postingan kategori sentimen | Filter sentimen + periode |
| Daftar Viral Issues (2.3) | Klik baris isu | Modal Detail Isu Viral | Isu ID + breakdown timeline |
| Modal Detail Isu Viral | Klik tombol "Generate Recommendation" | Modul `02_MANAJEMEN_PENGADUAN` modal generate | Isu ID + kategori + sentimen breakdown |
| Modal Detail Isu Viral | Klik tombol "Track Issue" | Dashboard Persepsi dengan isu pinned | Isu ID untuk tracking berkelanjutan |
| Daftar Rekomendasi (2.5) | Klik baris rekomendasi | Modal Detail Rekomendasi | Rekomendasi ID + key messages |
| Modal Detail Rekomendasi | Klik "Approve & Draft Content" | Editor konten dengan template pre-filled | Rekomendasi ID + template content |
| Alert Modal (status critical) | Klik "Eskalasi ke Tim Krisis" | Modul Notifikasi (broadcast WhatsApp) | Isu ID + severity + tim krisis recipient |
| Alert Modal (status critical) | Klik "Lihat Detail" | Modal Detail Isu Viral | Isu ID |

### 3.2 Decision Branch

- **Klik tombol "Generate Recommendation"**:
  - Kalau isu kategori "Misinformation" → Planning Agent generate template fact-check + infografis
  - Kalau isu kategori "Sentiment Drop" → Planning Agent generate template press release + key messages
  - Kalau isu kategori "Crisis Potential" → Trigger Orchestrator untuk aktivasi crisis flow

- **Status alert berdasarkan severity**:
  - LOW (viral score 0.25-0.50) → Tampil hijau di dashboard, monitoring only, tidak ada notif
  - MEDIUM (viral score 0.50-0.75) → Tampil kuning, push notif ke humas
  - HIGH (viral score 0.75+) → Tampil merah, push notif ke humas + sekda + crisis team, trigger crisis flow

### 3.3 Navigasi Masuk dari Modul Lain

- Dari **Modul `01_DASHBOARD_SITUASIONAL`** Top 5 Isu Viral → klik isu → masuk ke Modal Detail Isu Viral di modul ini
- Dari **Modul `01_DASHBOARD_SITUASIONAL`** kartu Sentimen Publik → masuk ke Dashboard Persepsi (2.6) di modul ini
- Dari **Modul `08_EARLY_WARNING_RISIKO`** kalau ada krisis terdeteksi yang related ke persepsi publik (cth: krisis reputasi) → masuk ke Dashboard Persepsi dengan filter wilayah affected

---

## 4. Alur Bisnis

### 4.1 Alur Monitoring Harian (Happy Path)

```
┌──────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
│ Humas pukul      │────▶│ Buka Dashboard       │────▶│ Skim skor persepsi    │
│ 08:00 pagi       │     │ Persepsi             │     │ keseluruhan + alert   │
└──────────────────┘     └──────────────────────┘     └──────────────────────┘
                                                                 │
                                                                 ▼
                                                     ┌──────────────────────┐
                                                     │ Skor normal (>70)?   │
                                                     └──────────────────────┘
                                                          │            │
                                                     Ya: lanjut    Tidak: drill
                                                          │            │
                                                          ▼            ▼
                                              ┌──────────────────┐  ┌────────────────────┐
                                              │ Cek Top 5 Viral  │  │ Klik viral issue   │
                                              │ untuk konteks    │  │ severity tertinggi │
                                              │ briefing         │  └────────────────────┘
                                              └──────────────────┘            │
                                                                              ▼
                                                                  ┌────────────────────────┐
                                                                  │ Modal detail isu       │
                                                                  │ tampil dengan timeline │
                                                                  │ + sample posts         │
                                                                  └────────────────────────┘
                                                                              │
                                                                              ▼
                                                                  ┌────────────────────────┐
                                                                  │ Klik "Generate         │
                                                                  │ Recommendation"        │
                                                                  └────────────────────────┘
                                                                              │
                                                                              ▼
                                                                  ┌────────────────────────┐
                                                                  │ Sistem generate action │
                                                                  │ plan + key messages    │
                                                                  └────────────────────────┘
```

**Penjelasan singkat:** Humas buka dashboard pagi sebelum standup. Kalau kondisi normal, cukup briefing data viral untuk konteks. Kalau ada isu kritis, drill ke detail dan trigger recommendation engine untuk siapkan respons.

### 4.2 Alur Respons Krisis (UX Flow Penting)

```
┌────────────────────┐     ┌──────────────────────┐     ┌─────────────────────────┐
│ Sistem detect      │────▶│ Validasi sentiment + │────▶│ Skor melewati threshold │
│ viral score breach │     │ severity scoring     │     │ HIGH (>0.75)            │
│ threshold          │     └──────────────────────┘     └─────────────────────────┘
└────────────────────┘                                              │
                                                                   ▼
                                                       ┌─────────────────────────┐
                                                       │ Push notif ke humas +   │
                                                       │ sekda + crisis team via │
                                                       │ WhatsApp + email + SMS  │
                                                       └─────────────────────────┘
                                                                   │
                                                                   ▼
                                                       ┌─────────────────────────┐
                                                       │ Tim crisis buka         │
                                                       │ Dashboard Persepsi      │
                                                       │ → modal alert tampil    │
                                                       └─────────────────────────┘
                                                                   │
                                                       ┌───────────┴───────────┐
                                                       ▼                       ▼
                                          ┌────────────────────┐  ┌──────────────────────┐
                                          │ Klik "Eskalasi ke  │  │ Klik "Lihat Detail"  │
                                          │ Tim Krisis"        │  │ untuk konteks penuh  │
                                          │ → broadcast multi- │  │ sebelum keputusan    │
                                          │ channel            │  │                      │
                                          └────────────────────┘  └──────────────────────┘
                                                       │                       │
                                                       └───────────┬───────────┘
                                                                   ▼
                                                       ┌─────────────────────────┐
                                                       │ Sekda kasih instruksi    │
                                                       │ ke humas: draft press    │
                                                       │ statement + koordinasi   │
                                                       │ multi-channel response   │
                                                       └─────────────────────────┘
                                                                   │
                                                                   ▼
                                                       ┌─────────────────────────┐
                                                       │ Tindak lanjut tracked    │
                                                       │ untuk evaluasi pasca-   │
                                                       │ krisis                  │
                                                       └─────────────────────────┘
```

**Penjelasan:** Saat viral score breach threshold HIGH, sistem auto-validate severity dan push notif multi-channel ke crisis team. Crisis team punya 2 jalur cepat: (a) eskalasi langsung untuk broadcast ke jaringan crisis response, atau (b) drill-down ke detail untuk konteks sebelum kasih instruksi. Tindak lanjut tercatat untuk audit dan evaluasi.

### 4.3 Alur Edge Case — Misinformation Terdeteksi

```
┌──────────────────────┐     ┌──────────────────────┐     ┌─────────────────────────┐
│ Viral issue dengan   │────▶│ Sistem cross-check   │────▶│ Misinformation flag     │
│ klaim spesifik       │     │ dengan knowledge     │     │ teraktivasi             │
│ terdeteksi           │     │ base regulasi resmi  │     └─────────────────────────┘
└──────────────────────┘     └──────────────────────┘                  │
                                                                       ▼
                                                           ┌─────────────────────────┐
                                                           │ Modal alert tampil di   │
                                                           │ dashboard dengan flag:  │
                                                           │ "Klaim X tidak sesuai   │
                                                           │ data resmi"             │
                                                           └─────────────────────────┘
                                                                       │
                                                                       ▼
                                                           ┌─────────────────────────┐
                                                           │ Sistem auto-generate    │
                                                           │ template fact-check:    │
                                                           │ klaim + data resmi      │
                                                           │ + sumber otoritatif     │
                                                           └─────────────────────────┘
                                                                       │
                                                           ┌───────────┴───────────┐
                                                           ▼                       ▼
                                              ┌────────────────────┐  ┌──────────────────────┐
                                              │ Humas approve      │  │ Humas reject (klaim  │
                                              │ template → publish │  │ ternyata valid) →    │
                                              │ infografis + video │  │ feedback ke sistem   │
                                              │ klarifikasi        │  │ untuk training       │
                                              └────────────────────┘  └──────────────────────┘
```

**Penjelasan:** Edge case kritis untuk respons fact-check. Sistem cross-check klaim viral dengan KB regulasi resmi. Kalau ada mismatch, generate template fact-check otomatis. Humas tetap punya gate approval untuk hindari false positive.

---

## 5. Data yang Dikelola Modul

### 5.1 Entity Bisnis Utama

**Postingan Media Sosial**

| Field | Deskripsi | Contoh Nilai |
|-------|-----------|---------------|
| Platform Sumber | Asal postingan | Twitter, Instagram, Facebook, TikTok, YouTube, news, forum |
| ID Postingan Eksternal | Identitas unik dari platform asal | tweet_id, post_id, dll |
| Akun Penulis | Username + display name penulis postingan | @warga_xyz, "Warga XYZ" |
| Profil Penulis | Follower count, status verified, tipe akun | 1500 followers, non-verified, personal |
| Konten Postingan | Teks postingan + hashtag + mention + media | Free text dengan metadata |
| Engagement Metrik | Likes, shares, komentar, perkiraan reach | 45 likes, 12 shares, 23 komentar |
| Waktu Postingan | Timestamp posting di platform asal | 2026-04-07 10:30 |
| Waktu Pengumpulan | Timestamp masuk ke sistem | 2026-04-07 10:32 |
| Lokasi (kalau ada) | Lokasi geografis dari postingan | Kota X |

**Hasil Analisis Sentimen per Postingan**

| Field | Deskripsi | Contoh Nilai |
|-------|-----------|---------------|
| Postingan ID | Referensi ke entity Postingan | SOC-2026-00001234 |
| Sentimen | Label klasifikasi sentimen | sangat_positif / positif / netral / negatif / sangat_negatif |
| Skor Sentimen | Angka -1.0 sampai +1.0 | -0.65 |
| Emosi | Label klasifikasi emosi dominan | marah / sedih / takut / bahagia / jijik / terkejut |
| Sarcasm Flag | Apakah postingan terdeteksi sarkasme | true / false |
| Topic Cluster | Cluster topik hasil clustering | "pelayanan", "infrastruktur" |
| Entity Mentioned | Entity yang disebut di postingan | "Dinas Kesehatan", "Pak Walikota" |
| Waktu Analisis | Timestamp analisis dilakukan | 2026-04-07 10:33 |

**Isu Viral**

| Field | Deskripsi | Contoh Nilai |
|-------|-----------|---------------|
| Nama Isu | Label deskriptif isu | "Kenaikan Tarif Parkir" |
| Kategori | Kategorisasi isu | Pelayanan / Infrastruktur / Kebijakan / Keuangan / Sosial / Lingkungan |
| Pertama Terdeteksi | Timestamp deteksi awal | 2026-04-06 14:00 |
| Puncak Viral | Timestamp saat skor viral tertinggi | 2026-04-07 09:30 |
| Skor Viral Saat Ini | Skor 0-1 berdasarkan komposisi volume + growth + engagement + influencer | 0.89 |
| Total Mentions | Akumulasi mention sejak deteksi | 2,340 |
| Sentimen Rata-rata | Skor sentimen rata-rata postingan terkait | -0.45 |
| Top Influencer | Daftar 5 akun dengan engagement tertinggi | Array akun + follower count + jumlah mention |
| Distribusi Platform | Mention per platform | Twitter: 1200, IG: 800, FB: 340 |
| Status | Status pengelolaan isu | active / monitoring / resolved |

**Rekomendasi Komunikasi**

| Field | Deskripsi | Contoh Nilai |
|-------|-----------|---------------|
| Isu Terkait | Referensi ke entity Isu Viral | "Kenaikan Tarif Parkir" |
| Tipe Rekomendasi | Kategori action plan | clarification / fact_check / amplification / pre_emptive |
| Priority | Tingkat prioritas action | 1 (highest) / 2 / 3 |
| Saran Konten | Draft key messages + saran format | Free text + metadata format |
| Channel | Kanal yang disarankan | Array kanal: website, twitter, instagram, video |
| Target Audience | Audience yang dituju | "Warga Kota X usia 25-45" |
| Timeline | Deadline implementasi | 2026-04-07 14:00 |
| Status | Status implementasi | draft / approval / published / monitoring |

### 5.2 Sample Data atau Dummy Data

**Sample Postingan Media Sosial**

| Platform | Penulis | Konten Singkat | Likes | Sentimen | Skor |
|----------|---------|----------------|-------|----------|------|
| Twitter | @warga_xyz | "Pelayanan Dinas Kesehatan memuaskan, antrian cepat, petugas ramah" | 45 | Positif | +0.72 |
| Twitter | @user_marah | "Jalan rusak Kec. A sudah 2 bulan! Pajak dibayar tapi layanan NOL!" | 234 | Sangat Negatif | -0.85 |
| Instagram | @info_kotax | "Pengumuman: layanan keliling Dinas Kependudukan minggu ini di Kel. B" | 12 | Netral | +0.05 |

**Sample Isu Viral**

| Nama Isu | Kategori | Skor Viral | Mentions | Sentimen | Trend |
|----------|----------|-----------|----------|----------|-------|
| Kenaikan Tarif Parkir | Kebijakan | 0.89 | 2,340 | -0.45 | +340% |
| Banjir Kecamatan A | Infrastruktur | 0.72 | 1,456 | -0.32 | +180% |
| Pelayanan Kesehatan | Pelayanan | 0.45 | 987 | +0.25 | 0% |

### 5.3 Catatan untuk Tim Downstream

- **Sentimen punya skor numerik (-1 sampai +1)** dan label kategorikal — keduanya disimpan untuk fleksibilitas analisis downstream
- **Isu Viral punya status state machine**: detected → tracking → action_taken → resolved. Tidak boleh skip state.
- **Engagement metrik di-snapshot per polling**, bukan real-time — supaya history-nya tracked untuk analisis growth rate
- **Sample postingan per kategori** disimpan terbatas (top 10 per hari) untuk hindari storage bloat — analisis lengkap pakai data warehouse

---

## 6. Kebutuhan Data Eksternal

### 6.1 Sumber Data

| Sumber | Instansi / Vendor | Jenis Data | Frekuensi |
|--------|-------------------|------------|-----------|
| Twitter / X | Twitter Inc | Postingan publik dengan keyword | Real-time |
| Instagram | Meta (Instagram) | Postingan publik + komentar di akun resmi | Per jam |
| Facebook | Meta (Facebook) | Postingan publik di halaman + grup publik | Per jam |
| TikTok | TikTok | Video publik dengan keyword | Per jam |
| YouTube | Google (YouTube) | Komentar di video terkait | Per jam |
| Portal Berita Lokal-Nasional | 50+ situs berita | Artikel berita dengan keyword pemerintah daerah | Per jam |
| Forum Publik | Vendor monitoring atau scraper internal | Diskusi publik di forum | Per 6 jam |
| Vendor Media Monitoring | Awantos / Talkwalker / sejenisnya | Agregasi sentimen lintas-platform | Real-time |

### 6.2 Breakdown Data yang Diperlukan

**Dari Twitter / X:**
- Postingan publik dengan keyword nama instansi pemerintah daerah
- Postingan publik dengan hashtag terkait (cth: #pemkotxyz, #pemprovxyz)
- Mention akun resmi pemerintah daerah
- Postingan dengan keyword kategori OPD (cth: "Dinas Kesehatan [daerah]")

**Dari Instagram:**
- Postingan publik dengan keyword di caption
- Komentar di akun resmi pemerintah daerah
- Postingan dengan tag lokasi di wilayah daerah

**Dari Facebook:**
- Postingan publik di halaman terkait pemerintah daerah
- Postingan di grup publik komunitas warga

**Dari TikTok:**
- Video publik dengan keyword + hashtag terkait

**Dari YouTube:**
- Komentar di video terkait pemerintah daerah (kanal berita, kanal resmi pemerintah)

**Dari Portal Berita:**
- Artikel berita dengan keyword instansi atau eksekutif pemerintah daerah
- Headline + konten artikel + tanggal publish

**Dari Forum Publik:**
- Thread diskusi tentang pemerintah daerah
- Postingan dengan keyword terkait

**Dari Vendor Media Monitoring (kalau berlangganan):**
- Agregasi data lintas-platform yang sudah pre-processed
- Sentimen analysis result dari vendor untuk benchmark

### 6.3 Catatan untuk Crawler Agent

- **Twitter / X API** berbayar tier minimum US$100/bulan untuk akses scale moderate. Free tier sangat terbatas.
- **Instagram & Facebook Graph API** butuh akses Business / Creator. Untuk monitoring publik, perlu app review approval Meta yang bisa makan waktu 2-4 minggu.
- **TikTok API** masih terbatas — fallback bisa pakai scraping web kalau API tidak cukup.
- **YouTube Data API** punya quota 10,000 unit per hari. Cukup untuk monitoring moderate, tapi perlu quota management.
- **Portal Berita** tidak punya API standar — perlu RSS aggregator atau web scraping per situs. Hati-hati ToS situs.
- **Vendor Media Monitoring** (Awantos, Talkwalker) tier mulai Rp 5-10jt/bulan. Perlu cost approval klien dulu sebelum implement.
- **Untuk POC**, bisa pakai sample data atau monitoring manual scope kecil sambil approval API tier dan vendor diurus.
- **Hati-hati PII**: postingan publik bisa jadi mention nama orang. Perlu masking atau anonymization untuk display di dashboard internal.

---

## 7. Stack Agent Modul

> Modul ini agent-heavy karena involve multi-stage processing dari ingestion sampai recommendation. Stack agent reasoning **dari kebutuhan modul**, bukan apply pipeline template.

### 7.1 Daftar Agent

| Agent Type | Peran di Modul Ini | Trigger | Output |
|------------|---------------------|---------|--------|
| Data Collection Agent | Scrape data dari 7 platform (Twitter, IG, FB, TikTok, YouTube, news, forum) dan vendor media monitoring kalau ada. Konfigurasi keyword + hashtag per daerah. | Scheduler (per platform punya cadence beda: Twitter real-time, IG/FB/TikTok per jam, forum per 6 jam) + on-demand saat humas request refresh keyword baru | Raw posts dengan metadata author, engagement, timestamp |
| Data Processing Agent | Cleaning text postingan (remove URLs, mentions, normalize slang Indonesia, convert emoji ke text), deduplikasi lintas-platform (sama posting di-share multiple platform), enrichment dengan lokasi geografis kalau ada | Event (post-collection) — sesaat setelah Data Collection produce data | Clean structured posts siap analisis |
| Analysis Agent (sentiment + emotion) | Klasifikasi sentimen 5 kelas + emosi 6 kelas + sarcasm detection per postingan menggunakan model bahasa Indonesia | Event — per postingan yang sudah di-process | Sentiment label + score + emotion label per post |
| Analysis Agent (topic + entity) | Topic clustering dan entity extraction (nama OPD, eksekutif, wilayah) per postingan, sequential setelah sentiment | Event — sequential setelah sentiment analysis selesai | Topic cluster ID + entity list per post |
| Analysis Agent (viral score) | Viral score calculation aggregate lintas-postingan dengan komposisi volume + growth rate + engagement + influencer mentions | Batch (per 15 menit) | Viral score per topik dengan trend metric, ranking top viral |
| Analysis Agent (narrative) | Klasifikasi tipe narasi (apresiasi / kegagalan / konspirasi / korban / ajakan aksi / faktual) per cluster topik viral | Batch — hanya jalan untuk topik dengan viral score > threshold trending (0.50+) | Narrative type label + prevalensi per cluster |
| Validation/Guardrail Agent | Validate output Analysis (terutama sentiment + viral score) sebelum jadi basis recommendation. Cek hallucination, format validation, konsistensi cross-Analysis. | Post-process — sandwich antara Analysis dan Planning | Verified output atau flag untuk manual review humas |
| Planning Agent | Generate strategi komunikasi berbasis insight ter-validate (sentiment trend, viral issue, narrative type). Output action plan dengan priority, channel, key messages, timeline. | Event-driven (saat viral score breach threshold MEDIUM/HIGH atau ada misinformation flag) | Action plan rekomendasi komunikasi |
| Knowledge Retrieval Agent | RAG ke knowledge base regulasi resmi pemerintah daerah untuk fact-check klaim viral (counter misinformation) | On-demand — dipanggil saat ada klaim spesifik di viral issue yang butuh cross-check | Relevant regulation excerpts + fact-check verdict |
| Task Automation Agent | Trigger alert ketika sentiment drop, viral score breach, atau crisis potential terdeteksi. Update status isu di tracking system. | Event-driven (saat threshold breach validated) | Action result, downstream trigger ke Notification Agent |
| Notification Agent | Kirim alert ke humas (sentiment drop), sekda (viral medium), kepala daerah + crisis team (viral high / crisis potential) via WhatsApp + email + push notification mobile | Event-driven — dipanggil oleh Task Automation dengan severity dan recipient list | Notification log dengan delivery status |
| Orchestrator Agent | Coordinate multi-agent saat crisis flow severity HIGH: parallel execution Planning + Validation + Notification + status update di Workflow/State (kalau ada eskalasi ke crisis tracking) | System-level — saat severity HIGH detected | Routing decision + execution state lintas-agent |

### 7.2 Alur Eksekusi Pipeline Agent

```
[Scheduler trigger per platform atau humas request refresh]
  ↓
Data Collection Agent (parallel per platform)
  ↓ (post-collection event)
Data Processing Agent (cleaning + dedupe + enrichment)
  ↓ (clean data event)
Analysis Agent — sentiment + emotion (per post)
  ↓ (sequential)
Analysis Agent — topic clustering + entity extraction (per post)
  ↓ (batch trigger per 15 menit, aggregate cross-post)
Analysis Agent — viral score calculation
  ↓
  ├─ Viral score < 0.25 → store ke warehouse, end pipeline
  └─ Viral score >= 0.25 → continue
       ↓
       Analysis Agent — narrative classification (hanya untuk trending+)
       ↓ (insight ready event)
       Validation/Guardrail Agent (post-process — cek konsistensi, hallucination)
       ↓
       ├─ Severity LOW (skor 0.25-0.50) → Reporting update dashboard saja, end
       │
       ├─ Severity MEDIUM (skor 0.50-0.75)
       │    ↓
       │    Knowledge Retrieval (kalau ada klaim spesifik untuk fact-check)
       │    ↓
       │    Planning Agent → generate recommendation
       │    ↓
       │    Validation post-process → cek output Planning
       │    ↓
       │    Task Automation → trigger Notification (humas + sekda)
       │
       └─ Severity HIGH (skor 0.75+)
            ↓
            Orchestrator Agent (System-level coordinate)
            ├─ Parallel: Knowledge Retrieval + Planning + Validation
            ├─ Task Automation → trigger multi-channel Notification
            │   (humas + sekda + crisis team via WhatsApp + email + SMS)
            └─ Workflow/State activate crisis tracking mode
```

### 7.3 Catatan Pattern Adaptive

- **HUMINT input dari humas**: kalau humas tahu ada isu yang belum ke-detect sistem (cth: rumor offline yang belum viral online), humas trigger Interactive Agent → Interactive trigger Data Collection mid-flow untuk fokus scrape topik spesifik dengan keyword baru
- **Mid-flow reverse trigger**: Analysis Agent yang detect klaim spesifik di postingan boleh trigger Knowledge Retrieval mid-flow untuk fact-check sebelum lanjut ke viral score calculation
- **Adaptive frequency Data Collection**: kalau ada isu trending, Data Collection auto-tingkatkan frekuensi scrape platform terkait (dari per jam jadi per 15 menit) selama isu masih aktif
- **Conditional narrative classification**: Analysis Narrative tidak jalan untuk semua post — hanya untuk topik yang sudah trending (skor 0.50+). Counter overload computation untuk noise rendah viral score.

### 7.4 Agent Shared dengan Modul Lain

- **Notification Agent** — shared dengan Modul `02_MANAJEMEN_PENGADUAN`, `06_PROGRAM_KONTROL_FISKAL`, `08_EARLY_WARNING_RISIKO`. Konfigurasi recipient list dan template message di-manage terpusat.
- **Validation/Guardrail Agent** — shared pattern dengan Modul `06_PROGRAM_KONTROL_FISKAL` dan `08_EARLY_WARNING_RISIKO` (modul yang produce output ke decision-maker)
- **Orchestrator Agent** — instance terpisah dari Orchestrator di Modul `01_DASHBOARD_SITUASIONAL` dan `08_EARLY_WARNING_RISIKO`, tapi pattern koordinasi konsisten
- **Knowledge Retrieval Agent** — shared knowledge base dengan Modul `05_KEBIJAKAN_TATA_KELOLA` (yang kelola dokumen regulasi resmi)

---

## 8. Konfigurasi Alert

### 8.1 Threshold

| Kondisi | Threshold | Aksi |
|---------|-----------|------|
| Sentimen overall normal | Skor net sentimen >= 0.5 | Tampilkan hijau di dashboard, tidak ada notif |
| Sentimen drop moderate | Penurunan 10-20% dalam 24 jam | Tampilkan kuning + notif internal di panel notifikasi |
| Sentimen drop tajam | Penurunan > 20% dalam 24 jam | Tampilkan merah + push notif ke humas |
| Viral score emerging | 0.25 - 0.50 | Tampilkan di daftar viral dengan warna hijau muda |
| Viral score trending | 0.50 - 0.75 | Tampilkan kuning + push notif ke humas + sekda |
| Viral score highly viral | > 0.75 | Tampilkan merah + push notif ke humas + sekda + crisis team via multi-channel |
| Crisis potential composite | Composite score > 0.80 (combine sentiment + viral + negative emotion) | Tampilkan merah dengan blink + multi-channel alert + auto-trigger crisis flow |
| Misinformation flag | Klaim cross-check tidak match KB resmi | Tampilkan merah dengan flag misinformation + auto-generate template fact-check |

### 8.2 Severity Levels

| Level | Warna | Tampilan di UI | Notifikasi |
|-------|-------|---------------|------------|
| Hijau / Normal | Hijau | Tampil normal di dashboard tanpa highlight | Tidak ada |
| Kuning / Perlu Perhatian | Kuning | Ditandai dengan badge peringatan di kartu/baris terkait | Notif internal di panel notifikasi humas |
| Merah / Kritis | Merah | Ditampilkan paling atas dashboard dengan kartu khusus, blink animasi | Push notif mobile + memicu alert ke modul Notifikasi (multi-channel) |
| Critical (Crisis) | Merah dengan ikon krisis | Pin di atas + alert modal otomatis muncul saat user buka dashboard | Multi-channel: WhatsApp + email + SMS + push notif mobile ke humas + sekda + kepala daerah + crisis team |

---

## 9. Standar Layanan yang Diharapkan

### 9.1 Kecepatan Tampil Data

| Aspek | Standar Diharapkan |
|-------|---------------------|
| Tampil halaman pertama dashboard | Cepat |
| Pembaruan kartu ringkasan | Cepat |
| Respons interaksi (filter, klik baris, drill-down) | Cepat |
| Render peta dengan layer aktif | Sedang (peta wajar lebih lambat) |
| Generate recommendation oleh Planning Agent | Sedang (butuh inference LLM) |

### 9.2 Frekuensi Pembaruan Data

| Jenis Data | Frekuensi |
|-----------|-----------|
| Postingan dari Twitter / X | Real-time |
| Postingan dari Instagram, Facebook, TikTok, YouTube | Per jam |
| Artikel dari portal berita | Per jam |
| Postingan dari forum publik | Per 6 jam |
| Sentimen analysis per postingan | Real-time (event-driven setelah ingest) |
| Viral score calculation | Per 15 menit (batch aggregate) |
| Narrative classification | Per 15 menit (untuk topik trending+) |
| Dashboard render | Real-time refresh otomatis |

### 9.3 Ketersediaan Layanan

| Aspek | Standar Diharapkan |
|-------|---------------------|
| Jam operasional | 24-7 |
| Toleransi downtime | Rendah |
| Konteks bisnis | Krisis reputasi tidak mengenal jam kerja — viral issue bisa muncul tengah malam dan butuh respons cepat. Sistem harus siap 24-7 dengan crisis team standby. Maintenance scheduled di jam dini hari (02:00-04:00) dengan notif eskalasi ke humas. |

---

## 10. Use Case Scenarios

### 10.1 Skenario Monitoring Harian Humas

**Aktor**: Tim Humas
**Goal**: Memahami kondisi persepsi publik untuk briefing pagi dan persiapan respons

```
1. Pukul 08:00, Tim Humas buka Dashboard Persepsi.
2. Sistem tampilkan skor persepsi 65/100 (kuning) dengan trend turun 8% dari kemarin.
3. Tim Humas skim Top 5 Viral Issues — lihat "Kenaikan Tarif Parkir" dengan skor 0.89 (highly viral).
4. Tim Humas klik baris isu → modal detail tampil dengan timeline mention, sample posts negatif, dan top 5 influencer.
5. Tim Humas klik "Generate Recommendation" → Planning Agent generate template press release dengan key messages.
6. Tim Humas review template, klik "Approve & Draft Content" → masuk editor konten dengan template pre-filled.
7. Tim Humas finalisasi konten, submit ke approval workflow ke Kabag Humas.
8. Setelah approve, konten di-publish ke website + Twitter + Instagram resmi.
9. Sistem tetap monitoring isu untuk track impact respons.
```

### 10.2 Skenario Edge Case — Krisis Tengah Malam

**Aktor**: Sekretaris Daerah + Tim Crisis Response
**Goal**: Respons cepat krisis reputasi yang muncul di luar jam kerja

```
1. Pukul 23:30, viral issue "Dugaan korupsi proyek X" naik dari 0.45 ke 0.82 dalam 2 jam (via Twitter dan TikTok).
2. Sistem detect breach threshold HIGH + composite crisis score > 0.80.
3. Validation Agent verify severity scoring → confirmed crisis.
4. Orchestrator coordinate parallel: Planning generate strategy + Knowledge Retrieval cross-check klaim + Task Automation trigger multi-channel Notification.
5. WhatsApp + email + SMS dikirim ke Sekda + Humas + Kepala Daerah + Crisis Team (8 orang).
6. Sekda buka aplikasi RIS dari notif → langsung masuk modal alert di Dashboard Persepsi.
7. Modal alert tampilkan: detail isu (5,200 mentions dalam 6 jam, top influencer dengan 50K followers), key claim, fact-check status (sebagian klaim tidak match data resmi), recommended action plan (joint statement + press conference besok pagi).
8. Sekda klik "Eskalasi ke Tim Krisis" → broadcast WhatsApp dengan instruksi koordinasi.
9. Sekda klik "Lihat Detail" → masuk Modal Detail Isu untuk siapkan briefing Kepala Daerah.
10. Pukul 06:00 pagi, joint statement + infografis fact-check siap publish; press conference dijadwalkan jam 09:00.
11. Tindak lanjut tracked di crisis log untuk evaluasi pasca-krisis.
```

### 10.3 Skenario Edge Case — Misinformation Terdeteksi

**Aktor**: Tim Humas
**Goal**: Counter misinformation viral dengan fact-check otomatis

```
1. Sistem detect viral issue dengan klaim spesifik: "Pemerintah daerah naikkan tarif PBB 50% tahun depan".
2. Knowledge Retrieval Agent cross-check klaim ke KB regulasi resmi (Pergub PBB terbaru).
3. Hasil cross-check: klaim tidak match — kenaikan resmi cuma 5%, tidak 50%.
4. Sistem flag postingan sebagai misinformation, status "fact-check needed".
5. Auto-generate template fact-check: claim original + data resmi dengan referensi Pergub + saran format infografis.
6. Tim Humas terima notif "Misinformation flag aktivasi".
7. Tim Humas buka template, review accuracy fact-check.
8. Tim Humas approve → publish infografis fact-check ke media sosial dengan tag "Klarifikasi Resmi".
9. Sistem track engagement rebuttal untuk evaluasi efektivitas counter-narrative.
```

---

## 11. Referensi Implementasi

### 11.1 Talkwalker

**URL**: https://www.talkwalker.com

**Fitur yang Diadaptasi**:
- AI-powered sentiment analysis lintas platform
- Crisis detection alerts dengan severity tiering
- Influencer identification dan engagement tracking

### 11.2 Hootsuite Insights

**URL**: https://hootsuite.com

**Fitur yang Diadaptasi**:
- Multi-platform monitoring dashboard terintegrasi
- Custom dashboard builder per role
- Scheduled reporting untuk briefing eksekutif

### 11.3 IBM Watson Natural Language Understanding

**URL**: https://www.ibm.com/cloud/watson-natural-language-understanding

**Fitur yang Diadaptasi**:
- Sentiment + emotion analysis untuk teks bahasa Indonesia
- Topic extraction dan entity recognition
- Multi-language support dengan fokus bahasa Indonesia

---

*Dokumen ini merupakan bagian dari Dokumentasi Brief Sistem Intelijen Regional (RIS)*
*Modul: Persepsi Publik & Komunikasi Strategis | Versi: 1.0.0*
