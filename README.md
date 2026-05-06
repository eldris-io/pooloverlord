# PoolOverlord v1.0.11

**PoolOverlord** is a modular security proxy and "Digital Tarpit" designed to shield local LLM instances (LM Studio, Ollama) from unauthorized access, credential harvesters, and automated scanners.

It provides a high-fidelity gaslighting engine and "Hook & Squeeze" latency traps to waste attacker resources while maintaining a professional facade.

## 🛡️ Core Features (v1.0.11)

- **Digital Gaslighting (LLM-Driven)**: Unauthorized requests for common vulnerability paths (e.g., `wp-config.php`, `.env`) are routed to your local LLM. It "hallucinates" high-entropy, enterprise-grade decoys that look 100% real but are logically non-functional.
- **Hook & Squeeze (Tarpit)**: Implements byte-level latency. Scanners receive an initial burst of data to prevent connection timeouts, followed by a character-by-character "drip" that can hold a connection open for minutes.
- **Identity Firewall (Total Immersion)**: Automatically scrubs "AI-isms" (e.g., "As an AI language model") from decoy responses. Replaces generic placeholders with high-entropy identifiers from the **Gibberish Library**.
- **Honey-Token Poisoning**: Injects fake AWS keys, Stripe tokens, and Database URLs into generated decoys to trigger automated alerts when used by attackers.
- **Recursive Directory Inception**: Traps scanners in infinite "Index of /" loops with fake file listings.
- **AI Studio Integration**: Full Private Network Access (PNA) and CORS compliance for seamless use with Google AI Studio via Tailscale Funnel.
- **Metadata Masking**: Hides your backend architecture by spoofing `model` and `system_fingerprint` identifiers.

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.11+**
- **LM Studio** (server active on port `1234`)
- **Tailscale Funnel** (routing to port `5001`)

### 2. Installation
```bash
git clone https://github.com/eldris-io/pooloverlord
cd PoolOverlord
pip install -r requirements.txt
```

### 3. Configuration
Edit the configuration block in `PoolOverlord.py`:
- `AUTH_KEY`: Set your master secret.
- `SOVEREIGN_IDENTITIES`: Customize your decoy domain and email libraries.
- `FEATURES`: Toggle modular defensive layers (Slow Drip, Gaslight, Honey Tokens).

### 4. Running
```bash
python3 PoolOverlord.py
```

## 🧪 Testing the Defense

### Simulate a Scanner (GET)
To see the tarpit and gaslighting engine in action, request a sensitive file via the Tailscale Funnel without an API key:
```bash
curl https://your-funnel-url.ts.net/v1/.env
```
*Result: An 18-second connection hang followed by a poisoned, realistic decoy.*

### Unauthorized API Access (POST)
Test the randomized API rejection delay (10-30s) by hitting the chat endpoint with no auth:
```bash
curl -X POST https://your-funnel-url.ts.net/v1/chat/completions -d '{"messages": [{"role": "user", "content": "hello"}]}'
```

## 📜 License
MIT
