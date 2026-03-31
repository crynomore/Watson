<p align="center">
  <img src="https://img.shields.io/badge/Burp_Suite-Extension-orange?style=flat-square"/>
  <img src="https://img.shields.io/badge/AI-Gemini_/_Claude_/_OpenAI-blue?style=flat-square"/>
  <img src="https://img.shields.io/badge/Python-3.9+-green?style=flat-square"/>
  <img src="https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square"/>
</p>

# 🔍 Watson — AI Bug Bounty Assistant

Watson is an AI-powered Burp Suite extension that transforms manual web security testing into an autonomous, context-aware operation. It watches your traffic, builds session intelligence, generates targeted attack payloads, builds multi-step kill chains, and flags vulnerabilities — all inside Burp.

---

## ✨ Features

| Tab | What it does |
|-----|--------------|
| **AI Assistant** | Analyses every proxied request/response — produces a Burp-style advisory with attack ideas and next tests |
| **AI Repeater** | Multi-tab repeater with history, body diff, IDOR auto-enumeration, and AI chat |
| **JWT Analyzer** | Autonomous JWT detection, alg:none, sig-strip, secret brute-force, confusion attacks |
| **App Flow** | Live endpoint tree, OAuth analysis, CVE matching |
| **WebSocket** | Frame capture, replay, injection fuzzing |
| **Adv. Tests** | Rate limiting, prototype pollution, HTTP smuggling, GraphQL, business logic |
| **AI Fuzzer** ⚡ | AI generates targeted payloads (IDOR, SQLi, XSS, SSTI, SSRF…), fires them, evaluates each with AI, surfaces HITs into Intelligence |
| **Attack Chain** 🔗 | Sequences all session intelligence into a step-by-step kill chain with pre-built requests you can fire with one click |
| **Triage** | Per-finding status tags, notes, false positive management |
| **Intelligence** | Live session memory: findings, auth tokens, secrets, IDOR object graph, 18-step recon pipeline with Wayback, CORS, and AI attack surface report |

---

## 🚀 Quick Start

### What you need

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.9+ | Backend server |
| Burp Suite | Any | Community or Pro |
| AI API key | — | **Gemini is free — 30 seconds to get one** |

> **No Java or Maven required.** The compiled extension JAR is provided in [Releases](../../releases).

---

### Step 1 — Get a free AI API key

