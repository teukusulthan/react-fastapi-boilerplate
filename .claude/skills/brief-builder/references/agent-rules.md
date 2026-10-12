# Agent Rules — Adaptive Orchestration Rules

File ini adalah **rules adaptive** yang brief-builder pakai saat reasoning agent stack untuk modul tertentu. Berbeda dengan `agent-catalog.md` yang vocabulary, file ini berisi **logical rules** yang menjamin agent stack masuk akal — tidak rigid pipeline, tapi tetap koheren.

## Cara pakai file ini

- **Setelah baca `agent-catalog.md`** untuk paham vocabulary, baca file ini untuk paham **kapan agent X membutuhkan agent Y, kapan tidak, dan kenapa**.
- Rules di sini bersifat **conditional**, bukan absolute. Setiap rule punya kondisi "kalau X, maka Y". Brief-builder evaluate kondisi dulu sebelum apply rule.
- Rules adaptive ke konteks project. Project punya HUMINT lengkap → behave berbeda dengan project tanpa HUMINT. Rules di sini cover keduanya.

## Prinsip dasar adaptability

**1. Tidak ada urutan agent yang fixed.** Agent bisa dipanggil di mana saja di flow. Misal: Analysis Agent yang detect data gap boleh trigger Data Collection mid-flow.

**2. Rules berdasarkan kebutuhan logis, bukan template.** "Reporting butuh Analysis upstream" karena Reporting tidak boleh format-and-present data noise — ini logis, bukan template.

**3. Tidak semua agent yang kelihatan related = wajib pasangan.** Beberapa kombinasi optional, beberapa wajib, beberapa mutually exclusive. Rules clarify yang mana.

**4. Counter-rules ada untuk fleksibilitas.** Setiap rule biasanya punya "Kecuali..." untuk handle edge case.

---

## Bagian 1 — Rules per-agent (basic constraints)

Per agent, ada minimum requirements yang harus terpenuhi supaya agent itu masuk akal di brief.

### Data Collection Agent

**Rule DC-1 — Wajib ada Section "Kebutuhan Data Eksternal" di feature brief.**
Kalau modul punya Data Collection Agent, maka modul itu harus punya Section "Kebutuhan Data Eksternal" yang isinya. Tidak boleh ada Data Collection tanpa source yang jelas.
*Kecuali*: Data Collection untuk pull data internal dari sistem klien yang lain (cross-module data fetch). Tetap perlu state sumbernya, walau bukan eksternal.

**Rule DC-2 — Wajib disertai Data Processing Agent setelahnya.**
Raw data dari Data Collection tidak boleh langsung jadi input ke Analysis atau Reporting. Wajib ada Data Processing untuk normalize, dedupe, validate.
*Kecuali*: Data Collection menarik data yang **sudah clean dan structured** dari sumber well-curated (rare — biasanya only API resmi pemerintah dengan data quality terjamin). Brief harus state eksplisit kalau skip Data Processing dengan alasan.

**Rule DC-3 — Trigger jelas di brief.**
Setiap Data Collection harus state trigger-nya: scheduled (sebut frekuensi), event-driven (sebut event pemicu), atau on-demand (sebut user action pemicu). Jangan kabur.

### Data Processing Agent

**Rule DP-1 — Tidak stand-alone.**
Data Processing tidak muncul di brief tanpa Data Collection upstream **atau** input data lain (HUMINT manual, internal DB ingest). Tidak ada Processing tanpa data source.

**Rule DP-2 — Output deterministik harus jelas.**
Brief harus state apa hasil processing-nya: clean text? deduplicated records? normalized format? Jangan vague.

### Analysis Agent

**Rule AN-1 — Wajib ada validated data input.**
Analysis tidak boleh dipanggil tanpa upstream yang produce ter-validate data. Sumber valid:
- Data Processing Agent output
- Knowledge Retrieval Agent output (untuk RAG-based analysis)
- HUMINT input langsung dari user yang sudah di-validate Interactive Agent (HUMINT confirmation)
- Data internal klien yang sudah structured (bypass Data Collection + Processing)

