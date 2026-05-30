# Voice Expense Tracker

Speak an expense out loud, get it parsed into structured data and stored automatically.

Record audio like *"spent 40 dollars at Costco on groceries and 12 on coffee at the cafe"* → Whisper transcribes it → Llama extracts each expense into `{amount, store, category, notes}` → everything is saved to SQLite and queryable by API. One recording can contain multiple expenses; each becomes its own row.

**Live:** https://voice-notes.duckdns.org/docs
**Stack:** FastAPI · Groq (Whisper + Llama) · SQLite · Docker · Caddy · Terraform · GitHub Actions · Oracle Cloud Always-Free
**Cost:** $0 (free-tier hosting + Groq free tier)

> Repo is named `voice-notes` (the project's original working name); the app itself is an expense tracker.

---

## What it does

1. `POST /api/expenses` with an audio file
2. Groq **Whisper** (`whisper-large-v3-turbo`) transcribes the audio to text
3. Groq **Llama** parses the transcript into one or more structured expenses
4. Each expense is saved to SQLite with its transcript and the raw model response
5. Query, summarize, or delete expenses through the API

The Llama call uses a **model-fallback chain** — it tries `llama-3.3-70b-versatile` first and falls back to `llama-4-scout-17b-16e-instruct` if that fails, so a single model hiccup doesn't break a request.

---

## Architecture

```
┌──────────┐   audio file   ┌───────────────┐
│  Client  │ ─────────────▶ │   FastAPI     │
│ (record) │                │  /api/expenses│
└──────────┘                └───────┬───────┘
                                    │ audio bytes
                                    ▼
                            ┌───────────────┐
                            │ Groq Whisper  │  speech → transcript
                            └───────┬───────┘
                                    │ transcript text
                                    ▼
                            ┌───────────────┐
                            │  Groq Llama   │  transcript → structured JSON
                            └───────┬───────┘  {amount, store, category, notes}
                                    │ parsed expenses
                                    ▼
                            ┌───────────────┐
                            │    SQLite     │  one row per expense
                            │  expenses.db  │  (persisted in a Docker volume)
                            └───────────────┘

Hosting :  Oracle Cloud Always-Free ARM VM (Ampere A1)
Ingress :  Caddy reverse proxy (automatic HTTPS via Let's Encrypt) ──▶ FastAPI :8000
IaC     :  Terraform provisions the VM, network, firewall
CI/CD   :  GitHub Actions — push to master ──▶ rsync to VM ──▶ rebuild container
```

---

## Tech choices (and why)

| Tool | Why |
|------|-----|
| **FastAPI** | Async, minimal boilerplate, auto-generates interactive API docs at `/docs`. |
| **Groq** | Very fast LLM + Whisper inference with a usable free tier; OpenAI-compatible API. |
| **Whisper `large-v3-turbo`** | Strong transcription quality at low latency. |
| **Llama (3.3-70b → llama-4-scout fallback)** | Good structured-extraction quality; fallback adds resilience to transient failures. |
| **SQLite** | Zero-config, single-file database — right-sized for a personal tool. Persisted in a Docker volume so data survives restarts. |
| **Docker + Compose** | Reproducible runtime; identical locally and on the VM. |
| **Caddy** | Reverse proxy with automatic, auto-renewing HTTPS in ~3 lines of config. |
| **Terraform** | Whole cloud setup (VM, network, firewall) defined as code and reproducible. |
| **GitHub Actions** | Free CI/CD; auto-deploys on every push to `master`. |
| **Oracle Cloud Always-Free** | Genuinely free ARM VM (no time limit), enough RAM for this workload. |

Prompts live in `prompts/` as YAML + markdown, kept out of the application code so they can be edited without touching Python.

---

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`    | `/` | Health check. |
| `POST`   | `/api/expenses` | Upload audio (max 25 MB); transcribes, parses, and saves expenses. |
| `GET`    | `/api/expenses` | List expenses (`?limit=`, `?offset=`). |
| `GET`    | `/api/expenses/summary` | Spend totals grouped by category (`?days=`). |
| `GET`    | `/api/expenses/{id}` | Fetch a single expense. |
| `DELETE` | `/api/expenses/{id}` | Delete an expense. |

Interactive docs (try it in the browser): **`/docs`**

---

## Run locally

```bash
git clone https://github.com/<your-username>/voice-notes.git
cd voice-notes

cp .env.example .env                      # add your GROQ_API_KEY
docker compose up voice-notes --build     # app on http://localhost:8080/docs
```

Locally, `compose.override.yaml` exposes the app on port 8080 and the Caddy/HTTPS
layer is skipped (running only the `voice-notes` service). On the server, the plain
`compose.yaml` runs the app behind Caddy with automatic HTTPS.

`.env` needs:

```
GROQ_API_KEY=gsk_your_key_here
DB_PATH=/data/expenses.db
```

Get a free Groq key at https://console.groq.com/keys

---

## Deployment

Infrastructure is provisioned with Terraform and the app deploys automatically via GitHub Actions.

**Provision the VM (one time):**

```bash
cd infra
terraform init
terraform apply        # creates VM, network, firewall on Oracle Cloud
```

**Deploy (automatic):**
Push to `master`. GitHub Actions then:
1. rsyncs the project to the VM (excluding secrets and infra files)
2. writes `.env` on the VM from GitHub Secrets
3. rebuilds and restarts the Docker containers
4. health-checks the live URL

Required GitHub Secrets: `OCI_SSH_PRIVATE_KEY`, `OCI_VM_IP`, `GROQ_API_KEY`.

---

## Project structure

```
voice-notes/
├── app/
│   ├── main.py            # FastAPI app + routes
│   ├── groq_client.py     # Whisper transcription + Llama parsing (with model fallback)
│   ├── database.py        # SQLite access layer
│   └── requirements.txt
├── prompts/               # externalized LLM prompts (YAML + markdown)
├── infra/                 # Terraform (Oracle Cloud VM, network, firewall)
├── .github/workflows/     # GitHub Actions deploy pipeline
├── Caddyfile              # reverse proxy + auto-HTTPS
├── Dockerfile
├── compose.yaml           # base (production: app behind Caddy)
└── compose.override.yaml  # local dev only (exposes app on :8080)
```

---

## Roadmap

- [ ] Simple web frontend (record button → results)
- [ ] LLM observability (trace prompts, latency, token usage)
- [ ] Evals for the expense-parsing prompt
- [ ] Automated SQLite backups