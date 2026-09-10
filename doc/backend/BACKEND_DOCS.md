# AuthArt Backend — Complete Technical Documentation

## 1. Overview

The **AuthArt Backend** is a Node.js & Express.js microservice responsible for:
- Web3 wallet cryptographic authentication (MetaMask personal sign verification).
- Decentralized Identity (DID) issuance (`did:pkh`).
- JWT session management.
- Artwork asset management and multipart file upload handling.
- AI gatekeeping workflow (linking uploads to originality analysis).
- NFT metadata generation and smart contract minting dispatch via `ethers.js`.

---

## 2. Directory Structure

```text
backend/
├── .env.example              # Template for environment variables
├── .gitignore                # Ignored node_modules, temp files, env
├── package.json              # Express, ethers, multer, cors, dotenv dependencies
├── README.md                 # Quickstart guide
├── BACKEND_DOCS.md           # Full technical documentation (this file)
├── server.js                 # Server entry point, auth middleware, and auth routes
├── routes/
│   └── artwork.js            # Express router for artwork lifecycle (/api/artworks)
├── services/
│   ├── ai.js                 # AI analysis adapter (deterministic fallback & microservice client)
│   └── blockchain.js         # EVM interaction for ERC-721 / EIP-2981 minting
├── data/                     # Persistent JSON storage directory
│   ├── users.json            # Stored user profiles and DIDs
│   ├── artworks.json         # Stored artwork metadata and status records
│   └── metadata/             # Generated ERC-721 token metadata JSON files
└── uploads/                  # Uploaded artwork image binaries
```

---

## 3. Environment Variables Configuration

Create a `.env` file in the `backend/` directory:

| Variable | Description | Example / Default |
|---|---|---|
| `PORT` | Port the backend server listens on | `5000` |
| `FRONTEND_ORIGIN` | Allowed client origin for CORS | `http://localhost:5173` |
| `JWT_SECRET` | Secret key for signing and verifying HMAC-SHA256 JWTs | `a-secure-random-secret-key` |
| `RPC_URL` | EVM JSON-RPC provider endpoint (e.g. Hardhat / Sepolia) | `http://127.0.0.1:8545` |
| `NFT_CONTRACT_ADDRESS` | Deployed `AuthArtNFT` contract address | `0x5FbDB2315678afecb367f032d93F642f64180aa3` |
| `MINTER_PRIVATE_KEY` | Private key used by backend to sign mint transactions | `0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80` |

---

## 4. Authentication Architecture & Flow

AuthArt implements passwordless, cryptographic authentication using Ethereum wallets (MetaMask).

```text
+-------------------+                 +-------------------+
|  Frontend Client  |                 |  Express Backend  |
+-------------------+                 +-------------------+
          |                                     |
          |-------- 1. POST /api/auth/nonce --->| (Generates 32-byte hex nonce, 5m TTL)
          |<------- Challenge Message ----------|
          |                                     |
   User signs message                           |
   via MetaMask (personal_sign)                 |
          |                                     |
          |-------- 2. POST /api/auth/verify -->| (Recovers address with recoverAddress)
          |         (address, signature)        | (Checks nonce validity & marks consumed)
          |                                     | (Creates did:pkh:eip155:1:<address>)
          |<------- JWT Token & User Profile ---| (Returns signed JWT valid for 24h)
          |                                     |
```

### 4.1 Nonce Generation (`POST /api/auth/nonce`)
- **Request Body:** `{ "address": "0x1234..." }`
- **Logic:**
  - Validates Ethereum address via `ethers.getAddress(address)`.
  - Generates a 32-byte cryptographic random nonce (`crypto.randomBytes(32).toString('hex')`).
  - Constructs the challenge string:
    ```text
    Welcome to AuthArt.

    Sign this message to authenticate your wallet: <checksummed_address>

    Nonce: <random_hex>
    Issued At: <iso_timestamp>
    ```
  - Saves in memory with a 5-minute TTL. Periodic cleanup runs every 60 seconds.

### 4.2 Signature Verification (`POST /api/auth/verify`)
- **Request Body:** `{ "address": "0x1234...", "signature": "0x..." }`
- **Logic:**
  - Recovers the signer address from `hashMessage(challenge)` using `recoverAddress`.
  - Ensures nonce is present, unexpired, and immediately deletes it (preventing replay attacks).
  - Generates deterministic DID: `did:pkh:eip155:1:<address>`.
  - Persists user in `data/users.json`.
  - Issues signed JWT token valid for 24 hours.