**Rule AN-2 — Output Analysis butuh Validation kalau affecting decision.**
Kalau output Analysis akan jadi basis Planning, Notification ke external, atau action otomatis — wajib ada Validation/Guardrail Agent post-process. Counter halusinasi.
*Kecuali*: Analysis untuk monitoring internal yang user double-check sendiri (cth: dashboard internal dengan transparansi data source).

**Rule AN-3 — Boleh trigger Data Collection mid-flow kalau data gap.**
Counter ke pipeline rigid: Analysis yang detect data tidak cukup boleh trigger Data Collection untuk lengkapi. Pattern adaptive valid.

### Planning Agent

**Rule PL-1 — Wajib ada konteks dari Analysis atau Knowledge Retrieval.**
Planning tidak generate strategy dari kosong. Konteks bisa dari:
- Analysis Agent (insight dari data)
- Knowledge Retrieval (best practices dari KB)
- Memory Agent (context dari sesi sebelumnya)

**Rule PL-2 — Output Planning butuh Validation kalau affecting policy/strategi.**
Sama dengan Analysis — Planning yang affect keputusan strategis butuh Validation post-process.

### Task Automation Agent

**Rule TA-1 — Wajib ada validated trigger.**
Task Automation tidak fire pada raw event. Trigger harus dari:
- Analysis Agent yang detect kondisi terpenuhi (sudah filtered)
- Workflow/State Agent yang transition ke state tertentu
- Validated threshold breach (bukan noise)

**Rule TA-2 — Action sensitif butuh Validation pre-process.**
Kalau action affect external stakeholder atau update DB kritis, wajib ada Validation pre-process untuk konfirmasi action benar.

### Orchestrator Agent

**Rule OR-1 — Hanya kalau 3+ agent dengan dependency.**
Orchestrator overkill untuk pipeline 1-2 agent linear. Cukup event chain antar agent. Orchestrator wajib kalau ada branching kompleks atau crisis coordinator.

**Rule OR-2 — Tidak user-triggered.**
Orchestrator selalu system-level. Kalau pipeline harus dipicu user, user trigger Interactive Agent yang lalu invoke Orchestrator.

### Interactive Agent

**Rule IA-1 — Talk-to-Data wajib ada Knowledge Retrieval atau direct data access.**
Interactive yang jawab pertanyaan user tentang data **tidak boleh halusinasi**. Wajib ground di Knowledge Retrieval (untuk dokumen) atau direct query ke data structured (untuk metrics).

**Rule IA-2 — HUMINT confirmation tidak butuh agent lain di backend.**
Interactive yang berperan sebagai HUMINT gate (validasi objective user sebelum jalankan flow) tidak butuh upstream agent. Pure user-facing dialogue.

**Rule IA-3 — Trigger ke pipeline backend lewat Orchestrator atau Task Automation.**
Interactive tidak langsung manage agent backend. Setelah Interactive validate user intent, dia trigger Orchestrator atau Task Automation untuk eksekusi pipeline.

### Reporting Agent

**Rule RP-1 — Wajib ada data source yang structured.**
Reporting tidak boleh format data noise atau raw. Data source bisa dari:
- Output Analysis Agent (paling umum)
- Data warehouse internal yang sudah structured
- Knowledge Retrieval untuk template-based reports

**Rule RP-2 — Reporting bukan Analysis.**
Kalau output butuh interpretasi atau insight generation, itu Analysis. Reporting cuma format-and-present existing insight. Jangan campur.

### Notification Agent

**Rule NT-1 — Wajib ada validated trigger event.**
Notification tidak stand-alone. Trigger harus dari Task Automation (action result), Analysis (anomaly detected), atau Workflow/State (state transition).

**Rule NT-2 — External-facing notification butuh Validation.**
Kalau notif keluar ke pihak eksternal (publik, eksekutif eksternal, media), wajib ada Validation pre-process. Counter risiko reputational atau salah send.

