# AuthArt Smart Contracts

Phase 4/5 contract layer for the AuthArt demo.

- `AuthArtNFT.sol`: ERC-721 + ERC-2981 royalties.
- `AuthArt1155.sol`: ERC-1155 collection minting.
- `AuthArtMarketplace.sol`: listing, purchase, royalty settlement and reputation.

## Local chain

```bash
npm install
npx hardhat compile
npx hardhat node
# in another terminal
npx hardhat run scripts/deploy.ts --network localhost
```

Copy the deployed NFT address into `backend/.env`, along with a Hardhat account private key and `RPC_URL=http://127.0.0.1:8545` to enable real contract minting.

The UI also has a safe local-demo fallback when blockchain variables are not configured. Do not describe that fallback as a real on-chain transaction.
