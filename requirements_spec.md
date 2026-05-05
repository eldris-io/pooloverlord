# Requirements: PoolOverlord (Acheron Refactor)

## 1. Overview
PoolOverlord is a Python-based security proxy and "tarpit" designed to sit between a local LLM instance (LM Studio/Ollama) and external clients (Google AI Studio, Web Servers, Apps, etc). It provides authentication, CORS compliance, and a "tarpit" to grief unauthorized automated scans.

## 2. Core Functional Requirements

### 2.1 The Gateway (Authorized Traffic)
- **Request Forwarding**: Proxy authorized `POST` and `GET` requests to the local LLM backend (Default: `127.0.0.1:1234`).
- **Streaming Support**: Must support Server-Sent Events (SSE) for real-time streaming in the AI Studio UI.
- **JSON Sanitation**: For non-streaming requests, aggressively strip LLM "slop" (Markdown code blocks, preamble text) using regex and brace-slicing to ensure raw JSON is delivered to the client.
- **Metadata Masking**: Intercept model metadata and response bodies to replace actual model names/fingerprints with `pool-core-v1` and `pool-shield-v1`.

### 2.2 The Tarpit (Unauthorized Traffic)
- **Branching Logic**:
    - **API Rejection**: Unauthorized requests to `/v1/` paths must return a **static 401 JSON** immediately (`{"error": "Pool's Closed. Unauthorized."}`). No LLM compute should be used.
    - **File Gaslighting**: Unauthorized requests to non-API paths (e.g., `/.env`, `/wp-login.php`) invoke the local LLM to generate a realistic but hallucinated "file" to waste the attacker's time.
- **State Tracking**: Maintain an in-memory set of unauthorized IPs to track "participants" in the tarpit.

### 2.3 Authentication & Access Control
- **Multi-Header Support**: Authenticate via `X-Lulz-Key`, `Authorization: Bearer <key>`, or `X-API-Key`.
- **IP Whitelisting**: Allow defined IPs (e.g., `127.0.0.1`) to bypass authentication checks for local debugging.
- **CORS & Private Network Access**: Implement full CORS headers and `Access-Control-Allow-Private-Network: true` to satisfy browser security requirements when calling from a public domain (AI Studio).

## 3. Technical Requirements
- **JSON-Only Responses**: Under no circumstances should the proxy return a standard HTML error page (404/500). All Flask errors must be caught and returned as JSON.
- **Management Endpoint**: Provide a `/management/pool/clear` route to reset the tarpit state.
- **Logging**: Implement thematic logging (`[POOL-LOG]`) with verbose diagnostics for unauthorized attempts (key length, headers received).

## 4. Operational Requirements
- **Versioning**: Maintain a `VERSION` constant in the script.
- **Configuration**: Use a dedicated, clearly commented block at the top of the script for `AUTH_KEY`, `LM_SERVER_URL`, and `PORT`.
- **No Dependencies (Minimalist)**: Rely primarily on `Flask` and `requests`.