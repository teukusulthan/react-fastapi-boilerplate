# Feature Decomposition — Heuristik & Naming

Fase 4 menentukan struktur output: berapa file `NN_*.md` yang dihasilkan, apa namanya, dan apa yang masuk ke masing-masing. Ini fase yang paling menentukan kualitas dan kelengkapan brief — keputusan di sini menentukan apa yang di-deep-dive di Fase 5.

**Aturan utama: jangan tanya kosong "menurut Anda dipecah jadi berapa fitur?".** Anda yang propose pemecahan berdasarkan storyline, modul fungsional, dan pola domain. User koreksi.

---

## Kapan satu komponen layak jadi `NN_*.md` tersendiri

Pakai **tes tiga sinyal**. Komponen layak jadi brief tersendiri kalau memenuhi minimal **2 dari 3** sinyal berikut:

### Sinyal 1: Punya data atau entity bisnis sendiri

Komponen mengelola entity bisnis utama yang tidak di-share dengan komponen lain. Contoh:
- ✅ "Manajemen Pengaduan" mengelola entity Aduan, Kategori Aduan, Status Aduan, Riwayat Penanganan → entity bisnis sendiri
- ✅ "Persepsi Publik" mengelola entity Posting Media Sosial, Skor Sentimen, Topik Pembahasan → entity bisnis sendiri
- ❌ "Filter Tanggal" tidak mengelola entity sendiri — ini fitur lintas-modul, bukan brief tersendiri

### Sinyal 2: Punya user flow utama tersendiri

Komponen punya storyline lengkap (aktor + trigger + actions + outcome) yang berbeda dari komponen lain. Contoh:
- ✅ "Dashboard Situasional" — Kepala Daerah pagi hari → buka → lihat → drill-down → keputusan
- ✅ "Early Warning & Risiko" — Sistem trigger alert → notifikasi → respons krisis → eskalasi
- ❌ "Login" — flow generic, bukan core to brief — masuk sebagai 1 paragraf di overview

### Sinyal 3: Punya team execution / OPD ownership tersendiri

Komponen di-handle oleh tim/OPD/role yang berbeda di sisi klien. Contoh:
- ✅ "Manajemen Pengaduan" — di-handle oleh Bagian Hubungan Masyarakat + 25 OPD
- ✅ "Program & Kontrol Fiskal" — di-handle oleh BPKAD + Bappeda
- ❌ "Notifikasi Push" — fitur lintas-modul, bukan team-owned

### Contoh keputusan

| Komponen | Sinyal 1 | Sinyal 2 | Sinyal 3 | Keputusan |
|---|---|---|---|---|
| Dashboard Situasional | ✅ | ✅ | ✅ | Brief tersendiri (`01_DASHBOARD_SITUASIONAL.md`) |
| Manajemen Pengaduan | ✅ | ✅ | ✅ | Brief tersendiri (`02_MANAJEMEN_PENGADUAN.md`) |
| Login & Authentication | ❌ | ❌ | ❌ | Section di OVERVIEW (Standar Keamanan) |
| Filter & Search | ❌ | ❌ | ❌ | Sub-section di setiap fitur yang relevan |
| Audit Trail | ✅ | ❌ | ✅ | Borderline — tanya user, default ke section di OVERVIEW |
| Notifikasi & Alert | ✅ | ✅ | ❌ | Borderline — kalau central, jadi brief; kalau distributed, jadi section per fitur |

---

## Naming convention

**Format file:** `NN_NAMA_FITUR.md`

**Aturan:**

1. **Prefix `NN_`** — zero-padded 2 digit
   - `00_OVERVIEW.md` — selalu file pertama, mandatory
   - `01_`, `02_`, ... `99_` — feature briefs urut prioritas
   - Urutan = urutan logis (fitur fondasional dulu, fitur dependent kemudian) atau urutan prioritas implementasi

2. **`NAMA_FITUR`** — `ALL_CAPS_SNAKE_CASE`
   - Bahasa Indonesia (kecuali istilah teknis Inggris yang lazim)
   - Maksimal 4 kata, idealnya 2-3 kata
   - Spesifik domain, bukan generic

**Contoh nama yang baik:**
- `01_DASHBOARD_SITUASIONAL.md`
- `02_MANAJEMEN_PENGADUAN.md`
- `03_PERSEPSI_PUBLIK.md`
- `06_PROGRAM_KONTROL_FISKAL.md`
- `08_EARLY_WARNING_RISIKO.md`

