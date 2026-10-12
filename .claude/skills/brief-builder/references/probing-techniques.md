# Propose-First Patterns — Usage Storyline & Feature Priority

Dua parameter Tier 1 ini paling rawan menjadi pertanyaan-pertanyaan panjang yang menyiksa user. **Aturan utama: jangan pernah tanya kosong.** Selalu propose dulu berdasarkan konteks yang sudah ada, baru minta validasi atau koreksi.

File ini berisi proposal templates dan validation patterns untuk kedua parameter — bukan daftar pertanyaan terbuka.

---

## Untuk menyusun Usage Storyline

### Aturan inti

User non-teknis tidak bisa menjawab "ceritakan keseharian decision authority menggunakan dashboard" — itu bukan bahasa mereka. **Anda yang membayangkan storyline-nya**, lalu sodorkan ke user untuk dikoreksi.

Modal Anda menyusun storyline tanpa input lengkap:
- Profil decision authority (jabatan + level)
- Domain isu (apa yang dimonitor / dianalisis)
- Sektor dan pola operasional khas instansi tersebut
- Cadence keputusan (harian / mingguan / situasional)

Dengan empat hal itu, Anda **sudah cukup untuk propose 1 primary flow** yang masuk akal. User akan koreksi langkah-langkah yang tidak match dengan kenyataan operasional klien — itu jauh lebih cepat daripada user harus mengarang flow dari kosong.

### Template proposal storyline

```
"Storyline pemakaian harian yang saya bayangkan:

[Aktor] biasanya [trigger waktu/situasi]:
1. [Action 1]
2. [Action 2]
3. [Action 3]
4. [Action 4]
→ [Outcome]

Yang ingin saya konfirmasi: **[1 hal paling tidak pasti dari proposal ini]?**"
```

### Contoh konkret 1 — Konteks: Dinas Perdagangan, monitoring harga

```
"Storyline pemakaian harian yang saya bayangkan:

Kabid Distribusi setiap pagi sebelum rapat staf:
1. Buka dashboard, lihat status komoditas hari ini (hijau/kuning/merah)
2. Klik komoditas merah, lihat breakdown per kabupaten
3. Drill-down ke pasar yang anomali, validasi pola
4. Tag tim pengawas pasar untuk verifikasi lapangan
→ Tim deploy ke lapangan jam 9, ada konteks data untuk briefing rapat

Yang ingin saya konfirmasi: **rutinitasnya memang pagi, atau Kabid biasanya cek
sore hari sebelum tutup kantor?**"
```

### Contoh konkret 2 — Konteks: Pemkot, monitoring kemacetan

```
"Storyline yang saya bayangkan:

Operator ATCS di shift pagi:
1. Pantau live feed CCTV 5 ruas kritis
2. Saat detect kemacetan abnormal, klik untuk lihat root cause (kecelakaan/event/pola)
3. Trigger intervensi: ubah timing lampu, deploy petugas, atau update info ke aplikasi publik
4. Catat di intervention log untuk audit
→ Kemacetan terurai 15-30 menit, data tercatat untuk evaluasi mingguan

Yang ingin saya konfirmasi: **operator memang punya wewenang ubah timing lampu
sendiri, atau harus eskalasi ke Kabid Lalu Lintas dulu?**"
```

### Contoh konkret 3 — Konteks: Sistem Intelijen Regional pemkot

```
"Storyline yang saya bayangkan untuk Dashboard Situasional:

Kepala Daerah setiap pagi pukul 7 di kantor:
1. Buka dashboard di tablet, lihat Indeks Kondisi Daerah + EWS status
2. Skim Top 5 Isu Viral untuk konteks media briefing
3. Klik OPD ranking terendah, lihat detail kinerja
4. Buat catatan untuk rapat koordinasi pukul 9
→ Rapat koordinasi punya konteks data terkini, instruksi konkret ke OPD

Yang ingin saya konfirmasi: **Kepala Daerah memang user harian, atau yang akses
daily sebenarnya Sekda yang prep brief untuk Kepala Daerah?**"
```

