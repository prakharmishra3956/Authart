# AuthArt Frontend — Pending Implementation Roadmap & TODOs

## 1. Executive Summary

While the **Phase 1 (Wallet Authentication & DID)** and basic **Phase 2 (Dashboard & Upload Flow)** are operational in the frontend, several essential features and production enhancements remain to be implemented to complete the full 5-phase AuthArt vision.

---

## 2. Gap Analysis by Phase

### Phase 1 & 2: Authentication & Creator Experience (Polish & Persistence)
- [ ] **Profile Persistence**: The "Edit Profile" tab in `Dashboard.jsx` currently only shows a local feedback notification. Needs a backend endpoint (`PUT /api/auth/profile`) and frontend integration to save custom display names, avatars, and bios to `users.json` or a database.
- [ ] **Wallet Event Listeners**:
  - Automatically handle account changes (`window.ethereum.on('accountsChanged')`).
  - Handle network/chain changes (`window.ethereum.on('chainChanged')`).
  - Handle wallet disconnections gracefully.
- [ ] **Extended Wallet Support**: Add WalletConnect / RainbowKit support alongside MetaMask for wider multi-wallet compatibility (e.g. Coinbase Wallet, Trust Wallet).

---

### Phase 3: AI Engine Insights & Visualizations (Detailed Breakdown)
- [ ] **Rich AI Analysis Modal / Drawer**:
  - Instead of just showing a percentage badge, display a breakdown modal showing:
    - **Content Similarity Score** (CLIP 512-d).
    - **Style Fingerprint Score** (ResNet-50 2048-d).
    - **Nearest Neighbor Match Preview**: If flagged or similar, show thumbnails of the reference artwork from ChromaDB that caused the match.
    - **Confidence Metrics & Price Estimator Graph**.
- [ ] **Real-time Scan Animation**: Interactive progress bar or radar scan animation during the `RUN AI CHECK` state.

---

### Phase 4: Blockchain & Web3 Minting (On-Chain Interactions)
- [ ] **Direct Client-Side Smart Contract Interaction**:
  - Allow creators to sign the `mint()` transaction directly from their own wallet in MetaMask (instead of solely relying on the backend relayer).
  - Configure customizable Royalty Percentage (EIP-2981 bps input: 2.5%, 5%, 10%).
- [ ] **Decentralized Storage (IPFS) Integration**:
  - Direct IPFS pinning of artwork binaries via Pinata / Web3.Storage.
  - Display IPFS CIDs (`ipfs://...`) on the minted artwork cards.
- [ ] **Transaction Status Tracking**:
  - Etherscan / Polygonscan block explorer link generation (`https://sepolia.etherscan.io/tx/<txHash>`).
  - Confirmed block receipt visual toast.

---

### Phase 5: Fully Functional NFT Marketplace
The Marketplace tab is currently a placeholder overview in `Dashboard.jsx`. The following components and flows need full implementation:
- [ ] **Marketplace Page / View**:
  - Grid of all listed NFTs with filters (Price, Category, AI Originality score, Creator).
- [ ] **Listing Flow**:
  - "List for Sale" modal on minted artwork cards allowing the owner to set a price in ETH.
  - Call `approve()` and `createListing()` on `AuthArtMarketplace.sol`.
- [ ] **Purchase Flow**:
  - "Buy Now" button triggering `buyItem()` with `value: priceInEth`.
  - Automatic on-chain transfer of NFT and royalty distribution.
- [ ] **Creator Reputation System**:
  - Badges for creators with high average originality scores and verified sales history.

---

## 3. UI/UX & Architectural Improvements

| Area | Missing Feature | Impact |
|---|---|---|
| **Routing** | Client-side routing with `react-router-dom` | Clean URLs (`/dashboard`, `/marketplace`, `/artwork/:id`) instead of state-based conditional rendering |
| **State Management** | React Context or Zustand store | Avoid prop-drilling auth state and user profiles between Navbar, Hero, and Dashboard |
| **Notifications** | Toast library (`react-hot-toast` or `sonner`) | Replace inline error/success strings with floating animated notifications |
| **Image Optimization** | Skeleton loaders & progressive image loading | Better UX when loading high-resolution art galleries |
| **Dark / Light Theme** | Theme switcher toggle | Allows users to toggle between dark cyberpunk Web3 mode and light minimalist studio mode |

---

## 4. Priority Implementation Checklist

```text
[High Priority]
  ├── 1. Connect Client-Side Minting via Ethers.js (Phase 4)
  ├── 2. Implement Marketplace Listing & Buy UI (Phase 5)
  └── 3. Add react-router-dom for proper page navigation

[Medium Priority]
  ├── 4. Rich AI Analysis Result Modal with detailed scores (Phase 3)
  ├── 5. Complete Profile Persistence & Avatar Uploads (Phase 2)
  └── 6. Account & Chain change event listeners in auth.js

[Low Priority / Polish]
  ├── 7. Animated radar scanning effect during AI analysis
  ├── 8. Toast notification system (Sonner / React Hot Toast)
  └── 9. Multi-wallet modal (WalletConnect)
```
