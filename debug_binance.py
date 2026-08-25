import os, sys, urllib.request, urllib.parse, urllib.error, hashlib, hmac, time, json
sys.path.insert(0, r"e:\AUTOMAÇÃO IA\TRADING AI")
from dotenv import load_dotenv
load_dotenv(r"e:\AUTOMAÇÃO IA\TRADING AI\.env")

api_key = os.getenv("BINANCE_TESTNET_API_KEY", "").strip().strip('"')
api_secret = os.getenv("BINANCE_TESTNET_SECRET", "").strip().strip('"')

BASE = "https://demo-fapi.binance.com"

print(f"Key length: {len(api_key)} | Secret length: {len(api_secret)}")
print(f"Key: {api_key[:8]}...{api_key[-4:]}")

# Server time vs local time
try:
    r = urllib.request.urlopen(f"{BASE}/fapi/v1/time", timeout=10)
    srv = json.loads(r.read())["serverTime"]
    local = int(time.time() * 1000)
    diff = local - srv
    print(f"Server time: {srv} | Local: {local} | Diff: {diff}ms")
    if abs(diff) > 1000:
        print(f"[WARN] Clock skew {diff}ms — usar serverTime")
    ts = srv  # usar server time
except Exception as e:
    print(f"Server time ERRO: {e}")
    ts = int(time.time() * 1000)

# Testa account com server time + recvWindow amplo
try:
    params = f"timestamp={ts}&recvWindow=10000"
    sig = hmac.new(api_secret.encode('utf-8'), params.encode('utf-8'), hashlib.sha256).hexdigest()
    url = f"{BASE}/fapi/v2/account?{params}&signature={sig}"
    req = urllib.request.Request(url, headers={"X-MBX-APIKEY": api_key})
    r = urllib.request.urlopen(req, timeout=10)
    data = json.loads(r.read())
    usdt = next((a.get("walletBalance", a.get("balance", "?")) for a in data.get("assets", []) if a["asset"] == "USDT"), "N/A")
    print(f"[OK] Auth funcionou! USDT = {usdt}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"[FAIL] {e.code}: {body}")
    if "-1022" in body:
        print("\nProvavelmente erro no secret. Recrie a API key no site e cole manualmente.")
    elif "-2008" in body:
        print("\nAPI key inválida. Recrie a API key no site.")