### Cara user mengoreksi (dan bagaimana Anda merespon)

User koreksi ringan ("sebenarnya Kabid bukan operator harian, dia review mingguan"):
→ **Update storyline, propose versi baru** dengan satu kalimat ringkas: *"OK, jadi yang harian sebenarnya staf di Kabid. Storyline jadi: staf [...]. Apakah primary flow seperti ini?"*

User kasih satu detail tambahan ("ada langkah verifikasi dengan Bulog sebelum deploy"):
→ **Sisipkan, lanjut**: *"Saya tambahkan langkah 3.5 — verifikasi dengan Bulog. Lanjut ke MoSCoW?"*

User bilang "nggak tau, terserah Anda":
→ **Catat sebagai asumsi, lanjut**: *"OK, saya pakai versi proposal di atas dan tandai sebagai asumsi yang perlu validasi langsung dengan klien sebelum implementation."* Catat di Blind Spot Review.

### Empat unsur wajib yang harus terisi (validated atau assumed)

Storyline lengkap mengandung:

1. **Aktor** — jabatan (bukan nama orang)
2. **Trigger** — situasi/waktu yang mengaktifkan
3. **Actions** — minimal 3-5 langkah konkret
4. **Outcome** — keputusan atau output yang muncul

Kalau salah satu kosong setelah validasi, isi dengan asumsi default berdasarkan sektor + tandai. Jangan loop tanya.

### Red flags storyline yang Anda harus tangkap

Setelah user setuju proposal Anda, jalankan internal check sebelum lanjut:

- Aktor masih "user/tim" tanpa jabatan → ganti ke jabatan paling masuk akal sebelum lanjut
- Trigger hanya "setiap hari" → tambahkan konteks situasi (sebelum rapat / saat alert / pagi pukul X)
- Action lompat dari "buka dashboard" ke "ambil keputusan" tanpa langkah perantara → tambahkan 1-2 langkah penghubung sebagai asumsi
- Outcome abstrak ("data-driven decision") → ganti ke tindakan konkret

Lakukan diam-diam. Jangan tanya user untuk perbaiki red flags ini — Anda yang perbaiki, user yang validate.

---

## Untuk menyusun Feature Priority (MoSCoW)

### Aturan inti

User tidak bisa kasih MoSCoW dari kosong. Mereka belum tentu tahu fitur apa saja yang feasible. **Anda yang propose pemetaan awal berdasarkan storyline + objective + feature decomposition yang sudah disepakati**, user re-prioritize.

Modal Anda menyusun MoSCoW:
- Storyline yang sudah ter-validate (ini sumber utama Must-have)
- Objective yang sudah disepakati
- Feature decomposition (jadi MoSCoW ini level sub-fitur di dalam masing-masing brief)

### Template proposal MoSCoW

```
"Berdasarkan storyline dan objective tadi, ini pemetaan awal MoSCoW saya:

**Must-have** (MVP wajib):
- [Fitur A] — dibutuhkan di langkah X storyline
- [Fitur B] — tanpa ini, objective Y tidak tercapai
- [Fitur C] — ...

**Should-have** (penting tapi bisa rilis tanpa ini):
- [Fitur D]
- [Fitur E]

**Could-have** (nilai tambah):
- [Fitur F]

**Won't-have v1** (sengaja keluar, kandidat versi berikutnya):
- [Fitur G]

Yang ingin saya konfirmasi: **dari list Must-have ini, ada yang menurut Anda
sebenarnya bisa di-defer ke Should atau sebaliknya?**"
```

### Contoh konkret — Konteks: monitoring harga komoditas

