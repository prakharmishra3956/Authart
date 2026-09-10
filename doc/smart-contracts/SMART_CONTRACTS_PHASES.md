# AuthArt Smart Contracts — Phase-Wise Architecture & Implementation Status

## 1. Overview of Smart Contract Phases

In the AuthArt ecosystem, the smart contract layer powers **Phase 4 (Blockchain & NFT Minting)** and **Phase 5 (NFT Marketplace & Royalty Settlements)**.

```text
+-----------------------------------------------------------------------------------------+
|                              SMART CONTRACT ARCHITECTURE                                |
+-----------------------------------------------------------------------------------------+
| Phase 4: Blockchain, Token Standards & Royalties                                        |
|   - AuthArtNFT.sol (ERC-721 + EIP-2981 Royalties + URI Storage)                         |
|   - AuthArt1155.sol (ERC-1155 Multi-Edition Artwork Token)                              |
+-----------------------------------------------------------------------------------------+
| Phase 5: Decentralized Marketplace & Reputation Engine                                  |
|   - AuthArtMarketplace.sol (Non-Custodial Escrow, EIP-2981 Payouts, Reputation Counter) |
+-----------------------------------------------------------------------------------------+
```

---

## 2. Phase-Wise Status Matrix

| Phase | Standard / Contract | Current Status | Implemented Features |
|---|---|---|---|
| **Phase 4** | `AuthArtNFT.sol` (ERC-721) | ✅ **Core Implemented** | ERC-721 token minting, token URI storage, ERC-2981 royalty configuration per token (`royaltyReceiver`, `royaltyBps`), OpenZeppelin Ownable access control. |
| **Phase 4** | `AuthArt1155.sol` (ERC-1155) | ✅ **Core Implemented** | Multi-edition batch minting, individual per-id token URI management. |
| **Phase 5** | `AuthArtMarketplace.sol` | 🟡 **Partially Complete** | Non-custodial escrow listing, buy function, automatic EIP-2981 royalty deduction, transfer to creator/seller, reputation score counters. |

---

## 3. Detailed Smart Contract Breakdown

### Phase 4: `AuthArtNFT.sol` (ERC-721 + EIP-2981)
- **Inheritance:** `ERC721URIStorage`, `ERC721Royalty`, `Ownable`
- **Core Function:**
  ```solidity
  function mint(
      address to,
      string calldata uri,
      address royaltyReceiver,
      uint96 royaltyBps
  ) external onlyOwner returns (uint256)
  ```
- **Key Characteristics:**
  - Auto-incrementing unique `tokenId`.
  - Configurable on-chain creator royalties (basis points: `500` = 5%).
  - Tracks creator address in `creators[tokenId]`.
  - Supports EIP-2981 interface query (`supportsInterface(0x2a55205a)`).

---

### Phase 4: `AuthArt1155.sol` (ERC-1155 Multi-Edition)
- **Inheritance:** `ERC1155`, `Ownable`
- **Core Function:**
  ```solidity
  function mint(address to, uint256 amount, string calldata tokenUri) external onlyOwner returns (uint256 id)
  ```
- **Key Characteristics:**
  - Allows minting multiple prints/editions of a single digital artwork under a single contract.
  - Dynamically returns token metadata URI per edition ID.

---

### Phase 5: `AuthArtMarketplace.sol` (Marketplace & Settlement)
- **Inheritance:** `ReentrancyGuard`, `Ownable`
- **Core Functions:**
  - `list(address nft, uint256 tokenId, uint256 price)`: Transfers NFT to the marketplace escrow and records the listing.
  - `cancel(uint256 id)`: Cancels the listing and returns the NFT to the seller.
  - `buy(uint256 id)`: Payable function with non-reentrancy protection:
    - Queries `royaltyInfo()` on the NFT contract using EIP-2981.
    - Automatically transfers royalty portion to `royaltyReceiver`.
    - Transfers remainder to `seller`.
    - Transfers NFT to `msg.sender`.
    - Increments `reputation[seller]` and `reputation[buyer]`.