### 4.3 Session Introspection (`GET /api/auth/me`)
- **Headers:** `Authorization: Bearer <JWT>`
- **Returns:** `{ "authenticated": true, "user": { ... } }`

---

## 5. Artwork Lifecycle & API Routes (`routes/artwork.js`)

All `/api/artworks/*` routes (except static file serving) require `authMiddleware`.

### 5.1 Artwork Data Schema
```json
{
  "id": "b3bb05d4-dd10-4c75-8f6c-ff5120aa5882",
  "title": "DARK KNIGHT",
  "description": "IT RISES IN DAWN",
  "originalName": "artwork.jpeg",
  "filename": "1788239508694-fa73d24a.jpeg",
  "mimeType": "image/jpeg",
  "size": 68326,
  "ownerAddress": "0xaadF4F8918a0EB462518fA11C62fD204183f6e49",
  "did": "did:pkh:eip155:1:0xaadf4f8918a0eb462518fa11c62fd204183f6e49",
  "status": "uploaded | minted",
  "aiStatus": "pending | passed | failed",
  "createdAt": "2026-09-01T05:11:48.705Z",
  "aiResult": {
    "original": true,
    "similarityScore": 0.12,
    "styleFingerprintScore": 0.3,
    "originalityScore": 1.0,
    "fraudAlert": false,
    "model": "AuthArt AI adapter",
    "sha256": "23ed8c9ed114...",
    "pricePrediction": {
      "suggestedEth": 1.88,
      "confidence": 0.72
    }
  },
  "mint": {
    "tokenId": "1788239518884",
    "network": "Local Demo Chain",
    "contractAddress": "demo-contract",
    "metadataUri": "local://metadata/b3bb05d4-dd10-4c75-8f6c-ff5120aa5882",
    "royaltyBps": 500
  }
}
```

### 5.2 API Endpoints

| Method | Route | Description |
|---|---|---|
| `GET` | `/api/artworks` | Returns list of artworks uploaded by the calling wallet. |
| `POST` | `/api/artworks/upload` | Handles `multipart/form-data` upload (`artwork` file, `title`, `description`). Max size: 10MB. |
| `POST` | `/api/artworks/:id/analyze` | Triggers AI originality & style fingerprint analysis. Updates `aiStatus` (`passed` or `failed`). |
| `POST` | `/api/artworks/:id/mint` | Verifies `aiStatus === 'passed'`, writes metadata JSON, and executes smart contract minting. |
| `GET` | `/api/artworks/file/:filename` | Serves binary file from `backend/uploads/`. |

---

## 6. Services & Subsystems

### 6.1 AI Integration Service (`services/ai.js`)
- Performs analysis on the artwork image binary.
- Produces `similarityScore`, `styleFingerprintScore`, `originalityScore`, `fraudAlert`, and `pricePrediction`.
- Can be configured to dispatch HTTP requests directly to the Python FastAPI microservice (`POST http://localhost:8000/analyze`).

### 6.2 Blockchain Service (`services/blockchain.js`)
- Interfaces with the smart contract using `ethers.Contract`:
  ```solidity
  function mint(address to, string uri, address royaltyReceiver, uint96 royaltyBps) external returns(uint256);
  ```
- Defaults to 500 basis points (5%) creator royalty.
- If blockchain environment variables are not set, provides a mock transaction receipt for safe local demonstrations.

---

## 7. Storage Layer

- **`data/users.json`**: Flat-file JSON map of wallet addresses to user profiles and DIDs.
- **`data/artworks.json`**: Flat-file JSON array containing all uploaded artwork records.
- **`data/metadata/`**: Directory storing standard ERC-721 OpenSea-compatible metadata JSON files per minted token.
- **`uploads/`**: Directory storing raw image uploads (`.png`, `.jpg`, `.webp`, `.gif`).

---

## 8. Running the Backend

### Installation
```bash
cd backend
npm install
```

### Development Mode (Auto-reloading with Node.js watch)
```bash
npm run dev
```

### Production Mode
```bash
npm start
```
Server runs by default at `http://localhost:5000`.