```
"Pemetaan awal MoSCoW saya:

**Must-have:**
- Anomaly alert harga real-time — storyline pagi pukul 7 tidak jalan tanpa ini
- Drill-down per kabupaten dengan trend 14 hari — langkah 2-3 storyline
- Intervention log dengan task assignment — langkah 4 storyline + audit trail
- Standardized data input form 27 pengawas — tanpa ini data tidak masuk konsisten

**Should-have:**
- Mission Simulation 3 opsi intervensi — bernilai tinggi, tapi MVP bisa rilis tanpa
- Heatmap regional — enhancement, bisa diganti tabel

**Could-have:**
- Prediksi tren 7 hari ke depan
- Push notif ke WhatsApp eksekutif

**Won't-have v1:**
- Benchmarking antar provinsi (scope berbeda)
- Forecasting jangka panjang 1 tahun+

Yang ingin saya konfirmasi: **Mission Simulation di Should-have, atau klien
melihatnya sebagai dealbreaker?**"
```

### Cara user re-prioritize (dan bagaimana Anda merespon)

User re-prioritize 1-2 item ("Mission Simulation harus Must-have, klien bilang itu dealbreaker"):
→ **Update, validasi coherence singkat**: *"OK, naik ke Must-have. Berarti scope Fase 5 untuk fitur ini lebih besar. Lanjut?"*

User minta tambahkan fitur yang belum ada di list:
→ **Tanya prioritas spesifik fitur baru itu**: *"Fitur [X] masuk Must atau Should menurut Anda?"* — satu kalimat, satu pertanyaan.

User bilang "semua Must-have penting":
→ **Push back via test pertanyaan**, satu kalimat: *"Kalau anggaran dipotong dan harus pilih 3 dari 5 untuk MVP, mana yang Anda pertahankan?"* — biarkan user pikirkan trade-off, bukan Anda yang tantang konseptual.

### Coherence check — wajib jalankan internal

Sebelum lanjut ke Fase 4 (Feature Decomposition), validate dalam internal reasoning:

1. Setiap Must-have → terhubung ke langkah storyline mana? Untuk objective mana?
2. Storyline → ada langkah penting yang tidak punya Must-have pendukung?
3. Komponen sistem level tinggi (web app, mobile, layer integrasi) → semua menjustifikasi minimal 1 Must-have?

Kalau ada misalignment, **propose koreksi** ke user dalam 1-2 kalimat. Jangan tanya kosong.

Contoh: *"Saya cek koherensi — fitur X di Must-have tidak muncul di storyline. Saya turunkan ke Should-have, atau Anda mau saya tambah langkah di storyline yang melibatkan fitur X?"*

### Red flags MoSCoW yang Anda harus tangkap

- Lebih dari 70% fitur masuk Must-have → user belum trade-off real, push back via 1 pertanyaan trade-off
- Must-have tidak punya kaitan storyline → demote diam-diam, sebut singkat saat update
- Won't-have v1 kosong → propose 1-2 fitur untuk masuk ke sana berdasarkan scope

---

## Penggunaan kedua teknik dalam alur Discovery

**Urutan ideal:**
1. Konteks dasar via Opening (1 pertanyaan)
2. Propose-validate parameter dasar: sektor, decision authority, domain isu, objective (3-4 turn)
3. Propose Storyline lengkap → user koreksi
4. Propose komponen sistem level tinggi (deskriptif: web app, mobile, layer integrasi — BUKAN tech stack spesifik)
5. Propose MoSCoW berdasarkan storyline + objective → user re-prioritize
6. Synthesis (Fase 3) → Feature Decomposition (Fase 4) → Deep-Dive Loop (Fase 5) → Blind Spot Review → Output

Total: ~6-8 turn untuk discovery + synthesis. Plus N+1 turn untuk Deep-Dive Loop. Kalau lebih dari 12 turn dan belum sampai Feature Decomposition, Anda kemungkinan terlalu banyak bertanya — re-evaluate, mulai propose lebih agresif.

**Storyline dulu, MoSCoW kemudian.** Storyline adalah grounding untuk validasi MoSCoW via coherence rule. Tidak boleh propose MoSCoW sebelum storyline ter-validate.
