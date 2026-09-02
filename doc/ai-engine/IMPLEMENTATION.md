# AuthArt AI Engine — Implementation Reference

**Project:** AuthArt — AI-Powered Decentralized NFT Art Platform  
**Component:** AI Engine (Python / FastAPI)  
**Location:** `ai-engine/`  
**Status:** ✅ Complete (All 5 Phases)

---

## Table of Contents

1. [Project Context](#1-project-context)
2. [Phase 1 — Environment Setup](#2-phase-1--environment-setup)
3. [Phase 2 — CLIP Image Embeddings](#3-phase-2--clip-image-embeddings)
4. [Phase 3 — ChromaDB Vector Database](#4-phase-3--chromadb-vector-database)
5. [Phase 4 — ResNet50 CNN Style Fingerprinting](#5-phase-4--resnet50-cnn-style-fingerprinting)
6. [Phase 5 — Auth, Validation & Price Prediction](#6-phase-5--auth-validation--price-prediction)
7. [API Reference](#7-api-reference)
8. [Scoring Logic](#8-scoring-logic)
9. [File Structure](#9-file-structure)
10. [Running & Testing](#10-running--testing)

---

## 1. Project Context

The original `main.py` was a **29-line placeholder** that used SHA-256 hashing to generate fake, random originality scores. It had no real machine learning, no database, and no security.

**Starting state:**
```python
def fallback(data: bytes):
    h = hashlib.sha256(data).hexdigest()
    n = int(h[:8], 16)
    sim = 0.05 + (n % 8500) / 10000  # Fake random number!
    return {'original': sim <= 0.985, 'model': 'fallback; replace with CLIP/CNN weights', ...}
```

**Ending state:** A fully functional ML microservice with dual-model analysis, vector database, API key security, input validation, and price prediction — **verified by 6 automated tests.**

---

## 2. Phase 1 — Environment Setup

**Goal:** Install all required Machine Learning dependencies.

### What was done

Created `requirements.txt` with all necessary Python packages:

```text
fastapi
uvicorn
python-multipart
torch
torchvision
transformers
pillow
chromadb
python-dotenv
```

### Commands used

```powershell
# Create virtual environment
python -m venv venv

# Activate
.\venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
```

### Key packages

| Package | Version Installed | Purpose |
|---|---|---|
| `torch` | 2.14.0 | Deep learning framework |
| `torchvision` | 0.29.0 | Pre-trained CNN models |
| `transformers` | 5.17.0 | HuggingFace models (CLIP) |
| `fastapi` | 0.141.1 | API framework |
| `chromadb` | 1.5.9 | Vector database |
| `pillow` | 12.3.0 | Image processing |
| `python-dotenv` | 1.2.3 | Environment variable loader |

### Issues resolved

- First attempt used pinned versions (e.g., `torch==2.2.1`) which failed because PyTorch had newer versions only. Switched to unpinned versions so pip resolves automatically.

---

## 3. Phase 2 — CLIP Image Embeddings

**Goal:** Replace the fake hash math with real image embeddings using a pre-trained CLIP model.

### What is CLIP?

CLIP (Contrastive Language-Image Pretraining) is a model trained by OpenAI on 400 million image-text pairs. It converts images into mathematical vectors (embeddings) that capture semantic content — **what the image is about**.

### Model used

```
openai/clip-vit-base-patch32
```
- Loaded from HuggingFace Hub on server startup
- Outputs a **512-dimensional embedding** per image
- Auto-downloads and caches weights (~350 MB) on first run

### Implementation

```python
from transformers import CLIPProcessor, CLIPModel

clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)

def get_clip_embedding(image: Image.Image):
    inputs = clip_processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = clip_model.get_image_features(**inputs)
        # Handle different output types across transformers versions
        if hasattr(outputs, 'pooler_output'):
            image_features = outputs.pooler_output
        elif isinstance(outputs, torch.Tensor):
            image_features = outputs
        else:
            image_features = outputs[0]
    # L2 normalization for cosine similarity
    image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
    return image_features.cpu().numpy().tolist()[0]
```

### Issues resolved

- `model(**inputs)` returned a `BaseModelOutputWithPooling` object instead of a tensor. Fixed by calling `model.get_image_features(**inputs)` instead and adding a type check to handle both tensor and object outputs.
- `model(**inputs)` also required `input_ids` (text inputs). `get_image_features` only needs image inputs.

---

## 4. Phase 3 — ChromaDB Vector Database

**Goal:** Store embeddings of known artworks and perform real cosine similarity search against them.

### What is ChromaDB?

ChromaDB is an open-source embedded vector database. It stores high-dimensional vectors and can find the nearest neighbors efficiently using approximate nearest neighbor (ANN) search.

### Configuration

```python
import chromadb

chroma_client = chromadb.PersistentClient(path="./.chroma")

# Collection for CLIP content embeddings
collection_clip = chroma_client.get_or_create_collection(
    name="artworks",
    metadata={"hnsw:space": "cosine"}  # Use cosine similarity metric
)

# Collection for CNN style embeddings
collection_style = chroma_client.get_or_create_collection(
    name="artworks_style",
    metadata={"hnsw:space": "cosine"}
)
```

- `PersistentClient` stores data in `.chroma/` directory — **survives server restarts**
- `hnsw:space: cosine` configures cosine distance (0 = identical, 1 = completely different)

### Distance to Similarity Conversion

```python
# ChromaDB returns cosine distance (0 = same, 1 = different)
# We convert to similarity (0 = different, 1 = same)
similarity = 1.0 - distance
```

### Bootstrapping Workflow

To populate the database, call `POST /bootstrap` with an image file.  
This saves both the CLIP and CNN embeddings to their respective collections.

### New `/bootstrap` endpoint added

```
POST /bootstrap
Body: multipart image file
```

### Issues resolved

- ChromaDB's `.delete(where={})` raises `ValueError` in newer versions. Fixed by fetching all IDs first and deleting by explicit IDs:
  ```python
  ids = collection.get()['ids']
  if ids:
      collection.delete(ids=ids)
  ```

### Verified

- Empty DB → `originalityScore: 1.0` (no matches found)
- After bootstrap → same image gives `originalityScore: 0.0`, `fraudAlert: True`

---

## 5. Phase 4 — ResNet50 CNN Style Fingerprinting

**Goal:** Add a second model that analyzes the *artistic style* of the image — independent of subject matter.

### Why a second model?

CLIP is excellent at understanding what an image contains, but it is not specifically trained for artistic style. Two artworks can have the same subject but be in completely different styles (e.g., a cat painted in oil vs. a cat in pixel art). ResNet captures textures, brushstrokes, and color patterns.

### Model used

```
torchvision.models.resnet50 (ImageNet pretrained)
```

### Key technique — Removing the classification head

ResNet-50 is normally a classifier. We remove its final layer to expose the raw **2048-dimensional feature map** it uses internally before predicting a class:

```python
from torchvision import models
import torch.nn as nn

resnet = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
resnet = nn.Sequential(*list(resnet.children())[:-1])  # Remove last layer
resnet.eval()
```

### Image preprocessing

ResNet requires specific ImageNet normalization:

```python
style_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])
```

### Embedding extraction

```python
def get_style_embedding(image: Image.Image):
    input_tensor = style_transform(image).unsqueeze(0).to(device)  # Add batch dim
    with torch.no_grad():
        features = resnet(input_tensor)    # Shape: [1, 2048, 1, 1]
    features = torch.flatten(features, 1)  # Shape: [1, 2048]
    features = features / features.norm(p=2, dim=-1, keepdim=True)  # Normalize
    return features.cpu().numpy().tolist()[0]
```

### Dual collection storage

Both embeddings are stored together under the **same UUID** at bootstrap time, keeping them synchronized:

```python
doc_id = str(uuid.uuid4())
collection_clip.add(embeddings=[clip_emb], documents=[filename], ids=[doc_id])
collection_style.add(embeddings=[style_emb], documents=[filename], ids=[doc_id])
```

### Score blending

```python
combined_sim = (sim_clip * 0.70) + (sim_style * 0.30)
```

Content (CLIP) is weighted at **70%** because it is a stronger general model. Style (ResNet) adds a **30%** refinement for artistic fingerprinting.

---

## 6. Phase 5 — Auth, Validation & Price Prediction

### 6a. API Key Authentication

**Problem:** The `/bootstrap` endpoint is write-access to the database. Without protection, anyone could flood it with fake data.

**Solution:** Server-to-server API Key header (`X-API-Key`).

The key is generated once, stored in `.env`, and shared with the Node.js backend (which is the only legitimate caller of `/bootstrap`). **It never reaches the browser.**

#### Architecture

```
Browser (React)
      |  JWT (user identity)
      v
Node.js Backend (port 5000)
      |  X-API-Key (server secret)
      v
Python AI Engine (port 8000)
```

#### Implementation

```python
from fastapi.security.api_key import APIKeyHeader
from fastapi import Security, Depends

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def require_api_key(api_key: str = Security(API_KEY_HEADER)):
    if api_key != AI_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key.")
    return api_key

@app.post('/bootstrap', dependencies=[Depends(require_api_key)])
async def bootstrap(...):
    ...
```

#### Key generation

```python
import secrets
secrets.token_hex(32)
# Output: de25e7ef96f5331994a5509ba778db561649ead8eef926e0492f3916542d6e8e
```

Stored in `ai-engine/.env`:
```env
AI_API_KEY=de25e7ef96f5331994a5509ba778db561649ead8eef926e0492f3916542d6e8e
```

---

### 6b. Input Validation

Applied to both `/analyze` and `/bootstrap` before any ML processing:

```python
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

def validate_image(data: bytes, content_type: str) -> Image.Image:
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(400, f"Unsupported file type '{content_type}'.")
    if len(data) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(400, f"File too large.")
    try:
        image = Image.open(io.BytesIO(data)).convert("RGB")
        image.verify()   # Detect corrupt/truncated files
        image = Image.open(io.BytesIO(data)).convert("RGB")  # Re-open after verify
        return image
    except Exception:
        raise HTTPException(400, "File is not a valid or readable image.")
```

> **Note:** Pillow's `.verify()` consumes the file handle, so the image must be re-opened after calling it.

---

### 6c. Price Prediction (`/predict-price`)

Since no real NFT sales dataset is available, a transparent rule-based estimator is used.

#### Formula

```
Base Price          = 0.05 ETH
Originality Bonus   = originality_score × 0.5  (max +0.5 ETH for fully original)
Similarity Penalty  = sim_clip × 0.03           (max -0.03 ETH for near-copy)
Style Bonus         = +0.05 ETH if sim_style < 0.3 (very unique style)

Estimated Price = Base + Bonus - Penalty + StyleBonus
Clamped to [0.01, 1.0] ETH
```

#### Sample response

```json
{
  "estimatedPriceETH": 0.0717,
  "priceUSD": 229.4,
  "breakdown": {
    "basePrice": 0.05,
    "originalityBonus": 0.0497,
    "similarityPenalty": 0.028,
    "styleBonus": 0.0
  },
  "originalityScore": 0.641,
  "model": "rule-based v1",
  "disclaimer": "Estimated price only. Actual market value may differ."
}
```

---

## 7. API Reference

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | None | Server health check + DB record count |
| `POST` | `/analyze` | None | Analyze image for originality |
| `POST` | `/bootstrap` | `X-API-Key` | Add artwork to vector database |
| `POST` | `/predict-price` | None | Estimate ETH price for artwork |

### `/analyze` Response Schema

```json
{
  "original": true,
  "similarityScore": 0.12,
  "styleFingerprintScore": 0.08,
  "originalityScore": 0.88,
  "fraudAlert": false,
  "model": "clip + resnet50 + chromadb",
  "sha256": "8e27b3..."
}
```

---

## 8. Scoring Logic

```
Step 1: Generate CLIP embedding (512-d) → query artworks collection
Step 2: Generate ResNet50 embedding (2048-d) → query artworks_style collection
Step 3: Convert cosine distances to similarities
          sim = 1.0 - distance
Step 4: Blend scores
          combined = (sim_clip × 0.70) + (sim_style × 0.30)
Step 5: Apply fraud threshold
          fraudAlert = combined > 0.95
Step 6: Compute final originality score
          originalityScore = 1.0 - combined
```

**Empty DB behavior:** When the database has no records, all distances default to `0.0`, so `originalityScore = 1.0` (treated as fully original).

---

## 9. File Structure

```
ai-engine/
├── main.py              ← FastAPI app — all endpoints and ML logic
├── test_inference.py    ← Automated test suite (6 tests)
├── requirements.txt     ← Python dependencies
├── .env                 ← Secret API key (NOT committed to git)
├── .env.example         ← Template for .env
├── debug_clip.py        ← Development debug script (can be deleted)
├── README.md            ← Technical documentation
├── venv/                ← Python virtual environment (NOT committed)
└── .chroma/             ← ChromaDB persistent storage (auto-generated)
```

---

## 10. Running & Testing

### Start the server

```powershell
cd ai-engine
.\venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

First run downloads model weights (~450 MB total). Subsequent runs load from cache instantly.

### Run automated tests

```powershell
.\venv\Scripts\python.exe test_inference.py
```

Expected output:
```
=== TEST 1: API KEY AUTH ===
  [PASS] No API key -> 403 Forbidden
  [PASS] Wrong API key -> 403 Forbidden

=== TEST 2: INPUT VALIDATION ===
  [PASS] PDF rejected -> 400
  [PASS] Oversized file -> 400
  [PASS] Corrupt image -> 400

=== TEST 3: ANALYZE WITH EMPTY DB ===
  [PASS] Empty DB -> original=True, originalityScore=1.0

=== TEST 4: BOOTSTRAP ===
  [PASS] Bootstrap -> success

=== TEST 5: FRAUD DETECTION ===
  [PASS] Duplicate image -> fraudAlert=True, originalityScore=0.0

=== TEST 6: PRICE PREDICTION ===
  [PASS] Price prediction: 0.07 ETH

[ALL TESTS PASSED]
```

### Populate the database with sample images

```powershell
# Example: bootstrap a real image via curl
curl -X POST http://localhost:8000/bootstrap \
  -H "X-API-Key: your-api-key-here" \
  -F "file=@path/to/sample_art.jpg"
```

---

## Summary of All Phases

| Phase | Feature | Status |
|---|---|---|
| 1 | Environment setup (venv, pip, requirements.txt) | Done |
| 2 | CLIP model (HuggingFace Transformers, 512-d embedding) | Done |
| 3 | ChromaDB vector database (cosine similarity search) | Done |
| 4 | ResNet50 CNN style fingerprinting (2048-d embedding) | Done |
| 5a | API Key auth on `/bootstrap` (python-dotenv + FastAPI Security) | Done |
| 5b | Input validation (file type, size, corrupt image) | Done |
| 5c | Price prediction `/predict-price` (rule-based estimator) | Done |
| — | Bootstrap with real NFT dataset | Not done (requires dataset) |
| — | `/mint` webhook to auto-register after minting | Not done |
