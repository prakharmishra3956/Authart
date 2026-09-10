# AuthArt Phase 1 — Wallet Authentication

Flow:
1. Frontend requests a one-time nonce challenge from `POST /api/auth/nonce`.
2. MetaMask signs the challenge with `personal_sign` through ethers `signMessage`.
3. Backend recovers the Ethereum address from the signature using `recoverAddress` (ecRecover-equivalent verification).
4. The backend creates a deterministic DID (`did:pkh:eip155:1:<address>`) for a new wallet or loads the existing DID for a returning wallet.
5. Backend issues a signed JWT.
6. Frontend stores the JWT and calls `/api/auth/me` to restore the session on refresh.

## Run backend

```bash
cd backend
npm install
# copy .env.example to .env and set JWT_SECRET
node server.js
```

Backend: `http://localhost:5000`

## Run frontend

```bash
cd frontend/vite-project
npm install
# copy .env.example to .env if the backend uses a different URL
npm run dev
```

Frontend: `http://localhost:5173`

## Notes

- Nonces expire after 5 minutes and are deleted after successful verification, preventing replay.
- The demo stores user records in `backend/data/users.json`. For production, move this to MongoDB/Redis and use a strong secret from environment/secret management.
- Never commit a real `JWT_SECRET`.

# Phase 2 — Dashboard

Authenticated users can now access `/api/artworks` and `/api/artworks/upload`. Artwork uploads require the Phase 1 JWT, are limited to 10 MB, and accept PNG/JPG/WEBP/GIF. Uploaded artwork is stored locally for development and marked `aiStatus: pending` so Phase 3 can consume it.