### Validation/Guardrail Agent

**Rule VG-1 — Sandwich pattern.**
Validation muncul di antara dua agent: `[Agent A] → Validation → [Agent B atau output]`. Tidak stand-alone.

**Rule VG-2 — Wajib di pipeline yang affect decision.**
Wajib hadir kalau pipeline produce output untuk: eksekutif decision, external stakeholder, action otomatis sensitif. Optional kalau output cuma internal monitoring.

### Memory Agent

**Rule MM-1 — Hanya kalau ada multi-session continuity.**
Memory tidak diperlukan untuk modul stateless atau per-request independent. Wajib kalau project punya AI Assistant yang harus ingat user context lintas sesi.

**Rule MM-2 — Pasangan dengan Interactive Agent.**
Memory paling sering muncul bersamaan dengan Interactive Agent — Memory feed konteks ke Interactive untuk personalisasi response.

### Knowledge Retrieval Agent

**Rule KR-1 — Wajib ada knowledge base.**
Knowledge Retrieval tidak make sense tanpa KB yang relevan. Brief harus state KB-nya: dokumen apa, struktur apa.

**Rule KR-2 — Pasangan dengan Interactive atau Analysis.**
Knowledge Retrieval rarely stand-alone. Dipanggil oleh Interactive (untuk Talk-to-Data) atau Analysis (untuk RAG-based analysis).

### Workflow/State Agent

**Rule WS-1 — Hanya untuk proses multi-tahap dengan state.**
Workflow/State overkill untuk single-step process. Wajib kalau modul punya state machine yang explicit (cth: pengaduan dengan state transitions).

**Rule WS-2 — Beda dengan Orchestrator.**
Workflow/State manage **internal state** satu proses (cth: state pengaduan). Orchestrator manage **antar-agent** di pipeline. Bisa coexist: Workflow/State trigger Orchestrator yang trigger agent-agent untuk state tertentu.

### Monitoring / Security / Learning

**Rule MS-1 — Lintas-modul, biasanya di OVERVIEW.**
Monitoring, Security/Compliance, Learning/Improvement default-nya muncul di OVERVIEW sebagai shared infrastructure. Tidak per-modul, kecuali modul punya kebutuhan unik (cth: modul fiskal yang butuh Security tier ekstra).

**Rule MS-2 — Tidak masuk pipeline data flow.**
Ketiga agent ini bukan bagian dari data flow modul. Mereka observability/governance layer yang lintas semua agent.

---

## Bagian 2 — Rules antar-agent (relationships dan dependencies)

Pasangan dan kombinasi agent yang sering muncul, plus rules-nya.

### Pipeline data canonical (paling umum)

```
[Data source eksternal]
  ↓
Data Collection Agent
  ↓ (post-collection event)
Data Processing Agent
  ↓ (clean data event)
Analysis Agent
  ↓ (insight ready event)
[Validation Agent — opsional, wajib kalau affecting decision]
  ↓
[Reporting Agent / Planning Agent / Task Automation / Notification]
```

**Rules untuk pipeline ini:**
- DC + DP wajib pasangan (Rule DC-2)
- AN butuh DP upstream atau alternatif (Rule AN-1)
- VG opsional tapi recommended kalau output keluar dari pipeline ke decision-maker

**Counter-pattern (adaptive):**
- AN bisa trigger DC mid-flow kalau data gap (Rule AN-3)
- DC bisa multi-source paralel (3 sumber → 3 instance DC → merge di DP)
- AN bisa beberapa stage (sentiment AN → topic AN → narrative AN, sequential)

### Pipeline interaktif (AI Assistant Talk-to-Data)

```
User question
  ↓
Interactive Agent (User-triggered, HUMINT validation)
  ↓ (on-demand call)
Knowledge Retrieval Agent (RAG to KB)
  ↓ (relevant context)
Interactive Agent (synthesize natural language response)
  ↓ (kalau user request action)
[Orchestrator atau Task Automation untuk trigger backend pipeline]
```

