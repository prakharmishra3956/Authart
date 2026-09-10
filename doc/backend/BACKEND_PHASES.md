# AuthArt Backend — Phase-Wise Architecture & Implementation Status

## 1. Overview of the 5 Phases in the Backend

The AuthArt backend acts as the central middleware that connects the client interface (React SPA), the artificial intelligence microservice (Python FastAPI / CLIP + ResNet-50), and the EVM blockchain smart contracts.

Here is the phase-wise breakdown of backend responsibilities:

```text
+-----------------------------------------------------------------------------------+
|                              AUTHART BACKEND PHASES                               |
+-----------------------------------------------------------------------------------+
| Phase 1: User Authentication & Decentralized Identity (DID)                       |
|   MetaMask Nonce Challenge -> ecRecover Signature -> did:pkh Issuance -> JWT      |
+-----------------------------------------------------------------------------------+
| Phase 2: Creator Studio & Asset Ingestion                                         |
|   Multipart Artwork Upload -> File Sanitization -> UUID Tagging -> Local Storage  |
+-----------------------------------------------------------------------------------+
| Phase 3: AI Microservice Integration & Gatekeeping                                |
|   Dispatch Artwork to AI Engine -> Content + Style Evaluation -> Minting Gate     |
+-----------------------------------------------------------------------------------+
| Phase 4: Decentralized Metadata & Smart Contract Minting                          |
|   OpenSea-Standard Metadata -> IPFS Pinning -> ERC-721 / EIP-2981 Minting         |
+-----------------------------------------------------------------------------------+
| Phase 5: Marketplace Backend & Event Indexing                                     |
|   Listing State Management -> Order History -> Event Listener -> Reputation Sync  |
+-----------------------------------------------------------------------------------+
```

---

## 2. Phase-Wise Status Matrix

| Phase | Description | Current Status | Implemented Components |
|---|---|---|---|
| **Phase 1** | Auth & DID | ✅ **Complete (MVP)** | Nonce generation, signature verification with `recoverAddress`, `did:pkh` assignment, HMAC-SHA256 JWT sessions, `/api/auth/me`. |
| **Phase 2** | Creator Studio & Ingestion | 🟡 **Partially Complete** | Multer image upload (10MB limit), artwork record generation, `/api/artworks` queries. Profile metadata persistence still pending. |
| **Phase 3** | AI Integration & Gatekeeping | 🟡 **Partially Complete** | Gatekeeping logic in `/analyze` endpoint. Uses local SHA-256 fallback; needs HTTP wiring to the active Python AI Engine (`:8000`). |
| **Phase 4** | Blockchain & NFT Minting | 🟡 **Partially Complete** | Metadata generation in `data/metadata/`, `ethers.js` minting helper. Needs IPFS storage integration (Pinata) and dynamic fee management. |
| **Phase 5** | Marketplace & Reputation | 🔴 **Pending** | Smart contracts exist in Hardhat, but backend routes for marketplace indexing, listings database, and reputation tracking are missing. |

---

## 3. Detailed Breakdown of Each Phase

### Phase 1: User Authentication & DID
- **Current State:**
  - `POST /api/auth/nonce`: Issues a 32-byte cryptographically secure random nonce with a 5-minute time-to-live (TTL).
  - `POST /api/auth/verify`: Recovers the Ethereum address from the `personal_sign` signature and generates a W3C-compliant PKH DID (`did:pkh:eip155:1:<address>`).
  - `authMiddleware`: Enforces Bearer token presence and verifies JWT integrity.
- **What's Implemented:** Complete, secure, replay-protected Web3 authentication.

---

### Phase 2: Creator Studio & Asset Ingestion
- **Current State:**
  - `POST /api/artworks/upload`: Accepts JPG, PNG, WEBP, and GIF files up to 10MB via `multer`.
  - Saves binary files in `backend/uploads/` with UUID-based filenames.
  - Creates an artwork record in `data/artworks.json` with initial status `aiStatus: pending`.
- **What's Implemented:** Image ingestion, file validation, and initial record creation.

---

### Phase 3: AI Microservice Integration & Gatekeeping
- **Current State:**
  - `POST /api/artworks/:id/analyze`: Ensures only the artwork creator can trigger analysis.
  - Invokes `services/ai.js` to calculate similarity, style fingerprint, and price suggestion.
  - Updates the artwork state to `aiStatus: passed` or `aiStatus: failed`.
  - Blocks minting if `aiStatus !== 'passed'`.
- **What's Implemented:** Strict verification gatekeeper logic before blockchain transactions can occur.

---

### Phase 4: Decentralized Metadata & Smart Contract Minting
- **Current State:**
  - `POST /api/artworks/:id/mint`: Validates that the artwork has passed the AI check.
  - Generates an OpenSea-compliant metadata JSON file in `data/metadata/<id>.json`.
  - Calls `services/blockchain.js` which connects to an EVM node via `ethers.JsonRpcProvider` and executes the `mint()` function on `AuthArtNFT.sol`.
  - Falls back to a mock local receipt when blockchain environment variables are not configured.
- **What's Implemented:** Metadata generation and smart contract interaction via Ethers v6.

---

### Phase 5: Marketplace Backend & Reputation Engine
- **Current State:**
  - The smart contracts (`AuthArtMarketplace.sol`) handle on-chain sales, royalties, and reputation scores.
  - The backend currently lacks dedicated marketplace endpoints to index active listings and track off-chain creator reputation scores.
- **What's Implemented:** Smart contract foundation only; backend layer pending.
