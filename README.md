# PoolOverlord

**PoolOverlord** is a Python-based security proxy and "Digital Tarpit" designed to shield local LLM instances (LM Studio, Ollama) from unauthorized access and automated scanners. 

It provides authentication, CORS/PNA compliance for Google AI Studio, and a high-fidelity gaslighting engine to grief malicious actors searching for common vulnerabilities.

## 🛡️ Core Features

- **Digital Gaslighting**: Unauthorized requests for file paths (e.g., `wp-config.php`, `.env`) trigger your local LLM to "hallucinate" convincing, high-entropy decoys. Scanners receive 100+ lines of enterprise-grade code that looks 100% real but is logically non-functional.
- **Log Protection**: Intercepts scanners before they hit your backend. Your LM Studio logs only show standard API traffic, never the raw scanner noise.
- **AI Studio Integration**: Implements Private Network Access (PNA) and CORS headers required for AI Studio to communicate with local servers over Tailscale Funnel.
- **Metadata Masking**: Intercepts and replaces model names/fingerprints with generic identifiers (`pool-core-v1`) to hide your architecture.
- **Bypass Safety Refusals**: Uses a "Synthetic Dataset" prompting strategy to ensure models generate realistic-looking credentials for decoys without triggering standard AI safety refusals.

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.12+**
- **LM Studio** (running a local server on port `1234`)
- **Tailscale Funnel** (configured to point to port `5001`)

### 2. Installation
```bash
git clone https://github.com/eldris-io/pooloverlord
cd PoolOverlord
pip install -r requirements.txt
```

### 3. Configuration
Edit the block at the top of `pooloverlord.py`:
- `AUTH_KEY`: Your secret API key (e.g., for `X-Eldris-Key`).
- `LM_SERVER_URL`: Your local backend address (default: `http://127.0.0.1:1234`).

### 4. Running
```bash
python3 pooloverlord.py
```

## 🧪 Testing the Tarpit

To see the gaslighting in action, try requesting a sensitive file through the proxy without an API key:
```bash
curl http://localhost:5001/.env
```
The proxy will wrap the request into a "Synthetic Dataset" prompt, causing your LLM to generate a realistic-looking (but fake) `.env` file, wasting the requester's time and compute.

## 📜 License
MIT