**Rules untuk pipeline ini:**
- IA wajib pasangan dengan KR untuk anti-halusinasi (Rule IA-1)
- IA tidak langsung trigger pipeline backend — lewat Orchestrator atau TA (Rule IA-3)
- Memory Agent opsional, paling sering muncul di pipeline ini (Rule MM-2)

### Pipeline workflow stateful (proses multi-tahap)

```
Trigger event (user action atau system)
  ↓
Workflow/State Agent (manage state machine)
  ↓ (at state transition)
[Agent yang relevan untuk state itu — Analysis, Task Automation, Notification, dst]
  ↓ (state result)
Workflow/State Agent (update state, log transition)
```

**Rules untuk pipeline ini:**
- WS dipakai untuk proses multi-step dengan state (Rule WS-1)
- WS tidak menggantikan Orchestrator — keduanya bisa coexist (Rule WS-2)
- Setiap state transition bisa trigger agent berbeda — adaptive

### Pipeline crisis response (kompleks dengan branching)

```
Threshold breach detected (oleh Analysis Agent)
  ↓
Orchestrator Agent (System-level, coordinate respons)
  ├─ Severity LOW → Notification ke monitoring team only
  ├─ Severity MEDIUM → Planning Agent generate strategi → Notification ke decision-maker
  └─ Severity HIGH → Planning Agent + Validation + multi-channel Notification + Workflow/State activate crisis mode
```

**Rules untuk pipeline ini:**
- OR wajib karena 3+ agent dengan branching (Rule OR-1)
- VG di branch HIGH wajib karena affect external + decision (Rule VG-2)
- Beberapa agent run paralel di branch HIGH

---

## Bagian 3 — Counter-rules untuk fleksibilitas

Rules yang mengakomodasi edge case dan project unik.

### Counter-rule 1 — Project dengan HUMINT lengkap dari user

**Skenario**: User upload data lengkap (cth: laporan investigasi, data survey internal). Tidak butuh Data Collection.

**Implikasi:**
- Data Collection Agent → SKIP
- Data Processing Agent → tetap dipakai untuk validate dan normalize HUMINT input
- Pipeline mulai dari: HUMINT → Interactive Agent (validate intent) → Data Processing → Analysis → ...
- Section "Kebutuhan Data Eksternal" di feature brief → SKIP
- Section "Stack Agent Modul" mention bahwa data input HUMINT, bukan eksternal

### Counter-rule 2 — Project dengan data internal sudah lengkap

**Skenario**: Klien punya database internal dengan data structured siap pakai.

**Implikasi:**
- Data Collection Agent → SKIP (tidak butuh pull dari eksternal)
- Data Processing Agent → opsional (kalau data sudah clean, bisa skip; kalau butuh enrichment/transformation, tetap dipakai)
- Analysis Agent langsung query ke data internal
- Section "Kebutuhan Data Eksternal" di feature brief → SKIP atau minimal (kalau butuh enrichment dari eksternal)

### Counter-rule 3 — Modul minimal (1-2 agent)

**Skenario**: Modul sederhana yang cuma butuh 1-2 agent (cth: dashboard agregator, modul Auth).

**Implikasi:**
- Tidak perlu Orchestrator (Rule OR-1)
- Tidak perlu Validation (kecuali high-stakes)
- Section "Stack Agent Modul" cukup tabel agent + brief reasoning, tanpa flow diagram

### Counter-rule 4 — Modul tanpa agent

**Skenario**: Modul utility murni yang tidak butuh agent (cth: modul Auth/RBAC pure CRUD, modul Notifikasi sebagai gateway pure passthrough yang dipanggil agent lain).

**Implikasi:**
- Section "Stack Agent Modul" → SKIP di feature brief
- Modul tetap muncul di OVERVIEW Section "Konsolidasi Stack Agent" dengan note "tidak punya agent stack sendiri"

### Counter-rule 5 — Mid-flow trigger reverse direction

