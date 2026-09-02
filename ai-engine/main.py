"""AuthArt AI Engine.
Integrates HuggingFace Transformers (CLIP) and ResNet50 (CNN) with ChromaDB.
Protected by API Key for internal service-to-service calls.
"""
import hashlib, os, io, uuid
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import JSONResponse
from PIL import Image
import torch
import torch.nn as nn
from torchvision import models, transforms
from transformers import CLIPProcessor, CLIPModel
import chromadb

# Load environment variables from .env
load_dotenv()
AI_API_KEY = os.getenv("AI_API_KEY", "")

app = FastAPI(title='AuthArt AI Engine')

# ── API Key Security ──────────────────────────────────────────────────────────
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def require_api_key(api_key: str = Security(API_KEY_HEADER)):
    """Dependency that enforces X-API-Key header on protected routes."""
    if not AI_API_KEY:
        raise HTTPException(status_code=500, detail="Server API key not configured.")
    if api_key != AI_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key.")
    return api_key

# ── Input Validation ──────────────────────────────────────────────────────────
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

def validate_image(data: bytes, content_type: str) -> Image.Image:
    """Validates file type, size, and integrity. Returns a PIL Image."""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{content_type}'. Allowed: jpeg, png, webp, gif."
        )
    if len(data) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({len(data) // 1024} KB). Maximum allowed is 10 MB."
        )
    try:
        image = Image.open(io.BytesIO(data)).convert("RGB")
        image.verify()  # Check if the image is corrupt
        image = Image.open(io.BytesIO(data)).convert("RGB")  # Re-open after verify
        return image
    except Exception:
        raise HTTPException(status_code=400, detail="File is not a valid or readable image.")

# ── 1. Load CLIP Model (Subject Matter) ──────────────────────────────────────
print("Loading CLIP model...")
model_id = "openai/clip-vit-base-patch32"
device = "cuda" if torch.cuda.is_available() else "cpu"
clip_processor = CLIPProcessor.from_pretrained(model_id)
clip_model = CLIPModel.from_pretrained(model_id).to(device)
print(f"CLIP model loaded on {device}.")

# ── 2. Load ResNet50 Model (Style Fingerprint) ────────────────────────────────
print("Loading ResNet50 Style model...")
resnet = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
resnet = nn.Sequential(*list(resnet.children())[:-1]).to(device)
resnet.eval()

style_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])
print("ResNet50 model loaded.")

# ── 3. Initialize Vector Database ────────────────────────────────────────────
print("Initializing ChromaDB...")
chroma_client = chromadb.PersistentClient(path="./.chroma")
collection_clip = chroma_client.get_or_create_collection(
    name="artworks",
    metadata={"hnsw:space": "cosine"}
)
collection_style = chroma_client.get_or_create_collection(
    name="artworks_style",
    metadata={"hnsw:space": "cosine"}
)
print("ChromaDB initialized.")


# ── Embedding Helpers ─────────────────────────────────────────────────────────
def get_clip_embedding(image: Image.Image):
    inputs = clip_processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = clip_model.get_image_features(**inputs)
        if hasattr(outputs, 'pooler_output'):
            image_features = outputs.pooler_output
        elif isinstance(outputs, torch.Tensor):
            image_features = outputs
        else:
            image_features = outputs[0]
    image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
    return image_features.cpu().numpy().tolist()[0]

def get_style_embedding(image: Image.Image):
    input_tensor = style_transform(image).unsqueeze(0).to(device)
    with torch.no_grad():
        features = resnet(input_tensor)
    features = torch.flatten(features, 1)
    features = features / features.norm(p=2, dim=-1, keepdim=True)
    return features.cpu().numpy().tolist()[0]

def query_scores(clip_emb, style_emb):
    """Query both collections and return similarity scores."""
    sim_clip, sim_style = 0.0, 0.0

    results_clip = collection_clip.query(query_embeddings=[clip_emb], n_results=1)
    if results_clip['distances'] and results_clip['distances'][0]:
        sim_clip = 1.0 - max(0.0, min(1.0, results_clip['distances'][0][0]))

    results_style = collection_style.query(query_embeddings=[style_emb], n_results=1)
    if results_style['distances'] and results_style['distances'][0]:
        sim_style = 1.0 - max(0.0, min(1.0, results_style['distances'][0][0]))

    return sim_clip, sim_style


