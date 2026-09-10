# AuthArt Backend — Pending Implementation Tasks & TODOs

This document details all the pending tasks required to bring the AuthArt backend from an MVP/demo stage to a production-ready Web3 platform.

---

## Task 1: Connect Backend to Real Python AI Engine (`ai-engine`)

### Problem
Currently, `backend/services/ai.js` uses a dummy SHA-256 fallback algorithm to generate fake similarity and style scores. The real Python AI Engine (`ai-engine/main.py`) running CLIP + ResNet-50 + ChromaDB at `http://localhost:8000/analyze` is not yet called by Express.

### Implementation Checklist
- [ ] Install `form-data` in backend: `npm install form-data`.
- [ ] Update `backend/services/ai.js` to dispatch a multipart POST request with the artwork image buffer to `http://localhost:8000/analyze`.
- [ ] Add `AI_ENGINE_URL` and `AI_ENGINE_API_KEY` to `backend/.env.example` and `.env`.
- [ ] Forward the `X-API-Key` header for secure communication between Express and FastAPI.
- [ ] Parse and map the returned CLIP similarity, ResNet style fingerprint, and price prediction into the artwork database record.

---

## Task 2: IPFS / Decentralized Storage Integration

### Problem
Artwork images are saved locally to `backend/uploads/` and metadata JSONs to `backend/data/metadata/`. If the server goes down or moves, the token URIs (`local://metadata/<id>`) become invalid.

### Implementation Checklist
- [ ] Integrate Pinata SDK (`@pinata/sdk`) or Web3.Storage.
- [ ] Update `POST /api/artworks/upload` or the minting pipeline to pin the image binary to IPFS, obtaining an `ipfs://<image_cid>` URI.
- [ ] Update `POST /api/artworks/:id/mint` to construct and pin the metadata JSON to IPFS, obtaining an `ipfs://<metadata_cid>` URI.
- [ ] Store both the IPFS CID and HTTP gateway URL in the database record.

---

## Task 3: User Profile Management & Persistence

### Problem
`GET /api/auth/me` returns user data, but there is no endpoint allowing users to update their display names, avatars, bios, and social links.

### Implementation Checklist
- [ ] Create `PUT /api/auth/profile` endpoint in `server.js` or `routes/auth.js`.
- [ ] Validate profile fields (display name, bio, email/social links).
- [ ] Update and persist the user object in `data/users.json` (or database).
- [ ] Return the updated user profile to the client.

---

## Task 4: Database Migration (JSON Files $\to$ Database)

### Problem
Data is currently persisted in flat JSON files (`data/users.json` and `data/artworks.json`). This will cause file write concurrency locks and memory bottlenecks under multi-user loads.

### Implementation Checklist
- [ ] Choose a persistent database engine (MongoDB with Mongoose or PostgreSQL with Prisma).
- [ ] Define schemas:
  - **User Schema**: `address`, `did`, `displayName`, `bio`, `avatarUrl`, `createdAt`, `lastLoginAt`.
  - **Artwork Schema**: `title`, `description`, `imageUrl`, `ipfsCid`, `ownerAddress`, `did`, `status`, `aiStatus`, `aiResult`, `mintReceipt`, `createdAt`.
  - **Marketplace Listing Schema**: `tokenId`, `sellerAddress`, `priceEth`, `isActive`, `listedAt`.
- [ ] Replace `fs.readFileSync` and `fs.writeFileSync` in `routes/artwork.js` and `server.js` with database queries.

---

## Task 5: Marketplace Backend Endpoints & Event Indexer

### Problem
The frontend marketplace tab lacks backend endpoints to query active NFT listings, floor prices, and sales history.

### Implementation Checklist
- [ ] Create `backend/routes/marketplace.js`:
  - `GET /api/marketplace/listings`: Returns active artwork listings with filters (price, originality score, category).
  - `GET /api/marketplace/listings/:id`: Returns detailed listing data.
  - `GET /api/marketplace/history`: Returns historical sales and royalty payouts.
- [ ] Implement an on-chain event listener in `backend/services/blockchain.js`:
  - Listen for `ItemListed`, `ItemSold`, and `ItemCanceled` events emitted by `AuthArtMarketplace.sol`.
  - Automatically update the local listing database when an on-chain transaction occurs.

---

## Task 6: Error Handling, Logging & Security Hardening

### Implementation Checklist
- [ ] Replace `console.log` with structured logging (e.g. `winston` or `pino`).
- [ ] Implement rate limiting (`express-rate-limit`) on `/api/auth/nonce` to mitigate DDoS / spamming attacks.
- [ ] Add `helmet` middleware for security headers.
- [ ] Add file magic number validation (e.g. `file-type`) to verify image MIME types beyond file extensions.