**Contoh nama yang harus ditolak:**

| Nama | Masalah | Ganti dengan |
|---|---|---|
| `01_dashboard.md` | Lowercase, tidak spesifik | `01_DASHBOARD_SITUASIONAL.md` |
| `01_FITUR_1.md` | Tidak deskriptif | `01_NAMA_DOMAIN.md` |
| `01_DASHBOARD_FOR_KEPALA_DAERAH_AND_SEKRETARIS_DAERAH.md` | Terlalu panjang | `01_DASHBOARD_EKSEKUTIF.md` |
| `01_LOGIN.md` | Bukan core feature | (masuk OVERVIEW) |
| `1_DASHBOARD.md` | Tidak zero-padded | `01_DASHBOARD_SITUASIONAL.md` |

---

## Pola pemecahan per tipe aplikasi

**Aplikasi monitoring & dashboard pemerintah daerah (referensi: RIS):**

```
00_OVERVIEW.md
01_DASHBOARD_SITUASIONAL          ← hub sentral, real-time
02_MANAJEMEN_PENGADUAN            ← pengelolaan aduan masyarakat
03_PERSEPSI_PUBLIK                ← analisis sentimen + komunikasi
04_KUALITAS_PELAYANAN             ← monitoring layanan publik
05_KEBIJAKAN_TATA_KELOLA          ← keselarasan kebijakan
06_PROGRAM_KONTROL_FISKAL         ← tracking anggaran + program
07_INTELIJEN_EKONOMI              ← analisis potensi ekonomi
08_EARLY_WARNING_RISIKO           ← deteksi dini + crisis response
```

**Aplikasi e-commerce / marketplace:**

```
00_OVERVIEW.md
01_KATALOG_PRODUK
02_KERANJANG_CHECKOUT
03_PEMBAYARAN_TRANSAKSI
04_MANAJEMEN_PESANAN
05_DASHBOARD_PENJUAL
06_REVIEW_RATING
07_PROMOSI_VOUCHER
```

**Aplikasi healthcare / klinik:**

```
00_OVERVIEW.md
01_REGISTRASI_PASIEN
02_REKAM_MEDIS_ELEKTRONIK
03_JADWAL_KONSULTASI
04_RESEP_FARMASI
05_BILLING_KLAIM_BPJS
06_DASHBOARD_DOKTER
```

**Aplikasi internal CRM / sales:**

```
00_OVERVIEW.md
01_MANAJEMEN_LEAD
02_PIPELINE_SALES
03_PROFIL_KLIEN
04_DASHBOARD_PERFORMANCE
05_FORECASTING_REVENUE
```

Pola di atas adalah **starting point**, bukan template wajib. Sesuaikan dengan domain klien aktual.

---

## Template proposal Fase 4

```
"Berdasarkan storyline dan tujuan tadi, saya usulkan pecah aplikasi ini menjadi
N fitur — masing-masing jadi satu brief terpisah:

- **00_OVERVIEW.md** — gambaran umum sistem, arsitektur, daftar fitur
- **01_[NAMA_FITUR_1].md** — [1-line deskripsi]; [alasan kenapa layak jadi brief tersendiri: entity bisnis sendiri / user flow utama / team ownership]
- **02_[NAMA_FITUR_2].md** — [...]
- ...
- **NN_[NAMA_FITUR_N].md** — [...]

N fitur cukup, atau ada yang perlu dipecah lebih / digabung?"
```

**Contoh konkret — Konteks: Sistem Intelijen Regional pemkot:**

```
"Berdasarkan storyline tadi, saya usulkan pecah jadi 8 fitur utama —
masing-masing satu brief terpisah:

- **00_OVERVIEW.md** — visi, arsitektur, integrasi antar modul, blind spot
- **01_DASHBOARD_SITUASIONAL.md** — hub sentral untuk Kepala Daerah, real-time
- **02_MANAJEMEN_PENGADUAN.md** — pengelolaan LAPOR! + sumber lain, integrasi 25 OPD
- **03_PERSEPSI_PUBLIK.md** — analisis sentimen media sosial + komunikasi strategis
- **04_KUALITAS_PELAYANAN.md** — monitoring IKM dan kinerja OPD
- **05_KEBIJAKAN_TATA_KELOLA.md** — keselarasan RPJMD dengan implementasi
- **06_PROGRAM_KONTROL_FISKAL.md** — tracking realisasi APBD + program prioritas
- **07_INTELIJEN_EKONOMI.md** — analisis PDRB, potensi investasi
- **08_EARLY_WARNING_RISIKO.md** — deteksi dini krisis sosial/ekonomi/keamanan

8 fitur cukup, atau ada yang perlu dipecah lebih / digabung?"
```

