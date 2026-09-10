# AuthArt — Project Architecture & Backend Technical Specification

## 1. Executive Summary

**AuthArt** is an AI-powered, decentralized Web3 NFT art platform designed to protect creators by verifying digital artwork originality before minting onto the blockchain. 

The architecture is divided into five core phases:
1. **Phase 1 — User Authentication & DID**: MetaMask wallet signature verification, one-time nonces, decentralized identity (`did:pkh`), and JWT generation.
2. **Phase 2 — Creator Dashboard**: Protected asset management, artwork upload pipelines, and status tracking.
3. **Phase 3 — AI Artwork Analysis**: Dual-model analysis (CLIP + ResNet-50) backed by ChromaDB vector similarity search to detect duplicates and plagiarism.
4. **Phase 4 — Smart Contracts & Minting**: ERC-721 / ERC-1155 smart contracts with EIP-2981 royalty enforcement and decentralized metadata.
5. **Phase 5 — NFT Marketplace**: Trading, peer-to-peer purchasing, on-chain royalty settlements, and creator reputation updates.

---

## 2. Directory & Module Overview

```text
AuthArt/
├── README.md                 # Complete project specification and 5-phase overview
├── ai-engine/                # Python FastAPI microservice (CLIP, ResNet-50, ChromaDB)
│   ├── main.py               # AI inference endpoints (/analyze, /bootstrap, /health)
│   ├── requirements.txt      # PyTorch, Transformers, ChromaDB dependencies
│   ├── test_inference.py     # Automated test suite for AI analysis
│   └── README.md             # AI Engine technical documentation
├── backend/                  # Node.js / Express.js REST API & Blockchain orchestrator
│   ├── server.js             # Express server, auth middleware, JWT, nonces
│   ├── routes/
│   │   └── artwork.js        # /api/artworks routes (upload, analyze, mint, view)
│   ├── services/
│   │   ├── ai.js             # AI engine communication adapter
│   │   └── blockchain.js     # Ethers.js integration for smart contract minting
│   ├── data/                 # Flat-file database (users.json, artworks.json, metadata/)
│   └── README.md             # Backend setup & API reference
├── frontend/                 # Client application
│   └── vite-project/         # React + Vite Web3 UI
├── smart-contracts/          # Hardhat development environment
│   ├── contracts/            # AuthArtNFT.sol, AuthArt1155.sol, AuthArtMarketplace.sol
│   └── README.md             # Contract compilation & local node instructions
└── doc/
    └── ai-engine/            # AI Engine design, roadmap, and walkthrough documentation
```

---

## 3. Detailed Backend Technical Breakdown (`backend/`)

The backend functions as the secure middleware and orchestrator between the React frontend, the Python AI Engine, and the Ethereum/EVM blockchain.

### 3.1 Authentication & Decentralized Identity (`server.js`)

The platform uses a cryptographic, passwordless authentication workflow:

```text
[Frontend (MetaMask)]                [Backend (Express)]
        |                                     |
        |--- 1. POST /api/auth/nonce -------->| (Generates 32-byte hex nonce, 5-min TTL)
        |<-- Returns challenge message -------|
        |                                     |
  Signs message                               |
  via personal_sign                           |
        |                                     |
        |--- 2. POST /api/auth/verify ------->| (Verifies signature with recoverAddress)
        |    (Address + Signature)            | (Matches against stored nonce)
        |                                     | (Creates did:pkh:eip155:1:<address>)
        |<-- Returns JWT & User Profile ------| (Issues HS256 JWT valid for 24h)
```

- **Replay Protection**: Nonces are strictly one-time-use and expire after 5 minutes.
- **Identity (DID)**: Uses W3C PKH DID method (`did:pkh:eip155:1:<checksummed_address>`).
- **Middleware (`authMiddleware`)**: Validates the `Authorization: Bearer <token>` header, decodes user DID and address, and protects downstream routes.

---

### 3.2 Artwork Lifecycle & Routing (`routes/artwork.js`)

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/artworks` | `GET` | Required | Returns all artworks owned by the authenticated wallet. |
| `/api/artworks/upload` | `POST` | Required | Accepts `multipart/form-data` (PNG, JPG, WEBP, GIF up to 10MB). Sets `status: uploaded` and `aiStatus: pending`. |
| `/api/artworks/:id/analyze` | `POST` | Required | Passes image through AI analysis to evaluate originality score. |
| `/api/artworks/:id/mint` | `POST` | Required | Enforces `aiStatus === 'passed'`. Generates NFT metadata and executes contract minting. |
| `/api/artworks/file/:filename` | `GET` | Public | Serves stored artwork image files. |

---

### 3.3 Services & Subsystem Integrations

#### 1. AI Integration Service (`services/ai.js`)
- Responsible for passing image binaries to the AI analysis layer.
- Evaluates **content similarity** and **style fingerprints** to establish an originality threshold.
- Generates price suggestions in ETH based on calculated originality confidence.

#### 2. Blockchain Service (`services/blockchain.js`)
- Interfaces with EVM nodes using `ethers.js` (`JsonRpcProvider`, `Wallet`, `Contract`).
- Calls the `mint(address to, string uri, address royaltyReceiver, uint96 royaltyBps)` smart contract method.
- Provides fallback to a mock local receipt when environment variables (`RPC_URL`, `NFT_CONTRACT_ADDRESS`, `MINTER_PRIVATE_KEY`) are not configured.

---

## 4. AI Engine Specifications (`ai-engine/`)

The Python microservice evaluates uploaded images to safeguard against copyright infringement and plagiarized minting.

- **Content Feature Extraction**: `openai/clip-vit-base-patch32` (512-dimensional vector).
- **Style Feature Extraction**: ResNet-50 with classifier removed (2048-dimensional intermediate feature map).
- **Vector Search Database**: ChromaDB collections (`artworks` & `artworks_style`) using Cosine Distance.
- **Combined Originality Formula**:
  $$\text{Combined Similarity} = 0.70 \times \text{Sim}_{\text{CLIP}} + 0.30 \times \text{Sim}_{\text{ResNet}}$$
  $$\text{Originality Score} = 1.0 - \text{Combined Similarity}$$
- **Gatekeeping Decision**:
  - If $\text{Combined Similarity} > 0.95 \implies \text{fraudAlert} = \text{True}$, minting blocked.
  - If $\text{Combined Similarity} \le 0.95 \implies \text{fraudAlert} = \text{False}$, minting permitted.

---

## 5. Smart Contracts & Storage (`smart-contracts/`)

- **`AuthArtNFT.sol`**: ERC-721 contract implementing ERC-2981 standard for creator royalties (default 500 bps = 5%).
- **`AuthArt1155.sol`**: Multi-edition art token contract.
- **`AuthArtMarketplace.sol`**: Non-custodial listing, purchase, and automatic royalty splitting contract.

---

## 6. Recommended Next Development Milestones

1. **AI Service Connection**: Wire `backend/services/ai.js` directly to `http://localhost:8000/analyze` via `axios` with `multipart/form-data` and API key headers.
2. **Decentralized Storage (IPFS)**: Integrate Pinata or Web3.Storage to upload images and metadata JSONs directly to IPFS rather than storing them in `backend/uploads` and `backend/data/metadata`.
3. **Database Layer**: Transition from JSON file storage (`data/users.json`, `data/artworks.json`) to MongoDB or PostgreSQL.