**Skenario**: Agent downstream (Analysis, Reporting) menemukan kondisi yang butuh re-trigger agent upstream (Data Collection).

**Implikasi:**
- Pattern valid dan adaptive (Rule AN-3)
- Brief boleh state ini di Section flow diagram dengan branching: "Kalau data gap → trigger DC refresh → loop balik ke AN"
- Tidak melanggar rules — pipeline tidak harus linear

### Counter-rule 6 — Agent shared lintas modul

**Skenario**: Notification Agent yang sama dipakai 5 modul berbeda untuk kirim alert.

**Implikasi:**
- Notification muncul di Section "Stack Agent Modul" tiap modul yang pakai (dengan trigger spesifik per modul)
- Di OVERVIEW Section "Konsolidasi Stack Agent", Notification muncul sekali sebagai shared resource dengan list modul yang pakai
- Konsistensi cross-modul wajib (di OVERVIEW dan tiap feature brief harus match)

---

## Bagian 4 — Checklist reasoning untuk brief-builder

Sebelum finalize Section "Stack Agent Modul" di feature brief, brief-builder jalankan checklist:

**Step 1 — Pahami konteks modul:**
- Apa data yang masuk ke modul? Eksternal, HUMINT, internal?
- Apa output modul? Insight, action, report, notif?
- Apa user-facing component? Chatbot, dashboard, backend service?
- Apa state management? Stateful multi-tahap atau stateless?

**Step 2 — Identifikasi agent dari konteks:**
- Untuk tiap "apa yang dilakukan modul" di Section 2 Fitur Utama, mapping ke canonical agent dari `agent-catalog.md`
- Tidak force agent yang tidak relevan
- Tidak skip agent yang clearly needed berdasarkan konteks

**Step 3 — Apply rules:**
- Setiap agent yang ter-identify, cek rules basic (Bagian 1) — apakah requirements terpenuhi?
- Cek rules antar-agent (Bagian 2) — apakah pasangan/dependency sound?
- Cek counter-rules (Bagian 3) — apakah ada edge case yang apply?

**Step 4 — Reasoning to user:**
- Untuk tiap agent di stack, kasih alasan singkat: "Data Collection Agent — untuk pull data BPS bulanan karena modul butuh data demografi terkini"
- Trigger eksplisit pakai vocabulary canonical
- Output umum: state apa yang dihasilkan agent untuk dikonsumsi downstream

**Step 5 — Konsistensi:**
- Cek konsistensi dengan Section "Kebutuhan Data Eksternal" — kalau data eksternal disebut, Data Collection harus ada (atau alasan eksplisit kalau skip)
- Cek konsistensi dengan Alur Bisnis di Section 4 — agent stack support flow yang disebut
- Cek konsistensi dengan modul lain di OVERVIEW — agent shared muncul di kedua tempat

**Step 6 — Adaptability check:**
- Apakah ada "kecuali..." yang relevan untuk project ini?
- Apakah ada pattern non-linear yang harus di-state (mid-flow trigger, branching)?
- Apakah agent stack ini reflect kebutuhan project, bukan template?

---

## Closing — prinsip pakai rules

1. **Rules adaptive, bukan absolute.** Setiap rule punya counter-rule untuk edge case. Brief-builder evaluate konteks dulu.

2. **Rules grounded di logika, bukan formalisme.** "Reporting butuh Analysis upstream" bukan karena template, tapi karena Reporting tanpa insight = format-and-present noise.

3. **Project unik wajar.** Counter-rules ada untuk handle project yang menyimpang dari pattern umum. Brief-builder transparent state penyimpangan dengan alasan.

4. **Konsistensi cross-section wajib.** Stack Agent harus konsisten dengan Kebutuhan Data Eksternal, Alur Bisnis, dan modul lain di OVERVIEW. Inkonsistensi = brief incomplete.

5. **Adaptive sambil masuk akal.** Fleksibel tidak berarti chaos. Rules di sini menjamin agent stack tetap koheren walau bentuknya bervariasi per project.
