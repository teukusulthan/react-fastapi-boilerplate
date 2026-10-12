# Agent Catalog — Vocabulary Reference

File ini adalah **vocabulary reference** untuk 18 kategori agent canonical yang dipakai brief-builder saat propose Section "Stack Agent Modul" di feature brief atau Section "Konsolidasi Stack Agent" di OVERVIEW.

## Cara pakai file ini

- **Saat reasoning agent stack untuk modul tertentu**, baca file ini untuk paham agent mana yang cocok untuk konteks modul.
- File ini **vocabulary**, bukan pipeline blueprint. Tidak ada urutan canonical, tidak ada pattern combo "shortcut".
- Untuk **rules antar-agent dan kapan agent wajib/skip**, baca `agent-rules.md` setelah baca file ini.

## Prinsip pemakaian agent

**Adaptive, bukan rigid.** Setiap agent bisa dipanggil di mana saja di flow tergantung kebutuhan project. Tidak ada agent "first" atau agent "last" yang fixed. Misal: Data Collection bisa muncul di mid-flow kalau Analysis Agent menemukan data gap dan butuh refresh.

**Vocabulary trigger canonical.** Trigger di brief harus pakai label dari list ini: `Scheduler / event`, `Event (post-collection)`, `Event / batch`, `Event-driven`, `Manual / event`, `Manual / scheduled`, `User-triggered`, `System-level`, `Continuous`, `On-demand`, `Post-process`, `Pre/Post process`, `Offline / periodic`. Boleh kombinasi (`Scheduler + on-demand`), tapi **jangan invent label baru**.

---

## #1 Data Collection Agent

**Peran utama**: Mengambil data dari sumber eksternal.

**Kapan dipakai**:
- Modul butuh data dari sumber luar yang tidak ada di sistem klien (BPS, BMKG, LAPOR!, media sosial, dll)
- Project butuh refresh data berkala dari sumber yang berubah (harga komoditas, sentimen media sosial, prakiraan cuaca)
- Data eksternal tidak punya push integration ke sistem klien (klien harus pull manual)
- Brief Section "Kebutuhan Data Eksternal" punya isi (kalau section itu skip, agent ini juga biasanya skip)
- Mid-flow refresh: agent lain (Analysis, Reporting) menemukan data gap dan butuh data tambahan untuk lengkapi konteks

**Kapan tidak dipakai**:
- Project punya data HUMINT lengkap dari user (manual input) yang sudah cukup untuk analisis
- Sistem klien sudah punya data internal yang cukup (cth: data aduan dari sistem LAPOR! internal yang sudah masuk ke DB)
- Modul agentic murni yang tidak konsumsi data eksternal (cth: AI Assistant Talk-to-Data ke knowledge base internal)
- Data sudah di-push oleh sumber eksternal via webhook/API push (kasus rare)

**Contoh use case**:
- Scrape data sensus penduduk dari BPS setiap awal bulan
- Crawl postingan Twitter dengan keyword pemerintah daerah secara real-time
- Refresh prakiraan cuaca BMKG per 6 jam
- On-demand pull data SIPD ketika user request laporan terbaru
- Trigger dari Analysis Agent: "data BPS untuk kabupaten X belum lengkap, refresh dari sumber"

**Range trigger yang mungkin**:
- `Scheduler` — pull periodik (harian/jam-an/menit-an tergantung urgency data)
- `Event` — saat agent lain detect data gap mid-flow
- `On-demand` — saat user request refresh data ad-hoc
- `Scheduler + on-demand` — kombinasi paling umum

**Output umum**: Raw atau semi-structured data dari sumber eksternal — biasanya butuh diproses Data Processing Agent dulu sebelum dipakai.

---

## #2 Data Processing Agent

**Peran utama**: Cleaning dan transform data mentah.

**Kapan dipakai**:
- Setelah Data Collection Agent menarik data mentah dari sumber eksternal (hampir selalu sepasang)
- Data dari berbagai sumber butuh dinormalisasi ke format konsisten
- Data mentah punya inconsistency: format tanggal beda, encoding beda, slang/typo, field missing
- Sebelum data masuk ke Analysis Agent — data harus clean dulu, jangan biarkan Analysis ngolah noise