| Provider | Model | Cost | Get Key |
|----------|-------|------|---------|
| **Google Gemini ★** | `gemini-2.0-flash` | **Free** (1,500 req/day) | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| Anthropic Claude | `claude-sonnet-4-5` | Pay-as-go | [console.anthropic.com](https://console.anthropic.com/settings/keys) |
| OpenAI | `gpt-4.1-mini` | Pay-as-go | [platform.openai.com](https://platform.openai.com/api-keys) |

---

### Step 2 — Download

```bash
git clone https://github.com/youruser/watson.git
cd watson
```

Or download the ZIP from the [Releases](../../releases) page.

---

### Step 3 — Download the extension JAR

Go to [Releases](../../releases) and download `watson-burp.jar`.  
Place it in the `extension/` folder:

```
watson/
└── extension/
    └── watson-burp.jar   ← here
```

---

### Step 4 — Run the installer

**macOS / Linux:**
```bash
chmod +x install.sh
./install.sh
```

**Windows:**  
Double-click `install.bat`

The installer creates a Python virtual environment, installs dependencies, and copies `.env.example` → `.env`.

---

### Step 5 — Add your API key

Open `.env` in any text editor:

```env
# Gemini is free and recommended
AI_PROVIDER=gemini
GEMINI_API_KEY=AIza...your_key_here
```

---

### Step 6 — Start the backend

```bash
# macOS / Linux
./start.sh

# Windows
start.bat
```

You should see:
```
[Watson] Starting backend on http://127.0.0.1:8000
[Watson] Provider: gemini  Model: gemini-2.0-flash
```

---

### Step 7 — Load into Burp Suite

1. Open Burp Suite
2. Go to **Extensions → Installed → Add**
3. Select type: **Java**
4. Select file: `extension/watson-burp.jar`
5. Click **Next** — the **Watson** tab appears in Burp's main toolbar ✓

---

## ⚙️ Configuration

### Via the Settings dialog (easiest)

In Watson → **Intelligence** tab → **⚙ Settings**

- Switch AI provider and model live
- Update API keys (written back to `.env`)
- Test backend connection

### Via `.env`

```env
# ── Provider ──────────────────────────────────
AI_PROVIDER=gemini          # openai | claude | gemini

# ── Model (optional — Watson picks a default) ─
# MODEL=gemini-2.0-flash

# ── Keys ──────────────────────────────────────
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...
```

Restart the backend after editing `.env`.

---

## 🤖 AI Model Guide

### Which should I use?

**Getting started / free:**
```env
AI_PROVIDER=gemini
# 1,500 req/day free. No credit card. 1M token context.
```

**Best quality (attack chains, JWT analysis):**
```env
AI_PROVIDER=claude
MODEL=claude-sonnet-4-5
```

**Lowest cost for high-volume fuzzing:**
```env
AI_PROVIDER=openai
MODEL=gpt-4.1-mini
```

### Comparison

| | Gemini 2.0 Flash | Claude Sonnet | GPT-4.1-mini |
|---|---|---|---|
| **Cost** | **Free** | ~$0.003/1K | ~$0.0004/1K |
| **Context window** | **1M tokens** | 200K | 128K |
| **Attack chain reasoning** | ★★★★☆ | **★★★★★** | ★★★★☆ |
| **Payload generation** | ★★★★☆ | ★★★★☆ | ★★★★☆ |
| **JWT / crypto analysis** | ★★★★☆ | **★★★★★** | ★★★★☆ |
| **Speed** | **★★★★★** | ★★★☆☆ | ★★★★☆ |
| **Free tier** | **Yes** | No | No |

---

## 📁 Project Structure

```
watson/
├── backend/
│   ├── main.py          — FastAPI server
│   ├── analyzer.py      — Multi-provider AI engine (OpenAI / Claude / Gemini)
│   ├── memory.py        — Session state
│   └── prompts.py       — Context-aware prompt templates
├── extension/
│   └── watson-burp.jar  — Compiled Burp extension (download from Releases)
├── .env.example         — Copy to .env and fill in your key
├── .gitignore
├── install.sh           — macOS/Linux one-click installer
├── install.bat          — Windows one-click installer
├── start.sh             — Start backend (macOS/Linux)
├── start.bat            — Start backend (Windows)
├── requirements.txt     — Python dependencies
└── README.md
```

---

## 🔧 Troubleshooting

**Backend won't start**
```bash
python3 --version          # needs 3.9+
.venv/bin/pip install -r requirements.txt
```

**Watson tab doesn't appear in Burp**
- Confirm `extension/watson-burp.jar` exists
- Burp → Extensions → check the Output / Errors tabs
- Burp needs Java 17+ — check via Burp → Help → Diagnostics

**Test the connection** — Watson → Intelligence → ⚙ Settings → Test Connection

**AI errors / timeouts**
- Gemini free tier: 15 req/min limit. Under heavy fuzzing, switch to `openai` + `gpt-4.1-mini`
- Claude: ensure `ANTHROPIC_API_KEY` is set in `.env`

**Wrong provider loading**
- Restart the backend after changing `AI_PROVIDER` in `.env`
- The `GET /health` endpoint shows the active provider: `http://127.0.0.1:8000/health`

**Port conflict**
```bash
# Run on a different port:
.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8001
# Then update Settings → Backend URL → http://127.0.0.1:8001/analyze
```

**Missing provider package**
```bash
.venv/bin/pip install anthropic          # for Claude
.venv/bin/pip install google-generativeai  # for Gemini
```

---

## 🛡️ Ethics & Legal

Watson is built for **authorised security testing only**. Only run it against targets you have explicit written permission to test.

The fuzzer includes a 50ms rate limiter per 10 requests. Use responsibly.

---

## 📄 License

MIT
