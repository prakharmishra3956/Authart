"""
Comprehensive test for AuthArt AI Engine.
Tests: API Key auth, input validation, /analyze, /bootstrap, /predict-price.
"""
import io, os
from PIL import Image
from main import app, collection_clip, collection_style, AI_API_KEY
from fastapi.testclient import TestClient

client = TestClient(app)

def make_image_bytes(color='blue', fmt='JPEG'):
    img = Image.new('RGB', (224, 224), color=color)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()

def clear_db():
    for col in [collection_clip, collection_style]:
        ids = col.get()['ids']
        if ids:
            col.delete(ids=ids)

# -- Setup -------------------------------------------------------------------
print("\n=== CLEARING DATABASE ===")
clear_db()
print("Done.\n")

# -- TEST 1: API Key Auth ----------------------------------------------------
print("=== TEST 1: API KEY AUTH ===")
img_bytes = make_image_bytes()

r = client.post("/bootstrap", files={"file": ("art.jpg", img_bytes, "image/jpeg")})
assert r.status_code == 403, f"Expected 403, got {r.status_code}"
print("  [PASS] No API key -> 403 Forbidden:", r.json()['detail'])

r = client.post("/bootstrap",
    headers={"X-API-Key": "wrong-key"},
    files={"file": ("art.jpg", img_bytes, "image/jpeg")})
assert r.status_code == 403, f"Expected 403, got {r.status_code}"
print("  [PASS] Wrong API key -> 403 Forbidden:", r.json()['detail'])

# -- TEST 2: Input Validation ------------------------------------------------
print("\n=== TEST 2: INPUT VALIDATION ===")

r = client.post("/analyze", files={"file": ("doc.pdf", b"not an image", "application/pdf")})
assert r.status_code == 400, f"Expected 400, got {r.status_code}"
print("  [PASS] PDF rejected -> 400:", r.json()['detail'])

big_data = b"x" * (11 * 1024 * 1024)
r = client.post("/analyze", files={"file": ("big.jpg", big_data, "image/jpeg")})
assert r.status_code == 400, f"Expected 400, got {r.status_code}"
print("  [PASS] Oversized file -> 400:", r.json()['detail'])

r = client.post("/analyze", files={"file": ("corrupt.jpg", b"this is not an image", "image/jpeg")})
assert r.status_code == 400, f"Expected 400, got {r.status_code}"
print("  [PASS] Corrupt image -> 400:", r.json()['detail'])

# -- TEST 3: Analyze with Empty DB -------------------------------------------
print("\n=== TEST 3: ANALYZE WITH EMPTY DB ===")
r = client.post("/analyze", files={"file": ("art.jpg", img_bytes, "image/jpeg")})
assert r.status_code == 200
result = r.json()
assert result['original'] == True
assert result['fraudAlert'] == False
assert result['originalityScore'] == 1.0
print("  [PASS] Empty DB -> original=True, originalityScore=1.0")

# -- TEST 4: Bootstrap (with valid API key) ----------------------------------
print("\n=== TEST 4: BOOTSTRAP ===")
r = client.post("/bootstrap",
    headers={"X-API-Key": AI_API_KEY},
    files={"file": ("art.jpg", img_bytes, "image/jpeg")})
assert r.status_code == 200
print("  [PASS] Bootstrap ->", r.json())

# -- TEST 5: Fraud Detection -------------------------------------------------
print("\n=== TEST 5: FRAUD DETECTION ===")
r = client.post("/analyze", files={"file": ("art.jpg", img_bytes, "image/jpeg")})
result = r.json()
assert result['original'] == False
assert result['fraudAlert'] == True
assert result['originalityScore'] == 0.0
print("  [PASS] Duplicate image -> fraudAlert=True, originalityScore=0.0")

# -- TEST 6: Price Prediction ------------------------------------------------
print("\n=== TEST 6: PRICE PREDICTION ===")
fresh_bytes = make_image_bytes(color='green')
r = client.post("/predict-price", files={"file": ("art2.jpg", fresh_bytes, "image/jpeg")})
assert r.status_code == 200
price = r.json()
assert 'estimatedPriceETH' in price
assert 0.01 <= price['estimatedPriceETH'] <= 1.0
print("  [PASS] Price prediction:")
print("         Estimated Price:", price['estimatedPriceETH'], "ETH (~$" + str(price['priceUSD']) + " USD)")
print("         Breakdown:", price['breakdown'])
print("         Disclaimer:", price['disclaimer'])

print("\n[ALL TESTS PASSED]")
