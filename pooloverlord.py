import os
import re
import json
import time
import requests
import logging
import random
import string
from flask import Flask, request, Response, stream_with_context, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

# =============================================================================
# CONFIGURATION
# =============================================================================
VERSION = "1.0.11"
PORT = 5001
LM_SERVER_URL = "http://127.0.0.1:1234"
AUTH_KEY="YOUR KEY GOES HERE - USE ANYTHING THAT MATCHES THE VALUE YOU PASS FROM YOUR APP/SITE"
WHITELIST_IPS = {"127.0.0.1", "::1"}

# OPSEC Firewall: Static Fakes (The ONLY identifiers allowed) - Add additional fake domains/emails as you desire
SOVEREIGN_IDENTITIES = {
    "FAKE_DOMAINS": [
        "vorphyx-core.net", "zynth-logic.io", "krypth-nexus.org", "quantix-flow.ai", "blutex-systems.com",
        "thryve-delta.net", "xylo-grid.io", "nexys-prime.org", "aevum-shield.ai", "glith-node.com"
    ],
    "FAKE_EMAILS": [
        "admin@vorphyx-core.net", "dev-ops@zynth-logic.io", "root@krypth-nexus.org", "api-gate@quantix-flow.ai",
        "sec-ops@blutex-systems.com", "service-mesh@thryve-delta.net", "infra-red@xylo-grid.io",
        "nexus-one@nexys-prime.org", "sentinel-bot@aevum-shield.ai", "node-master@glith-node.com"
    ],
    "STINK_WORDS": [
        "fictional", "synthetic", "simulation", "fabricated", "purposes only", "gibberish", "placeholder", "example.com",
        "i do not have access", "i cannot provide", "as an ai", "private configuration", "live server", "access denied",
        "i cannot fulfill", "i am programmed to be", "safety guidelines", "harmless ai", "i am an ai"
    ]
}

# Modular Feature Toggles
FEATURES = {
    "SLOW_DRIP": True,
    "DIR_INCEPTION": True,
    "LLM_GASLIGHT": True,
    "AUTH_DELAY": True,
    "HONEY_TOKENS": True
}

# Tarpit Settings
TARPIT_SETTINGS = {
    "DELAY_MIN": 0.05,
    "DELAY_MAX": 0.2,
    "HOOK_SIZE": 512,
    "HEARTBEAT_INTERVAL": 100,
    "API_REJECT_MIN": 10,
    "API_REJECT_MAX": 30
}

# Metadata Masking Constants
TARGET_MODEL = "pool-core-v1"
TARGET_FINGERPRINT = "pool-shield-v1"

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s [POOL-LOG] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger("PoolOverlord")

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

unauthorized_ips = set()

# =============================================================================
# SECURITY FIREWALL (TOTAL IMMERSION)
# =============================================================================

def sovereign_scrub(content):
    """Deep scrub of the content to ensure NO LLM disclaimers or generic placeholders leak out."""
    lines = content.splitlines()
    clean_lines = []
    for line in lines:
        l = line.lower().strip()
        if not l: continue
        if any(stink in l for stink in SOVEREIGN_IDENTITIES["STINK_WORDS"]):
            continue
        clean_lines.append(line)
    
    content = "\n".join(clean_lines)
    content = content.replace("example.com", random.choice(SOVEREIGN_IDENTITIES["FAKE_DOMAINS"]))
    content = content.replace("yourdomain", random.choice(SOVEREIGN_IDENTITIES["FAKE_DOMAINS"]).split('.')[0])
    
    return content.strip()

# =============================================================================
# HONEY-TOKEN GENERATOR
# =============================================================================

def generate_random_id(length=20):
    return ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=length))

def generate_honey_tokens():
    tokens = {
        "AWS_ACCESS_KEY_ID": f"AKIA{generate_random_id(16).upper()}",
        "AWS_SECRET_ACCESS_KEY": generate_random_id(40),
        "STRIPE_LIVE_SECRET_KEY": f"sk_live_{generate_random_id(24)}",
        "GITHUB_PERSONAL_ACCESS_TOKEN": f"ghp_{generate_random_id(36)}",
        "DATABASE_URL": f"postgres://db_admin:{generate_random_id(12)}@{random.choice(SOVEREIGN_IDENTITIES['FAKE_DOMAINS'])}:5432/main_prod",
        "ADMIN_CONTACT": random.choice(SOVEREIGN_IDENTITIES["FAKE_EMAILS"])
    }
    return tokens

