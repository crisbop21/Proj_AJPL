# CLAUDE.md — Development Instructions

This file tells Claude Code everything it needs to know to build and extend this project correctly. Read this fully before writing any code.

---

## What This App Does

This is a personal Streamlit app for a Spanish-speaking life coach. It allows her to:

1. Record voice notes in Spanish after client sessions directly in the browser
2. Transcribe them using ElevenLabs Scribe v2
3. Structure the content using Claude into 7 coaching fields stored as JSON
4. Associate notes with a specific client selected from a dropdown
5. Store all sessions in Supabase
6. Generate a PDF report per client summarizing their full history

Everything is in Spanish. All AI outputs must be in Spanish. All UI labels should be in Spanish.

---

## Tech Stack and Versions

```
streamlit>=1.32.0
streamlit-audiorecorder>=0.0.5
anthropic>=0.25.0
elevenlabs>=1.0.0
supabase>=2.0.0
reportlab>=4.0.0
pydub>=0.25.1
av>=10.0.0
```

Do not add new dependencies without checking if existing ones can handle the task.

---

## Secrets and Environment

All secrets are in `.streamlit/secrets.toml` (gitignored). Access them in code via `st.secrets`:

```python
st.secrets["ANTHROPIC_API_KEY"]
st.secrets["ELEVENLABS_API_KEY"]
st.secrets["SUPABASE_URL"]
st.secrets["SUPABASE_ANON_KEY"]
```

Never hardcode keys. Never use `os.environ` — always use `st.secrets`.

---

## Database Schema (Supabase / PostgreSQL)

### clients table

```sql
CREATE TABLE clients (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT NOT NULL,
  notes       TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

### sessions table

```sql
CREATE TABLE sessions (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id           UUID REFERENCES clients(id) ON DELETE CASCADE,
  raw_transcript      TEXT,
  structured_summary  JSONB,
  session_number      INT,
  recorded_at         TIMESTAMPTZ DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION set_session_number()
RETURNS TRIGGER AS $$
BEGIN
  SELECT COALESCE(MAX(session_number), 0) + 1
  INTO NEW.session_number
  FROM sessions
  WHERE client_id = NEW.client_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER auto_session_number
BEFORE INSERT ON sessions
FOR EACH ROW EXECUTE FUNCTION set_session_number();
```

The `structured_summary` column is JSONB. Always store Claude output as a parsed Python dict, not a string.

---

## Services Architecture

All business logic lives in `services/`. Streamlit pages only call service functions — no API calls inside page files.

### services/database.py

Handles all Supabase reads and writes. Key functions:

```python
def get_all_clients() -> list[dict]
def add_client(name: str, notes: str = "") -> None
def delete_client(client_id: str) -> None
def save_session(client_id: str, transcript: str, summary: dict) -> None
def get_sessions_for_client(client_id: str) -> list[dict]
def delete_session(session_id: str) -> None
```

Always call `create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])` inside each function, not at module level, to avoid connection issues in Streamlit's hot-reload environment.

### services/transcription.py

Uses ElevenLabs Scribe v2. Always pass `language_code="es"` and `model_id="scribe_v2"`.

```python
def transcribe_audio(audio_path: str) -> str:
    client = ElevenLabs(api_key=st.secrets["ELEVENLABS_API_KEY"])
    with open(audio_path, "rb") as f:
        result = client.speech_to_text.convert(
            file=f,
            model_id="scribe_v2",
            language_code="es"
        )
    return result.text
```

The audio file must be WAV format. Use pydub to export if needed before calling this function.

### services/structuring.py

Calls Claude with a strict Spanish system prompt and returns parsed JSON. Always use `claude-sonnet-4-20250514`. The response must be parsed with `json.loads`. Wrap in try/except and if parsing fails, make a follow-up call asking Claude to return only valid JSON.

System prompt to use verbatim:

```
Eres un asistente para una coach de vida. Recibirás la transcripción
de una nota de voz en español grabada tras una sesión con un cliente.

