# AuthArt AI Engine

The AI Engine is a standalone Python microservice built with **FastAPI**. It is the verification gatekeeper between a creator uploading artwork and the NFT minting process on the blockchain. No artwork can be minted unless it passes through this engine and is deemed sufficiently original.

---

## Architecture Overview

```text
Uploaded Image
      |
      v
 +-----------+       +------------+
 |   CLIP    |       | ResNet-50  |
 | Embedding |       |   Style    |
 |  (512-d)  |       | Embedding  |
 |           |       |  (2048-d)  |
 +-----------+       +------------+
      |                    |
      v                    v
+----------+        +------------+
| ChromaDB |        |  ChromaDB  |
| artworks |        |artworks_   |
|(content) |        |   style)   |
+----------+        +------------+
      |                    |
      +--------+----------+
               |
               v
       Cosine Similarity
       (against closest match)
               |
               v
    Combined Originality Score
    (70% Content + 30% Style)
               |
       +-------+-------+
       |               |
     PASS             FAIL
       |               |
   Return Score    fraudAlert=True
                   Minting Blocked
```

---

## Files

| File | Purpose |
|---|---|
| [`main.py`](./main.py) | FastAPI application — model loading, endpoints, scoring logic |
| [`requirements.txt`](./requirements.txt) | Python dependencies |
| [`test_inference.py`](./test_inference.py) | Automated end-to-end verification script |
| [`debug_clip.py`](./debug_clip.py) | Development debug script (can be deleted) |
| `.chroma/` | Persistent ChromaDB vector database storage (auto-generated) |
| `venv/` | Python virtual environment (auto-generated, not committed) |

---

## Models

### 1. CLIP — Content Similarity (`openai/clip-vit-base-patch32`)

**What it does:** Understands the *subject matter* and *semantic content* of an image.

**How it works:**
- Loaded from HuggingFace Transformers on server startup.
- The image is passed through the CLIP Vision Transformer encoder.
- The model outputs a **512-dimensional embedding** — a mathematical vector that captures what the image is "about".
- The vector is **L2-normalized** so that cosine similarity can be used directly.

**Why CLIP?**
- CLIP is trained on 400M image-text pairs and has excellent general image understanding.
- Two images with very similar content (even if slightly edited) will produce very close embeddings.

```python
inputs = clip_processor(images=image, return_tensors="pt")
outputs = clip_model.get_image_features(**inputs)
# Normalize → 512-d vector
```

---

### 2. ResNet-50 — Style Fingerprinting (`torchvision.models.resnet50`)

**What it does:** Understands the *visual style* and *texture* of an image — brushstrokes, color patterns, composition, artistic fingerprint.

**How it works:**
- A pre-trained ResNet-50 model is loaded from PyTorch's model hub.
- The **final classification layer is removed** (`nn.Sequential(*list(resnet.children())[:-1])`). This exposes the raw 2048-dimensional feature map that the model uses internally before making predictions.
- The image is preprocessed with standard ImageNet normalization (`mean=[0.485, 0.456, 0.406]`).
- The resulting **2048-dimensional style vector** is L2-normalized.

**Why ResNet-50 for style?**
- CNNs naturally extract hierarchical visual features — edges → textures → patterns → style.
- The intermediate feature map (before the classifier) is a dense representation of the image's visual characteristics, making it ideal for style comparison.

```python
resnet = nn.Sequential(*list(resnet.children())[:-1])  # Remove classifier
features = resnet(image_tensor)      # Shape: [1, 2048, 1, 1]
features = torch.flatten(features, 1)  # Shape: [1, 2048]
```

---

## Vector Database (ChromaDB)

**ChromaDB** is an open-source embedded vector database. It is configured to persist data locally in the `.chroma/` directory, so the database of known artworks survives server restarts.

Two separate **collections** are maintained:

| Collection | Model | Dimension | Purpose |
|---|---|---|---|
| `artworks` | CLIP | 512 | Content/subject matter similarity |
| `artworks_style` | ResNet-50 | 2048 | Artistic style similarity |

Both collections use **Cosine Similarity** (`hnsw:space: cosine`) as their distance metric. Cosine distance ranges from 0 (identical) to 1 (completely different).

---

## Scoring Logic

When `/analyze` is called, the engine performs these steps:

1. **Extract CLIP embedding** → query `artworks` collection → get `dist_clip` (cosine distance to nearest match)
2. **Extract Style embedding** → query `artworks_style` collection → get `dist_style` (cosine distance to nearest match)
3. **Convert distances to similarities:**
   ```
   sim_clip  = 1.0 - dist_clip
   sim_style = 1.0 - dist_style
   ```
4. **Blend into a combined score:**
   ```
   combined_sim = (sim_clip * 0.70) + (sim_style * 0.30)
   ```
   > Content similarity is weighted higher (70%) because CLIP is a stronger general model. Style adds a 30% refinement.
5. **Decision threshold:**
   ```
   original = (combined_sim <= 0.95)
   fraudAlert = not original
   originalityScore = 1 - combined_sim
   ```

**Empty Database Behavior:** If the database has no records to compare against, all distances default to `0.0`, meaning the image is treated as 100% original (`originalityScore: 1.0`).

---

## API Endpoints

### `GET /health`
Health check.

**Response:**
```json
{
  "ok": true,
  "service": "AuthArt AI Engine (CLIP + ResNet50 + ChromaDB)"
}
```

---

### `POST /analyze`
The main endpoint. Accepts a multipart image upload and returns originality scores.

**Request:**
```
Content-Type: multipart/form-data
Body: file=<image file>
```

**Response:**
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

| Field | Description |
|---|---|
| `original` | `true` if the artwork passes the originality check |
| `similarityScore` | How similar the content is to the closest known artwork (0-1) |
| `styleFingerprintScore` | How similar the style is to the closest known artwork (0-1) |
| `originalityScore` | Final blended originality score (1 = fully original, 0 = exact copy) |
| `fraudAlert` | `true` if the artwork is flagged as potentially plagiarized |
| `sha256` | SHA-256 hash of the uploaded file bytes |

---

### `POST /bootstrap`
Adds a known original artwork to both vector databases. Use this to populate the database with reference artworks.

**Request:**
```
Content-Type: multipart/form-data
Body: file=<image file>
```

**Response:**
```json
{
  "status": "success",
  "added_id": "19bf119c-d68a-42e9-ba53-e4c169486f9e",
  "filename": "artwork.jpg"
}
```

> **Note:** In production, this endpoint should be authenticated and only called by an admin or after a successful minting event to register the new NFT into the database.

---

## Running Locally

**1. Create and activate a virtual environment:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**2. Install dependencies:**
```bash
pip install -r requirements.txt
```

**3. Start the server:**
```bash
uvicorn main:app --reload --port 8000
```

The server will download the CLIP and ResNet-50 model weights on first launch (~600 MB total, cached after that).

**4. Run automated tests:**
```bash
python test_inference.py
```

---

## Known Limitations & Future Improvements

| Limitation | Future Fix |
|---|---|
| Empty database treats all images as original | Bootstrap with a real NFT dataset (e.g., from OpenSea or a curated corpus) |
| Style fingerprint is generic (not art-specific) | Fine-tune ResNet on a labeled art style dataset |
| No price prediction model | Train a regression model on historical NFT sales data |
| No authentication on `/bootstrap` | Add JWT middleware to protect the endpoint |
| Single server process (no scaling) | Deploy with Gunicorn + multiple workers or containerize with Docker |