**Kapan tidak dipakai**:
- Data sudah clean dan structured dari sumber (rare — biasanya happens kalau sumber adalah API resmi well-curated)
- Modul tidak punya tahap data preparation (cth: AI Assistant pure user-facing yang tidak ingest data)
- Data Collection skip (kalau data eksternal tidak ada, processing juga tidak ada)

**Contoh use case**:
- Normalisasi format tanggal dari berbagai sumber jadi ISO 8601
- Cleaning text postingan media sosial: remove URLs, normalize slang, convert emoji ke text
- Deduplikasi aduan yang masuk dari multiple kanal (LAPOR! + WhatsApp + email)
- Validasi field wajib di data BPS sebelum disimpan ke warehouse
- Enrichment: tambah lokasi geografis berdasarkan kode kabupaten

**Range trigger yang mungkin**:
- `Event (post-collection)` — paling umum, jalan sesaat setelah Data Collection selesai
- `Event-driven` — saat data baru masuk dari sumber push integration
- `Batch` — process kumpulan data per periode

**Output umum**: Clean structured data — siap dikonsumsi Analysis Agent atau langsung disimpan ke warehouse.

---

## #3 Analysis Agent

**Peran utama**: Menghasilkan insight dari data yang sudah clean dan terstruktur.

**Kapan dipakai**:
- Modul butuh interpret data jadi insight bermakna (sentiment, trend, anomaly, classification, scoring)
- Project butuh trend analysis, anomaly detection, atau classification berbasis data
- Analisis harus data-driven (bukan free-form opini agent) — agent ini grounded di data input
- Data input sudah ter-validate (dari Data Processing atau dari structured source langsung)
- Untuk modul yang feed insight ke Reporting, Notification, atau Planning downstream

**Kapan tidak dipakai**:
- Data belum tersedia atau belum di-process (Analysis tidak boleh ngolah data noise)
- Project hanya butuh format-and-present data yang sudah ada → pakai Reporting Agent
- Modul tidak butuh interpretasi (cth: Notification pure passthrough, Auth utility)
- Analisis cuma sederhana count/aggregate yang bisa dilakukan SQL/dashboard query langsung

**Contoh use case**:
- Klasifikasi sentimen aduan masyarakat (positif/netral/negatif) per platform
- Deteksi anomali transaksi keuangan daerah dibandingkan baseline historis
- Trend topik media sosial 30 hari terakhir + viral score calculation
- Skoring prioritas isu berdasarkan multiple variables (volume, growth, engagement, influencer)
- Klasifikasi narrative type (success story / failure / conspiracy / call to action)

**Range trigger yang mungkin**:
- `Event` — saat data baru masuk dari Data Processing (per-record analysis)
- `Batch` — saat scheduler trigger analisis periodik (aggregate analysis lintas-record)
- `Event / batch` — kombinasi: per-post sentiment + batch viral score
- `On-demand` — saat user request analisis ad-hoc

**Output umum**: Insight terstruktur — metrics, summary, classification labels, anomaly flags, scores.

---

## #4 Planning Agent

**Peran utama**: Membuat rencana atau strategi berbasis konteks dan insight.

**Kapan dipakai**:
- Modul butuh generate strategic plan, mission plan, atau task breakdown
- Project melibatkan recommendation engine yang menghasilkan rencana tindakan (bukan sekadar insight)
- Ada konteks yang cukup untuk planning (insight dari Analysis, knowledge dari Knowledge Retrieval)
- Output butuh structured action plan: priority, steps, channel, timeline, key messages

**Kapan tidak dipakai**:
- Project hanya butuh insight tanpa rencana (Analysis Agent cukup)
- Tidak ada konteks data untuk planning — Planning tanpa data input = halusinasi (sama buruk dengan Analysis tanpa data)
- Modul executional yang tidak generate plan — cuma execute (pakai Task Automation)

**Contoh use case**:
- Generate strategi komunikasi krisis berdasarkan analisis sentimen + viral issue
- Buat task breakdown untuk respons banjir berdasarkan severity + lokasi affected
- Generate action plan rekomendasi kebijakan berdasarkan analisis dampak
- Mission planning untuk tim lapangan berdasarkan early warning trigger

