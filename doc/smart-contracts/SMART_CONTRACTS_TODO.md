# AuthArt Smart Contracts — Pending Tasks & Implementation Roadmap

This document outlines all pending smart contract enhancements, test coverage, and security requirements to make the on-chain infrastructure production-ready.

---

## 1. Pending Tasks by Category

### Category 1: Contract Features & Security Enhancements

- [ ] **1.1 Add Solidity Events (Audit & Indexing Requirement)**
  - **Issue:** `AuthArtNFT.sol` and `AuthArtMarketplace.sol` currently emit no custom events.
  - **Action:** Add:
    ```solidity
    event ArtworkMinted(uint256 indexed tokenId, address indexed creator, address indexed recipient, string tokenURI, uint96 royaltyBps);
    event ItemListed(uint256 indexed listingId, address indexed seller, address indexed nft, uint256 tokenId, uint256 price);
    event ItemSold(uint256 indexed listingId, address indexed buyer, address indexed seller, uint256 price, uint256 royaltyPaid, address royaltyReceiver);
    event ItemCanceled(uint256 indexed listingId, address indexed seller);
    ```

- [ ] **1.2 Safe Ether Transfers in Marketplace**
  - **Issue:** `buy()` uses `payable(receiver).transfer(...)` which has a 2300 gas limit and can fail if the receiver is a smart contract (e.g. Gnosis Safe / multisig).
  - **Action:** Replace with OpenZeppelin's `Address.sendValue(payable(receiver), royalty)` or the call pattern:
    ```solidity
    (bool sent, ) = payable(receiver).call{value: royalty}("");
    require(sent, "Royalty transfer failed");
    ```

- [ ] **1.3 OpenZeppelin v5 Compatibility & Access Control**
  - **Issue:** `AuthArtNFT.sol` uses `_burn(tokenId)` and constructor syntax designed for OZ v4.
  - **Action:** Upgrade to OpenZeppelin v5 contracts with `ERC721URIStorage` + `ERC2981` inheritance and `Ownable(msg.sender)`.

- [ ] **1.4 Direct Creator Minting with Cryptographic Voucher / Signature**
  - **Issue:** Currently only `onlyOwner` (the backend relayer) can call `mint()`.
  - **Action:** Implement EIP-712 signature voucher minting so creators can mint directly with a signature issued by the AI verification engine, paying their own gas without backend relayer gas costs.

---

### Category 2: Automated Testing Suite (`test/`)

- [ ] **2.1 Comprehensive Unit Tests (`AuthArtNFT.test.ts`)**
  - [ ] Test successful minting and token ID incrementation.
  - [ ] Test that `onlyOwner` restriction blocks unauthorized minting.
  - [ ] Test `tokenURI()` retrieval matches metadata.
  - [ ] Test `royaltyInfo(tokenId, salePrice)` calculates the exact royalty basis points (e.g., 500 bps = 5%).

- [ ] **2.2 Marketplace Integration Tests (`AuthArtMarketplace.test.ts`)**
  - [ ] Test listing creation with token escrow.
  - [ ] Test listing cancellation and NFT return.
  - [ ] Test item purchase with accurate split: seller payment + creator EIP-2981 royalty transfer.
  - [ ] Test buyer and seller reputation increments on sale completion.
  - [ ] Test reentrancy attack prevention on `buy()`.

---

### Category 3: Multi-Network Deployment & Verification Scripts

- [ ] **3.1 Testnet Deployment Scripts (`scripts/deploy-testnet.ts`)**
  - Setup deployment configurations for Ethereum Sepolia, Base Sepolia, and Polygon Amoy in `hardhat.config.js`.
- [ ] **3.2 Automatic Etherscan Contract Verification**
  - Configure `@nomicfoundation/hardhat-verify` and add API keys for Sepolia Etherscan / Polygonscan.

---

## 2. Priority Implementation Checklist

```text
[High Priority]
  ├── 1. Add custom Solidity events to AuthArtNFT and AuthArtMarketplace
  ├── 2. Replace payable.transfer() with call{value: ...} for safe multisig transfers
  └── 3. Create full automated test suite (test/AuthArtNFT.test.ts & test/Marketplace.test.ts)

[Medium Priority]
  ├── 4. Configure Sepolia & Polygon testnet networks in hardhat.config.js
  ├── 5. Add contract verification scripts for block explorers
  └── 6. Implement EIP-712 voucher minting for decentralized creator gas payments

[Low Priority / Advanced]
  └── 7. Explore LayerZero cross-chain minting adapter for multi-chain distribution
```