---

## Cara user mengoreksi (dan bagaimana Anda merespon)

**User setuju ("8 cukup, lanjut"):**
→ Catat struktur final, pindah ke Fase 5 (Deep-Dive Loop).

**User tambah fitur ("tambah satu untuk integrasi WhatsApp"):**
→ Propose nama dan posisi: *"OK, saya tambah `09_INTEGRASI_WHATSAPP.md` di akhir. Atau Anda mau di-insert di tengah misal antara 02 dan 03?"* — Satu kalimat, satu pertanyaan.

**User kurangi fitur ("Intelijen Ekonomi nggak usah dulu"):**
→ Hapus dan re-number: *"OK, hapus 07. Sisa 7 fitur, nomor di-shift jadi 01-07. Lanjut?"*

**User ganti nama ("ganti DASHBOARD_SITUASIONAL jadi DASHBOARD_KOMANDO"):**
→ Update tanpa banyak tanya: *"OK, ganti ke `01_DASHBOARD_KOMANDO.md`. Lanjut?"*

**User restructure ("gabung 5 dan 6"):**
→ Propose nama gabungan: *"OK, saya gabung jadi `05_KEBIJAKAN_DAN_FISKAL.md`. Sisanya re-number jadi 06, 07. OK?"*

**User bilang "terserah Anda":**
→ Ambil proposal apa adanya, catat sebagai asumsi: *"OK, saya pakai 8 fitur seperti proposal di atas dan tandai sebagai struktur asumsi yang perlu re-validate dengan klien sebelum implementation."*

**User minta >10 fitur:**
→ Push back ringan, satu kalimat: *"10+ fitur jadi sesi panjang dan eksekusi v1 berisiko. Mau saya gabung beberapa fitur kecil dulu, atau Anda terima sesi panjang dengan banyak file?"*

---

## Internal coherence check sebelum lanjut ke Fase 5

Sebelum mulai Deep-Dive Loop, validate dalam internal reasoning:

1. **Apakah setiap fitur punya minimal 1 use case di storyline?** Kalau ada fitur tanpa use case, salah satu dari dua: storyline kurang, atau fitur tidak relevan → angkat ke user.
2. **Apakah ada fitur yang overlap entity bisnis atau flow?** Kalau iya, propose merge.
3. **Apakah ada fitur yang seharusnya satu tapi terpecah?** Kalau iya, propose merge.
4. **Apakah jumlah fitur masuk akal untuk timeline klien?** 8 fitur untuk 3 bulan = ambisius. Angkat sebagai catatan di Blind Spot Review, jangan blok progress.

Kalau ada misalignment, **propose koreksi** ke user dalam 1-2 kalimat. Jangan tanya kosong.

---

## Red flags struktur yang harus ditangkap

- Ada fitur dengan deskripsi vague seperti "Reporting" atau "Analytics" → push back: *"Reporting untuk apa spesifik? Aduan? Anggaran? Ini lebih cocok jadi section di fitur induknya."*
- Ada fitur yang sebetulnya sub-fitur dari yang lain → propose demote
- Tidak ada fitur dashboard sentral → unusual, angkat ke user: *"Tidak ada dashboard utama? Atau ini akan masuk salah satu fitur lain?"*
- 1 fitur saja → unusual untuk app klien serius, angkat: *"Hanya 1 fitur — apakah ini benar scope, atau v1 minimal saja?"*
- 15+ fitur → terlalu pecah, propose konsolidasi

---

## Output Fase 4

Catat struktur final ini secara eksplisit di working memory Anda — list dengan urutan dan nama file. Ini akan jadi roadmap untuk Fase 5 Deep-Dive Loop dan referensi cross-link di `00_OVERVIEW.md`.

Format catatan internal (Anda yang track, tidak ditampilkan ke user):

```
FEATURE_DECOMPOSITION_FINAL:
- 00_OVERVIEW.md
- 01_DASHBOARD_SITUASIONAL.md
- 02_MANAJEMEN_PENGADUAN.md
- ...
- 08_EARLY_WARNING_RISIKO.md

TOTAL: 1 overview + 8 feature briefs = 9 files
```

Setelah ini terkunci, lanjut Fase 5.
