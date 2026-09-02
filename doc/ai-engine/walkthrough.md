# AI Engine Upgrade Walkthrough

We have successfully upgraded the AuthArt AI Engine from a dummy mock script to a fully functional Machine Learning microservice!

## What We Did

### 1. Replaced the "Fake Math"
The original `main.py` used a simple SHA-256 hash trick to randomly guess if an image was original. We completely stripped that out and wrote real integration code for the HuggingFace `transformers` library.

### 2. Integrated a Real CLIP Model (Phase 1 & 2)
The AI engine now loads `openai/clip-vit-base-patch32` (a pre-trained multimodal model) on server startup. When a creator uploads an artwork, it converts that image into a mathematical vector representation (an "embedding").

### 3. Integrated ChromaDB (Phase 3)
Instead of comparing against nothing, we added `chromadb`, a persistent Vector Database. 
- It stores a record of every "original" artwork.
- When an artwork is analyzed, it calculates the **Cosine Similarity** distance against the closest known image in the database.
- If the similarity is > 98%, it correctly flags the upload as a **fraud** and sets the `originalityScore` to near 0!

## Test Results
We ran a dedicated test script (`test_inference.py`) that successfully proved the workflow:
1. Checked a dummy image against an empty database. Output: **`original: True`, `fraudAlert: False`**.
2. Bootstrapped (saved) that dummy image to the database.
3. Re-ran the analysis on the same dummy image. Output: **`original: False`, `fraudAlert: True`, `similarityScore: 1.0`**.

> [!TIP]
> The engine now actually works as a real, protective AI gatekeeper for the Web3 minting process!