Devuelve ÚNICAMENTE un objeto JSON válido con estas claves exactas:
  resumen_sesion (string)
  objetivos_trabajados (array of strings)
  obstaculos_identificados (array of strings)
  avances_y_revelaciones (array of strings)
  compromisos_del_cliente (array of strings)
  temas_pendientes (array of strings)
  estado_emocional (string)

Sin texto fuera del JSON. Sin bloques de código. Solo el objeto JSON. Todo en español.
```

### services/pdf_generator.py

Uses ReportLab to build an in-memory PDF. Returns `bytes` (not a file path). Use `io.BytesIO` as the buffer.

Before building the PDF, make one additional Claude call to generate a `resumen_general` by passing all session summaries concatenated. This synthesis appears on the report cover page.

PDF structure in order:
1. Cover: client name, date range, session count, resumen_general
2. Historial de Sesiones: one section per session with date, resumen_sesion, compromisos_del_cliente, avances_y_revelaciones
3. Temas Pendientes: unique list aggregated from all sessions

---

## Streamlit Pages

### app.py

Sets page config and displays a welcome message. No logic here.

```python
st.set_page_config(page_title="Life Coach Notes", page_icon="🎙️", layout="wide")
```

### pages/1_recording.py — Nueva Sesión

Flow in strict order:
1. Client selector dropdown (loaded from Supabase)
2. audiorecorder component for mic capture
3. On audio captured: show audio playback widget
4. Button: "Transcribir y estructurar"
5. On click: export audio to temp WAV file, call transcribe_audio, delete temp file
6. Show transcript in editable st.text_area
7. Call structure_notes with the transcript
8. Display structured summary using st.expander per field
9. Button: "Guardar sesión" — calls save_session then shows st.success

Use `st.spinner` for transcription and structuring steps. Use `tempfile.NamedTemporaryFile` for the audio file and always delete it after transcription.

### pages/2_history.py — Historial

1. Client selector dropdown
2. Show count of sessions
3. Loop through sessions in chronological order using st.expander per session
4. Label each expander: "Sesión {session_number} — {recorded_at[:10]}"
5. Button: "Generar Reporte PDF"
6. On click: call generate_pdf, show st.download_button with the returned bytes

### pages/3_clients.py — Clientes

1. Form to add new client: name (required) and notes (optional)
2. On submit: call add_client, then st.rerun() to refresh
3. List all clients below with name and created_at date

---

## Code Style Rules

- All UI text, labels, buttons, and messages must be in Spanish
- All Claude outputs are in Spanish — never translate them in the UI
- Never put API calls inside Streamlit page files — always use services/
- Use f-strings for string formatting
- Use type hints on all service function signatures
- Use `st.spinner()` for every operation that takes more than 1 second
- Use `st.success()` after saves, `st.error()` for caught exceptions, `st.warning()` for validation
- Never use `st.experimental_rerun()` — use `st.rerun()`
- Supabase client must be instantiated inside each function, not at module level

---

## Error Handling

Every API call (ElevenLabs, Claude, Supabase) must be wrapped in try/except. Show `st.error()` with a human-readable Spanish message on failure. Never let raw Python exceptions surface to the UI.

Example pattern:

```python
try:
    transcript = transcribe_audio(tmp_path)
except Exception as e:
    st.error(f"Error al transcribir el audio. Por favor intenta de nuevo.")
    st.stop()
```

---

## What Is Not Built Yet (Future Features)

These are in the roadmap but not implemented in v1:

- Session editing after saving
- Date range filtering in history
- Password login gate using st.secrets
- Cross-client insights view
- Real-time transcription via ElevenLabs Scribe v2 Realtime WebSocket
- Charts in PDF showing goal progress over time

Do not build these unless explicitly asked. Focus on making the MVP solid first.

---

## Testing Checklist Before Committing

- [ ] Add a test client in Clientes page — appears in dropdown immediately after rerun
- [ ] Record a 30-second Spanish voice note — transcript is returned in Spanish
- [ ] Structured summary has all 7 fields populated and in Spanish
- [ ] Save session — appears in Historial with correct session number
- [ ] Generate PDF — downloads correctly and contains resumen_general and session history
- [ ] No API keys appear anywhere in the code or logs
- [ ] No unhandled exceptions surface to the UI