# ── API Endpoints ─────────────────────────────────────────────────────────────
@app.get('/health')
def health():
    return {
        'ok': True,
        'service': 'AuthArt AI Engine (CLIP + ResNet50 + ChromaDB)',
        'db_records': collection_clip.count()
    }


@app.post('/bootstrap', dependencies=[Depends(require_api_key)])
async def bootstrap(file: UploadFile = File(...)):
    """
    [Protected] Add a known original artwork to the vector database.
    Requires header: X-API-Key: <AI_API_KEY>
    Only the Node.js backend should call this endpoint.
    """
    data = await file.read()
    image = validate_image(data, file.content_type)

    clip_emb = get_clip_embedding(image)
    style_emb = get_style_embedding(image)
    doc_id = str(uuid.uuid4())

    collection_clip.add(embeddings=[clip_emb], documents=[file.filename], ids=[doc_id])
    collection_style.add(embeddings=[style_emb], documents=[file.filename], ids=[doc_id])

    return {"status": "success", "added_id": doc_id, "filename": file.filename}


@app.post('/analyze')
async def analyze(file: UploadFile = File(...)):
    """Analyze uploaded artwork for originality. Open endpoint (called by backend)."""
    data = await file.read()
    image = validate_image(data, file.content_type)

    clip_emb = get_clip_embedding(image)
    style_emb = get_style_embedding(image)
    sim_clip, sim_style = query_scores(clip_emb, style_emb)

    combined_sim = (sim_clip * 0.7) + (sim_style * 0.3)
    original = combined_sim <= 0.95
    h = hashlib.sha256(data).hexdigest()

    return {
        'original': original,
        'similarityScore': round(sim_clip, 3),
        'styleFingerprintScore': round(sim_style, 3),
        'originalityScore': round(1 - combined_sim, 3),
        'fraudAlert': not original,
        'model': 'clip + resnet50 + chromadb',
        'sha256': h
    }


@app.post('/predict-price')
async def predict_price(file: UploadFile = File(...)):
    """
    Predict an indicative ETH price for the artwork.
    Uses a rule-based model combining originality and style uniqueness.
    This is an estimate, NOT a guaranteed market value.
    """
    data = await file.read()
    image = validate_image(data, file.content_type)

    clip_emb = get_clip_embedding(image)
    style_emb = get_style_embedding(image)
    sim_clip, sim_style = query_scores(clip_emb, style_emb)

    combined_sim = (sim_clip * 0.7) + (sim_style * 0.3)
    originality = 1.0 - combined_sim  # 0 = total copy, 1 = fully original

    # ── Rule-Based Price Model ────────────────────────────────────────────────
    # Base price for any artwork
    base_price = 0.05

    # Originality bonus: highly original art commands a premium
    originality_bonus = originality * 0.5

    # Similarity penalty: art too close to existing work is discounted
    similarity_penalty = sim_clip * 0.03

    # Style uniqueness bonus: very different style gets extra value
    style_bonus = 0.05 if sim_style < 0.3 else 0.0

    estimated_price = base_price + originality_bonus - similarity_penalty + style_bonus

    # Clamp to a reasonable range
    estimated_price = max(0.01, min(1.0, estimated_price))

    return {
        'estimatedPriceETH': round(estimated_price, 4),
        'priceUSD': round(estimated_price * 3200, 2),  # Approx ETH/USD rate
        'breakdown': {
            'basePrice': base_price,
            'originalityBonus': round(originality_bonus, 4),
            'similarityPenalty': round(similarity_penalty, 4),
            'styleBonus': style_bonus,
        },
        'originalityScore': round(originality, 3),
        'model': 'rule-based v1',
        'disclaimer': 'Estimated price only. Actual market value may differ.'
    }


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
