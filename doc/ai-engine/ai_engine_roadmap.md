# AI Engine Production Roadmap

The current AI engine is a deterministic mock. To make it fully functional and capable of actually analyzing images for originality, we need to replace the `fallback()` function with real Machine Learning models. 

Here are the step-by-step tasks to complete the AI Engine.

## Phase 1: Machine Learning Environment Setup

### 1. Install ML Dependencies
Update `requirements.txt` and install the actual libraries needed for image processing and AI inference.
- **`torch` & `torchvision`**: Core deep learning frameworks.
- **`transformers`**: HuggingFace library to easily load pre-trained CLIP models.
- **`faiss-cpu` or `chromadb`**: For our local Vector Database (Similarity Search).
- **`pillow`**: For image processing.

## Phase 2: Feature Extraction (The Brains)

### 2. Implement CLIP for Similarity
CLIP (Contrastive Language-Image Pretraining) by OpenAI is excellent for understanding image content.
- Load a pre-trained CLIP model (e.g., `openai/clip-vit-base-patch32`).
- Create a function that takes the uploaded image, runs it through CLIP, and outputs a mathematical vector (an **embedding**) representing the image.

### 3. Implement CNN for Style Fingerprinting
While CLIP understands *what* is in the image, a Convolutional Neural Network (CNN) like ResNet can be tuned to understand the *style* (brushstrokes, colors, texture).
- Load a pre-trained ResNet model (or train a custom one).
- Strip the classification head to extract the raw feature map.
- Create a function that outputs a **style vector**.

## Phase 3: Similarity Search (Vector Database)

### 4. Setup a Vector Database
To know if an image is stolen, we have to compare it against existing art. We can't do this one-by-one; we need a Vector Database.
- Integrate **FAISS** (by Meta) or **ChromaDB** into the FastAPI app.
- This database will store the CLIP and CNN embeddings of *all previously minted NFTs*.

### 5. Create the Comparison Logic
Update the `/analyze` endpoint to perform the following flow:
1. Receive uploaded image.
2. Generate its CLIP embedding.
3. Query the Vector Database for the "Nearest Neighbors" (the most similar existing images).
4. Calculate the cosine similarity distance between the uploaded image and the closest match.
5. Generate the `similarityScore`.

## Phase 4: Decision Making

### 6. Originality & Fraud Logic
Replace the random math in `main.py` with actual thresholds based on the model outputs.
- Set a threshold (e.g., if cosine similarity is > 0.95, flag `fraudAlert = True`).
- Calculate the `originalityScore` dynamically based on how far the image is from its nearest neighbor.

### 7. Populate a Starter Dataset (Bootstrapping)
The AI won't know an image is copied unless it has a database of original images to compare it against.
- Write a script to scrape or download a batch of existing NFT images.
- Run them all through your new CLIP model to generate embeddings.
- Save these embeddings into your Vector Database so the AI has a baseline to compare new uploads against.

---

> [!TIP]
> **Next Steps:** If you want to start building this, I recommend we begin with **Phase 1 & 2**—integrating the `transformers` library and getting a real CLIP model to generate an embedding for an uploaded image.