**Range trigger yang mungkin**:
- `Event` — saat Analysis Agent menghasilkan insight kritis yang butuh action plan
- `Manual` — saat eksekutif request planning ad-hoc
- `Manual / event` — kombinasi paling umum

**Output umum**: Structured plan — list of steps, actions, priorities, timelines, channels.

---

## #5 Task Automation Agent

**Peran utama**: Eksekusi aksi otomatis berdasarkan kondisi atau trigger.

**Kapan dipakai**:
- Modul butuh action otomatis ketika kondisi tertentu terpenuhi (threshold breach, event detection)
- Project punya business logic "kalau X terjadi, lakukan Y otomatis"
- Action lebih luas dari sekadar notif — bisa update DB, trigger workflow lain, panggil agent lain, dll
- Sebelum action dijalankan, ada validated trigger (bukan sembarang event)

**Kapan tidak dipakai**:
- Modul cuma butuh notif keluar — pakai Notification Agent saja
- Action butuh judgment manusia (jangan auto-execute keputusan strategis)
- Trigger belum di-validate — risky kalau auto-action di trigger noise

**Contoh use case**:
- Auto-update status aduan jadi "eskalasi" saat detected viral score > threshold
- Auto-trigger notif WhatsApp ke kepala OPD saat aduan kategori X masuk
- Auto-execute backup data trigger setelah scheduled job
- Auto-route aduan ke OPD relevan berdasarkan klasifikasi kategori

**Range trigger yang mungkin**:
- `Event-driven` — paling umum, jalan ketika kondisi terpenuhi

**Output umum**: Action result / status — sukses/gagal eksekusi, log entry, downstream trigger.

---

## #6 Orchestrator Agent

**Peran utama**: Mengatur flow dan koordinasi antar-agent dalam pipeline kompleks.