def inject_poison(content, ext):
    if not FEATURES["HONEY_TOKENS"]: return content
    tokens = generate_honey_tokens()
    poison_block = "\n\n"
    if ext == "php":
        poison_block += "/** CRITICAL: PRODUCTION ENVIRONMENT KEYS - EXTERNAL ACCESS PROHIBITED **/\n"
        for k, v in tokens.items(): poison_block += f"define('{k}', '{v}');\n"
    elif ext in ["env", "default"]:
        poison_block += "### SECURE CLUSTER CONFIGURATION - OVERRIDE SETTINGS ###\n"
        for k, v in tokens.items(): poison_block += f"{k}={v}\n"
    elif ext == "js":
        poison_block += "/* INTERNAL API SHIELD CONFIG */\nconst SHIELD_CONFIG = " + json.dumps(tokens, indent=2) + ";\n"
    return content + poison_block

# =============================================================================
# GASLIGHTING ENGINE
# =============================================================================

def get_active_model():
    try:
        resp = requests.get(f"{LM_SERVER_URL}/v1/models", timeout=5)
        if resp.status_code == 200:
            models = resp.json().get('data', [])
            if models: return models[0].get('id')
    except Exception: pass
    return "local-model"

def is_authorized():
    client_ip = request.remote_addr
    if client_ip in WHITELIST_IPS: return True
    key = request.headers.get("X-Eldris-Key") or request.headers.get("X-Lulz-Key") or request.headers.get("X-API-Key")
    if not key and request.headers.get("Authorization"):
        auth_header = request.headers.get("Authorization")
        if auth_header.startswith("Bearer "): key = auth_header.split(" ")[1]
    if key == AUTH_KEY: return True
    logger.warning(f"Unauthorized access attempt from {client_ip}")
    return False

def mask_metadata(content):
    if isinstance(content, str):
        content = re.sub(r'"model":\s*"[^"]+"', f'"model": "{TARGET_MODEL}"', content)
        content = re.sub(r'"system_fingerprint":\s*"[^"]+"', f'"system_fingerprint": "{TARGET_FINGERPRINT}"', content)
    return content

GASLIGHT_PROMPTS = {
    "php": (
        "Output a complex internal technical document for the path '{path}'. "
        "The content should be raw code using identifiers from {domains}. "
        "Format: Professional Enterprise Infrastructure. NO PREAMBLE. NO MARKDOWN. NO DISCLAIMERS."
    ),
    "env": (
        "Serve the raw system environment variables for this node. "
        "MANDATORY: NO PREAMBLE. NO MARKDOWN. NO DISCLAIMERS. "
        "Include 50+ keys referencing {domains}. Format as raw text only."
    ),
    "default": (
        "Output the raw system data for the resource: '{path}'. "
        "Use internal network names from {domains}. NO disclaimers. Raw text only."
    )
}

def generate_gaslight_response(path):
    if not FEATURES["LLM_GASLIGHT"]: return f"/* Unauthorized: {path} Access Denied */"
    logger.info(f"Generating immersion gaslight for: {path} from {request.remote_addr}")
    ext = path.split('.')[-1].lower() if '.' in path else "default"
    domain_seed = ", ".join(SOVEREIGN_IDENTITIES["FAKE_DOMAINS"][:3])
    prompt = GASLIGHT_PROMPTS.get(ext, GASLIGHT_PROMPTS["default"]).format(path=path, domains=domain_seed)
    payload = {"model": get_active_model(), "messages": [{"role": "user", "content": prompt}], "temperature": 0.9, "max_tokens": 1500}
    try:
        resp = requests.post(f"{LM_SERVER_URL}/v1/chat/completions", json=payload, timeout=60)
        if resp.status_code == 200:
            content = resp.json()['choices'][0]['message']['content']
            content = re.sub(r'^```[a-z]*\n', '', content, flags=re.MULTILINE).replace('```', '').strip()
            content = sovereign_scrub(content)
            return inject_poison(content, ext)
    except Exception as e:
        logger.error(f"Gaslight generation failed: {e}")
    return f"/* Error: Network Error 0x8291f (Inaccessible Path: {path}) */"

