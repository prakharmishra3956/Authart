# AuthArt Frontend — Technical Documentation

## 1. Overview

The **AuthArt Frontend** is a modern Web3 Single Page Application (SPA) built with **React 19** and **Vite**. It provides a clean, responsive user experience for digital artists to:
- Authenticate using their MetaMask wallet via cryptographic message signing.
- View and manage their decentralized identity (DID: `did:pkh:eip155:1:<address>`).
- Upload digital artworks to the backend.
- Run AI-assisted originality and style fingerprint scans.
- Trigger NFT minting with automatic EIP-2981 royalty configuration.
- Browse creator vaults and marketplace listings.

---

## 2. Directory Structure

```text
frontend/
├── package.json              # Top-level script runner (delegates to vite-project)
├── FRONTEND_DOCS.md          # Technical documentation (this file)
└── vite-project/             # Main React + Vite application
    ├── index.html            # HTML entry point with viewport & font configurations
    ├── package.json          # React, Vite, Ethers.js dependencies & scripts
    ├── vite.config.js        # Vite build & plugin configurations
    ├── vercel.json           # SPA rewrites & Vercel deployment config
    ├── eslint.config.js      # ESLint rules
    ├── .env.example          # Environment variable template
    ├── public/               # Static assets & icons
    └── src/
        ├── main.jsx          # React DOM root render
        ├── App.jsx           # Root component with auth session routing
        ├── App.css           # Layout and component utility styles
        ├── index.css         # Global design system & theme variables
        ├── components/       # Reusable UI modules
        │   ├── Navbar.jsx    # Top navigation bar with wallet connection trigger
        │   ├── Hero.jsx      # Landing page hero section
        │   ├── Stats.jsx     # Platform statistics component
        │   ├── Vault.jsx     # Featured creator artworks preview
        │   ├── Footer.jsx    # Page footer
        │   └── MobileWalletModal.jsx # Mobile MetaMask deep link / fallback modal
        ├── pages/            # Page-level views
        │   ├── Home.jsx      # Unauthenticated landing page
        │   └── Dashboard.jsx # Authenticated creator studio & artwork management
        ├── services/         # API & Web3 integration layer
        │   ├── auth.js       # MetaMask signing, DID generation, JWT session storage
        │   └── api.js        # REST API client for backend communication
        └── styles/           # Dedicated stylesheet modules
```

---

## 3. Environment Variables Configuration

Create a `.env` file in `frontend/vite-project/`:

| Variable | Description | Default / Example |
|---|---|---|
| `VITE_API_URL` | Backend Express API base URL | `http://localhost:5000/api` |

*Note: If deployed on Vercel or cloud hosting, set `VITE_API_URL` to your live backend endpoint (e.g. `https://your-backend.onrender.com/api`).*

---

## 4. Key Modules & Technical Implementation

### 4.1 Authentication Service (`src/services/auth.js`)

Provides Web3 authentication through MetaMask without passwords:
1. **Wallet Detection**: Detects `window.ethereum` (or provides deep-link redirection on mobile).
2. **Account Request**: Prompts user for wallet access via `eth_requestAccounts`.
3. **Nonce Challenge**: Calls `POST /auth/nonce` to obtain a fresh cryptographic challenge.
4. **Signature Recovery**: Prompts user to sign via `signer.signMessage(challenge.message)`.
5. **Token Storage**: Submits signature to `POST /auth/verify` and stores the resulting JWT in `localStorage` (`authart_jwt`).
6. **Session Restoration**: Uses `restoreSession()` on page refresh by validating token with `GET /auth/me`.

### 4.2 API Client (`src/services/api.js`)

Centralizes all REST requests to the backend:
- `getMyArtworks()`: Fetches uploaded artworks owned by the connected wallet.
- `uploadArtwork(formData)`: Uploads image file, title, and description (`multipart/form-data`).
- `analyzeArtwork(id)`: Initiates AI originality check on backend.
- `mintArtwork(id)`: Dispatches the minting transaction for verified artworks.

### 4.3 Creator Dashboard (`src/pages/Dashboard.jsx`)

The primary studio for authenticated creators featuring three tabs:
1. **Upload Artwork**:
   - File dropzone supporting PNG, JPG, WEBP, and GIF (up to 10MB).
   - Real-time pipeline visualizer showing progress from Upload $\to$ AI Originality $\to$ Mint + Royalty $\to$ Marketplace.
   - **My Artwork Gallery**: Lists artworks with status badges (`PENDING`, `PASSED`, `FAILED`, `MINTED`), originality percentage scores, and action buttons (`RUN AI CHECK`, `START MINTING`).
2. **Marketplace View**: Lifecycle overview for listings, purchases, and EIP-2981 royalty settlements.
3. **Edit Profile**: Displays read-only wallet address, DID identifier, and editable creator bio.

### 4.4 Mobile Wallet Support (`src/components/MobileWalletModal.jsx`)

Provides seamless onboarding for mobile users:
- Detects mobile user agents (iOS / Android).
- Generates universal deep links (`https://metamask.app.link/dapp/<url>`) to open the app inside the MetaMask mobile browser.
- Directs users to the Google Play Store or Apple App Store if MetaMask is not installed.

---

## 5. Technology Stack & Dependencies

- **Framework**: React 19 (`react`, `react-dom`)
- **Build Tool**: Vite 8 (`@vitejs/plugin-react`)
- **Web3 Library**: Ethers.js v6 (`ethers`)
- **Styling**: Vanilla CSS with custom CSS Variables, Flexbox, and CSS Grid

---

## 6. Running the Frontend

### Install Dependencies
```bash
cd frontend/vite-project
npm install
```

### Start Development Server
```bash
npm run dev
```
Accessible by default at `http://localhost:5173`.

### Production Build
```bash
npm run build
npm run preview
```
