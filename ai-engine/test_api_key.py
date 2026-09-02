"""
test_api_key.py
Focused test for API Key authentication on the /bootstrap endpoint.
Run: .\\venv\\Scripts\\python.exe test_api_key.py
"""
import io
from PIL import Image
from main import app, AI_API_KEY
from fastapi.testclient import TestClient

client = TestClient(app)

# ── Create a small dummy image for upload ─────────────────────────────────────
def make_dummy_image():
    img = Image.new('RGB', (64, 64), color='red')
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()

img_bytes = make_dummy_image()

PASS = "[PASS]"
FAIL = "[FAIL]"

print("=" * 55)
print("  AuthArt AI Engine — API Key Auth Test")
print("=" * 55)
print(f"  Loaded API Key from .env: {AI_API_KEY[:8]}...{AI_API_KEY[-4:]}")
print("=" * 55)

all_passed = True

# ── TEST 1: No API key at all ─────────────────────────────────────────────────
print("\nTEST 1: Request with NO API key header")
r = client.post("/bootstrap", files={"file": ("art.jpg", img_bytes, "image/jpeg")})
if r.status_code == 403:
    print(f"  {PASS} Status: {r.status_code} | Detail: {r.json()['detail']}")
else:
    print(f"  {FAIL} Expected 403, got {r.status_code} | Body: {r.text}")
    all_passed = False

# ── TEST 2: Empty API key value ───────────────────────────────────────────────
print("\nTEST 2: Request with EMPTY API key (X-API-Key: )")
r = client.post("/bootstrap",
    headers={"X-API-Key": ""},
    files={"file": ("art.jpg", img_bytes, "image/jpeg")})
if r.status_code == 403:
    print(f"  {PASS} Status: {r.status_code} | Detail: {r.json()['detail']}")
else:
    print(f"  {FAIL} Expected 403, got {r.status_code} | Body: {r.text}")
    all_passed = False

# ── TEST 3: Wrong API key ─────────────────────────────────────────────────────
print("\nTEST 3: Request with WRONG API key")
r = client.post("/bootstrap",
    headers={"X-API-Key": "totally-wrong-key-12345"},
    files={"file": ("art.jpg", img_bytes, "image/jpeg")})
if r.status_code == 403:
    print(f"  {PASS} Status: {r.status_code} | Detail: {r.json()['detail']}")
else:
    print(f"  {FAIL} Expected 403, got {r.status_code} | Body: {r.text}")
    all_passed = False

# ── TEST 4: Almost-correct key (1 char off) ───────────────────────────────────
print("\nTEST 4: Request with ALMOST correct API key (1 char modified)")
tampered_key = AI_API_KEY[:-1] + ("0" if AI_API_KEY[-1] != "0" else "1")
r = client.post("/bootstrap",
    headers={"X-API-Key": tampered_key},
    files={"file": ("art.jpg", img_bytes, "image/jpeg")})
if r.status_code == 403:
    print(f"  {PASS} Status: {r.status_code} | Detail: {r.json()['detail']}")
else:
    print(f"  {FAIL} Expected 403, got {r.status_code} | Body: {r.text}")
    all_passed = False

# ── TEST 5: Correct API key ───────────────────────────────────────────────────
print("\nTEST 5: Request with CORRECT API key")
r = client.post("/bootstrap",
    headers={"X-API-Key": AI_API_KEY},
    files={"file": ("art.jpg", img_bytes, "image/jpeg")})
if r.status_code == 200:
    body = r.json()
    print(f"  {PASS} Status: {r.status_code} | Added ID: {body['added_id']}")
else:
    print(f"  {FAIL} Expected 200, got {r.status_code} | Body: {r.text}")
    all_passed = False

# ── TEST 6: Confirm /analyze does NOT require API key ─────────────────────────
print("\nTEST 6: /analyze endpoint works WITHOUT any API key")
r = client.post("/analyze", files={"file": ("art.jpg", img_bytes, "image/jpeg")})
if r.status_code == 200:
    print(f"  {PASS} Status: {r.status_code} | /analyze is publicly accessible")
else:
    print(f"  {FAIL} Expected 200, got {r.status_code} | Body: {r.text}")
    all_passed = False

# ── TEST 7: Confirm /predict-price does NOT require API key ───────────────────
print("\nTEST 7: /predict-price endpoint works WITHOUT any API key")
r = client.post("/predict-price", files={"file": ("art.jpg", img_bytes, "image/jpeg")})
if r.status_code == 200:
    price = r.json()
    print(f"  {PASS} Status: {r.status_code} | Estimated: {price['estimatedPriceETH']} ETH")
else:
    print(f"  {FAIL} Expected 200, got {r.status_code} | Body: {r.text}")
    all_passed = False

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
if all_passed:
    print("  ALL 7 API KEY TESTS PASSED")
else:
    print("  SOME TESTS FAILED - Review output above")
print("=" * 55)