**Kapan dipakai**:
- Modul punya 3+ agent dengan dependency saling kait
- Pipeline kompleks dengan branching (kondisi A → flow X, kondisi B → flow Y)
- Multi-step workflow yang butuh coordinator (vs satu workflow stateful — pakai #17 Workflow/State)
- Crisis response yang butuh koordinasi multiple agent secara real-time

**Kapan tidak dipakai**:
- Modul cuma punya 1-2 agent linear — overkill, langsung event chain antar agent saja
- Workflow stateful di dalam satu konteks — pakai #17 Workflow/State (Orchestrator atur antar-konteks/antar-agent)
- Trigger user langsung — Orchestrator selalu system-level, bukan user-facing

**Contoh use case**:
- Coordinate Data Collection → Processing → Analysis → Validation → Reporting untuk pipeline harian
- Crisis response coordinator: panggil Analysis untuk severity scoring, Planning untuk strategi, Notification untuk eskalasi
- Pipeline conditional: kalau viral score > threshold, trigger Planning + Notification; kalau tidak, cuma Reporting

**Range trigger yang mungkin**:
- `System-level` — selalu sistem yang trigger, bukan user

**Output umum**: Routing decision / execution state — log dispatching agent, result aggregation.

---

## #7 Interactive Agent

**Peran utama**: Interface interaktif ke user (chat/UI) untuk query, navigasi, dan konfirmasi.

**Kapan dipakai**:
- Modul punya AI Assistant Talk-to-Data interface
- Project butuh HUMINT confirmation gate sebelum jalankan flow agent (validasi objective dari user)
- Modul punya chatbot untuk query insight atau navigasi sistem
- Setiap kali user perlu trigger flow secara natural language atau klarifikasi intent

**Kapan tidak dipakai**:
- Modul pure backend tanpa user-facing interaction
- Modul yang user-interaction-nya cuma form-based (tidak butuh natural language)

**Contoh use case**:
- "Apa tren persepsi publik hari ini?" → query insight dari data
- HUMINT confirmation: "Apa objective utama dari request analisis ini?" sebelum trigger Data Collection + Analysis
- Intelligent navigation: user tanya "ada laporan apa hari ini?" → response + redirect ke halaman terkait
- Guidance ambiguous query: "Apakah Anda ingin: 1. Daily report, 2. Trend analysis, 3. Crisis summary?"

**Range trigger yang mungkin**:
- `User-triggered` — selalu dimulai dari user action (chat input, klik tombol)

**Output umum**: Natural language response, navigation action, structured query untuk agent downstream.

---

## #8 Reporting Agent

**Peran utama**: Menyusun output jadi format konsumsi (report, dashboard data, presentasi).

**Kapan dipakai**:
- Modul butuh generate report PDF, summary deck, dashboard rendering
- Project punya output untuk konsumsi manusia (klien, eksekutif, publik)
- Data sudah di-analisis dan siap di-format jadi human-readable artifact
- HTML/dashboard generation, infografis output, executive briefing

**Kapan tidak dipakai**:
- Modul tidak menghasilkan output untuk human consumption (cth: backend pipeline yang feed ke modul lain)
- Data belum di-analisis — Reporting bukan tempat analyze, dia format-and-present

**Contoh use case**:
- Generate executive briefing PDF setiap pagi pukul 06:00
- Render dashboard situasional dengan data agregat dari modul lain
- Generate infografis sentimen mingguan untuk humas
- Export report ad-hoc saat user klik tombol "Generate PDF"

**Range trigger yang mungkin**:
- `Scheduled` — generate report periodik (harian, mingguan, bulanan)
- `Manual` — saat user request export
- `Manual / scheduled` — kombinasi paling umum

**Output umum**: Human-readable report — PDF, dashboard data, HTML page, infografis.

---

## #9 Memory Agent

**Peran utama**: Mengelola memory dan context lintas session atau lintas waktu.

**Kapan dipakai**:
- Project punya AI Assistant yang butuh remember konteks user lintas session
- Modul punya conversation history yang panjang dan butuh summarization
- User preference / pattern perlu dipelajari sistem dari waktu ke waktu

**Kapan tidak dipakai**:
- Modul stateless per-request (sebagian besar modul backend)
- Tidak ada konsep session lintas waktu di modul

**Contoh use case**:
- AI Assistant ingat user X biasanya tanya tentang data fiskal — auto-prioritize konteks fiskal
- Long-term memory hasil analisis sebelumnya untuk dipakai di analisis sequential
- Session summary untuk continuity ketika user balik setelah beberapa hari

**Range trigger yang mungkin**:
- `Continuous` — always-on background service untuk maintain memory store

**Output umum**: Retrieved context / memory state untuk dipakai agent lain (paling sering Interactive Agent).

---

## #10 Knowledge Retrieval Agent

**Peran utama**: Mengambil informasi dari knowledge base internal (RAG, semantic search, doc QA).

**Kapan dipakai**:
- Modul AI Assistant Talk-to-Data — butuh retrieve relevant docs untuk jawab pertanyaan user
- Project punya knowledge base (dokumen, FAQ, regulasi) yang harus di-query secara semantic
- Sebelum Interactive Agent generate response, butuh konteks dari KB (anti-halusinasi)

**Kapan tidak dipakai**:
- Tidak ada knowledge base yang relevan
- Modul cuma query data structured (pakai SQL/dashboard, bukan retrieval semantic)

**Contoh use case**:
- RAG untuk jawab pertanyaan eksekutif berdasarkan dokumen RPJMD + RKPD
- Semantic search di knowledge base regulasi pemerintah
- Doc QA untuk pertanyaan "apa kebijakan terbaru tentang X?"

**Range trigger yang mungkin**:
- `On-demand` — dipanggil agent lain (biasanya Interactive Agent) saat butuh konteks dari KB

**Output umum**: Relevant documents / facts — top-K results dari semantic search dengan score.

---

## #11 Validation / Guardrail Agent

**Peran utama**: Validasi output dan kontrol kualitas sebelum output diteruskan.

**Kapan dipakai**:
- Output dari Analysis / Planning / Interactive akan diteruskan ke decision-maker (eksekutif, klien)
- Project punya risiko halusinasi atau output salah yang merugikan (reputational, legal, finansial)
- Sebelum Task Automation execute action sensitif (notif ke external, update DB kritis)
- Modul yang produce content publik atau affecting reputation

**Kapan tidak dipakai**:
- Output cuma internal monitoring tanpa decision impact
- Validation overkill untuk modul low-stakes (cth: dashboard internal yang user double-check sendiri)

**Contoh use case**:
- Cek hallucination di output Analysis Agent sebelum jadi recommendation ke eksekutif
- Format validation di output Reporting Agent sebelum publish
- Sandwich di pipeline: Analysis → Validation → Planning (Planning pakai output yang sudah ter-validate)
- Pre-action validation: sebelum Notification kirim alert ke kepala daerah, validate severity scoring benar

**Range trigger yang mungkin**:
- `Post-process` — paling umum, jalan setelah agent lain produce output

**Output umum**: Verified atau corrected output — flag valid/invalid, koreksi otomatis kalau bisa, atau reject dan notify.

---

## #12 Monitoring Agent

**Peran utama**: Observability dan health check sistem agent.

**Kapan dipakai**:
- Project butuh observability lintas-modul (sistem monitoring agent ecosystem)
- Tracking failure, latency, throughput agent-agent
- Lebih ke level OVERVIEW (lintas-modul), bukan per-modul

**Kapan tidak dipakai**:
- Per-modul level — Monitoring biasanya shared infrastructure di sistem
- Project kecil tanpa kebutuhan observability formal

**Contoh use case**:
- Track failure rate Data Collection Agent di tiap source
- Performance monitoring Analysis Agent (latency, throughput)
- Alert kalau ada agent yang down atau error rate spike

**Range trigger yang mungkin**:
- `Continuous` — always-on background

**Output umum**: Logs, alerts, metrics dashboard.

---

## #13 Learning / Improvement Agent

**Peran utama**: Optimasi sistem dari feedback (prompt tuning, eval, auto-improve).

**Kapan dipakai**:
- Project punya feedback loop dari user (rating, koreksi, eval)
- Sistem butuh continuous improvement untuk agent yang pakai LLM (prompt tuning, model selection)
- Lebih ke level meta-system, bukan per-modul

**Kapan tidak dipakai**:
- MVP atau POC — belum ada data feedback yang cukup
- Modul tanpa LLM atau ML component

**Contoh use case**:
- Periodic eval Analysis Agent berdasarkan ground truth dari humas
- Auto-tune prompt Interactive Agent berdasarkan user feedback
- A/B test model alternatif untuk sentiment analysis

**Range trigger yang mungkin**:
- `Offline / periodic` — jalan di luar jam operasional, tidak real-time

**Output umum**: Improved config, tuned prompts, model performance reports.

---

## #14 Security / Compliance Agent

**Peran utama**: Kontrol akses dan compliance (data masking, audit, policy enforcement).

**Kapan dipakai**:
- Modul handling data sensitif (data pribadi, data fiskal, data internal classified)
- Project punya regulasi yang harus dipatuhi (UU PDP, GDPR-equivalent)
- Audit log wajib untuk akuntabilitas
- Lintas-modul: muncul di OVERVIEW sebagai shared layer

**Kapan tidak dipakai**:
- Modul tidak handling data sensitif
- Compliance sudah handled di layer infrastruktur (bukan agent)

**Contoh use case**:
- Data masking untuk PII di output Reporting Agent sebelum di-share publik
- Audit log akses ke modul fiskal sensitive
- Policy enforcement: blok query yang akses data di luar wewenang user role

**Range trigger yang mungkin**:
- `Pre/Post process` — sandwich di sekitar agent yang akses data sensitif

**Output umum**: Safe output, audit log entry, access decision (allow/deny).

---

## #15 Simulation / What-if Agent

**Peran utama**: Simulasi skenario dan prediksi dampak.

**Kapan dipakai**:
- Modul butuh "what-if analysis" — eksekutif tanya "kalau X terjadi, apa dampaknya?"
- Project punya use case scenario planning (kebijakan, ekonomi, krisis)
- Ada model prediksi dengan parameter yang bisa di-vary

**Kapan tidak dipakai**:
- Tidak ada use case prediksi
- Data tidak cukup untuk reliable simulation

**Contoh use case**:
- Prediksi dampak kenaikan tarif PBB pada penerimaan daerah
- Scenario planning krisis: kalau banjir di 5 kecamatan, berapa lama recovery?
- What-if: kalau program X di-scale ke 3x, berapa cost & impact?

**Range trigger yang mungkin**:
- `On-demand` — selalu dipicu user request

**Output umum**: Simulation results — scenario outcomes, sensitivity analysis, confidence interval.

---

## #16 Tool Integration Agent

**Peran utama**: Abstraksi penggunaan tools/API external (S3, API, DB wrapper).

**Kapan dipakai**:
- Agent lain butuh akses external resource via tool (cloud storage, third-party API)
- Project butuh adapter layer untuk simplify integration
- Lintas-modul shared infrastructure

**Kapan tidak dipakai**:
- Akses tool langsung di-handle di layer integrasi sistem (bukan agent)
- Tidak ada external tool yang perlu di-wrap

**Contoh use case**:
- Wrapper ke S3 untuk simpan/ambil dokumen besar
- Adapter ke API LAPOR! untuk Data Collection Agent
- Tool wrapper untuk akses cloud database dari modul lain

**Range trigger yang mungkin**:
- `On-demand` — dipanggil agent lain saat butuh akses external

**Output umum**: Tool result — data dari external resource atau status operasi.

---

## #17 Workflow / State Agent

**Peran utama**: Mengelola state kompleks di proses multi-tahap.

**Kapan dipakai**:
- Modul punya proses multi-tahap dengan state machine (pengaduan: terima → klasifikasi → assign → tindak → tutup)
- Project butuh state persistence lintas waktu (proses bisa pause dan resume)
- Beda dengan Orchestrator (#6): Workflow/State manage **state internal** satu proses; Orchestrator manage **antar-agent**

**Kapan tidak dipakai**:
- Proses single-step tanpa state
- Stateless modul yang per-request independent

**Contoh use case**:
- Manajemen pengaduan multi-tahap dengan state transition tracked
- Workflow approval kebijakan dengan multi-stage review
- Process tracking untuk crisis response (declared → assess → respond → resolve)

**Range trigger yang mungkin**:
- `Event-driven` — state transition dipicu event (user action, agent output, threshold)

**Output umum**: State transitions log, current state, history of transitions.

---

## #18 Notification Agent

**Peran utama**: Distribusi hasil/alert ke user atau sistem (email, Slack, webhook, WhatsApp).

**Kapan dipakai**:
- Modul perlu kirim notif keluar (alert ke eksekutif, update ke stakeholder, broadcast ke publik)
- Trigger event sudah valid dari agent lain (bukan stand-alone — Notification jangan di-trigger user langsung untuk hindari abuse)
- Alert sistemik: sentiment drop, viral issue, crisis potential, threshold breach

**Kapan tidak dipakai**:
- Tidak ada use case notif keluar
- Notif handled di level UI (browser notification, in-app message) tanpa butuh agent terpisah

**Contoh use case**:
- Email harian briefing ke eksekutif pagi
- WhatsApp alert ke kepala OPD saat aduan kategori urgent masuk
- Webhook ke sistem eksternal saat threshold breach
- Push notif mobile saat status EWS berubah merah

**Range trigger yang mungkin**:
- `Event-driven` — dipicu agent lain (paling sering Task Automation atau Analysis yang detect anomaly)

**Output umum**: Notification sent confirmation — log delivery status, channel used, recipients.

---

## Closing — prinsip pakai catalog ini

1. **Vocabulary saja, bukan template.** Brief-builder reasoning dari konteks modul, bukan apply pattern pre-defined.

2. **Adaptive flow.** Setiap agent bisa muncul di mana saja di pipeline tergantung kebutuhan. Tidak ada "first agent" atau "last agent" yang fixed.

3. **Kombinasi trigger valid.** `Scheduler + on-demand` untuk Data Collection, `Event / batch` untuk Analysis — kombinasi natural OK selama pakai vocabulary canonical.

4. **Tidak semua modul butuh semua kategori.** Modul sederhana bisa cuma butuh 1-2 agent. Modul kompleks bisa butuh 7+. Agent stack mengikuti modul, bukan sebaliknya.

5. **Per-modul vs lintas-modul itu situasional.** Beberapa agent (Memory, Monitoring, Security, Learning) **sering** muncul di OVERVIEW sebagai shared infrastructure, **tapi bisa juga** muncul di feature brief kalau modul punya instance sendiri. Brief-builder yang putuskan case-by-case.

6. **Setelah baca catalog ini, baca `agent-rules.md`** untuk paham rules antar-agent dan kapan agent wajib/skip secara logis.
