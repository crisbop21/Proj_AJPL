# 🎙️ Life Coach Voice Notes App

A personal tool for a life coach to record voice notes in Spanish after client sessions, structure them using Claude AI, store them in Supabase, and generate PDF reports per client.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit (Python) |
| Voice Recording | streamlit-audiorecorder |
| Speech to Text | ElevenLabs Scribe v2 |
| AI Structuring | Anthropic Claude (claude-sonnet-4-20250514) |
| Database | Supabase (PostgreSQL) |
| PDF Generation | ReportLab |
| Deployment | Streamlit Community Cloud |

**Total additional cost: $0** — runs entirely on existing ElevenLabs and Anthropic subscriptions plus free tiers for Supabase and Streamlit Cloud.

---

## Features

- Record voice notes in Spanish directly in the browser
- Transcribe audio using ElevenLabs Scribe v2 (best-in-class Spanish accuracy)
- Structure notes with Claude into 7 coaching fields in Spanish
- Select clients from a dropdown or add new ones on the fly
- Append new sessions to existing client history in Supabase
- Generate downloadable PDF reports summarizing a client's full session history

---

## Project Structure

```
life-coach-app/
├── app.py                    # Main Streamlit entry point
├── pages/
│   ├── 1_recording.py        # Voice recording and session saving
│   ├── 2_history.py          # Client history and PDF generation
│   └── 3_clients.py          # Client management
├── services/
│   ├── transcription.py      # ElevenLabs Scribe v2 calls
│   ├── structuring.py        # Claude API calls and prompt logic
│   ├── database.py           # Supabase CRUD operations
│   └── pdf_generator.py      # ReportLab PDF assembly
├── .streamlit/
│   └── secrets.toml          # API keys (gitignored — never commit this)
├── CLAUDE.md                 # Instructions for Claude Code development
├── requirements.txt
└── README.md
```

---

## Local Setup

### 1. Clone the repo

```bash
git clone https://github.com/youruser/life-coach-app.git
cd life-coach-app
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure secrets

Create `.streamlit/secrets.toml` and add your keys:

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
ELEVENLABS_API_KEY = "sk_..."
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGci..."
```

### 4. Run the Supabase SQL

In your Supabase SQL Editor, run the two CREATE TABLE statements in `CLAUDE.md` under the Database Schema section.

### 5. Run the app

```bash
streamlit run app.py
```

---

## Deployment

1. Push to GitHub (ensure `.streamlit/secrets.toml` is in `.gitignore`)
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo
3. Set main file path to `app.py`
4. Go to Advanced Settings > Secrets and paste your `secrets.toml` contents
5. Click Deploy

---

## Claude Structured Summary Fields

Every session note is processed by Claude and stored as a JSON object with these fields (all in Spanish):

| Field | Description |
|---|---|
| `resumen_sesion` | 2 to 3 sentence overview of the session |
| `objetivos_trabajados` | Goals that were active or discussed |
| `obstaculos_identificados` | Blockers, fears, or resistance points |
| `avances_y_revelaciones` | Breakthroughs and insights |
| `compromisos_del_cliente` | Actions the client committed to |
| `temas_pendientes` | Topics to follow up on next session |
| `estado_emocional` | Observed or reported emotional state |

---

## Roadmap

- [x] Voice recording in browser
- [x] ElevenLabs transcription in Spanish
- [x] Claude structuring into coaching fields
- [x] Supabase client and session storage
- [x] PDF report generation
- [ ] Session editing after saving
- [ ] Date filtering in history view
- [ ] Password protection login gate
- [ ] Cross-client insights view
- [ ] Real-time transcription via ElevenLabs Scribe v2 Realtime WebSocket

---

## Privacy

This app is for personal use only. All client data is stored in a private Supabase project. No data is shared with third parties beyond the API calls to ElevenLabs (audio) and Anthropic (text). Both providers have data privacy policies compatible with professional coaching use.