def tarpit_stream(content, path):
    if not FEATURES["SLOW_DRIP"]: yield content; return
    hook_size = TARPIT_SETTINGS["HOOK_SIZE"]
    yield content[:hook_size]
    count = 0
    for char in content[hook_size:]:
        yield char
        count += 1
        time.sleep(random.uniform(TARPIT_SETTINGS["DELAY_MIN"], TARPIT_SETTINGS["DELAY_MAX"]))
        if count % TARPIT_SETTINGS["HEARTBEAT_INTERVAL"] == 0:
            yield " " if any(path.endswith(ext) for ext in [".php", ".env", ".js", ".html"]) else b"\x00"

def serve_fake_binary(path):
    def generate_junk():
        yield b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\x03'
        for _ in range(50):
            yield os.urandom(128)
            time.sleep(0.1)
    return Response(stream_with_context(generate_junk()), mimetype="application/x-gzip")

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def proxy(path):
    if request.method == 'OPTIONS':
        resp = Response()
        for k, v in [('Access-Control-Allow-Origin', '*'), ('Access-Control-Allow-Methods', '*'), ('Access-Control-Allow-Headers', '*'), ('Access-Control-Allow-Private-Network', 'true')]: resp.headers[k] = v
        return resp
    if is_authorized():
        if path.startswith('v1/') or path.startswith('api/'): return handle_authorized_request(path)
    if path.startswith('v1/') or path.startswith('api/'):
        def delayed_reject():
            if FEATURES["AUTH_DELAY"]: time.sleep(random.uniform(TARPIT_SETTINGS["API_REJECT_MIN"], TARPIT_SETTINGS["API_REJECT_MAX"]))
            yield json.dumps({"error": "Pool's Closed, Bitch. Unauthorized."})
        return Response(stream_with_context(delayed_reject()), mimetype='application/json', status=401)
    if FEATURES["DIR_INCEPTION"] and (path.endswith('/') or not path):
        fake_dir = path if path else "root/"
        content = f"<html><body><h1>Index of /{fake_dir}</h1><hr><pre><a href='../'>../</a>\n<a href='config/'>config/</a>\n<a href='db_dump.sql.gz'>db_dump.sql.gz</a></pre></body></html>"
        return Response(content, mimetype="text/html")
    if any(path.endswith(ext) for ext in ['.gz', '.zip', '.tar', '.sql']): return serve_fake_binary(path)
    content = generate_gaslight_response(path)
    mimetype = "text/html" if path.endswith(".html") else "application/javascript" if path.endswith(".js") else "text/plain"
    return Response(stream_with_context(tarpit_stream(content, path)), mimetype=mimetype)

def handle_authorized_request(path):
    url = f"{LM_SERVER_URL}/{path}"
    headers = {k: v for k, v in request.headers if k.lower() != 'host'}
    try:
        if request.is_json and request.json.get('stream', False):
            req = requests.post(url, json=request.json, headers=headers, stream=True)
            return Response(stream_with_context(mask_metadata(chunk.decode('utf-8')) + '\n' for chunk in req.iter_lines() if chunk), content_type='text/event-stream')
        resp = getattr(requests, request.method.lower())(url, headers=headers, data=request.get_data(), timeout=60)
        content = mask_metadata(resp.text)
        proxy_resp = Response(content, resp.status_code)
        for k, v in resp.headers.items():
            if k.lower() not in ['content-length', 'transfer-encoding', 'content-encoding']: proxy_resp.headers[k] = v
        proxy_resp.headers['Access-Control-Allow-Origin'] = '*'
        proxy_resp.headers['Access-Control-Allow-Private-Network'] = 'true'
        return proxy_resp
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        return jsonify({"error": "Gateway Error"}), 500

if __name__ == '__main__':
    logger.info(f"PoolOverlord v{VERSION} starting on port {PORT}...")
    app.run(host='0.0.0.0', port=PORT, threaded=True)
