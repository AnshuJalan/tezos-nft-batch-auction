# Deploy

The scripts provided in this folder assist the deployment of the batch auction contract. [Taquito](https://tezostaquito.io/) library to has been used simplify the process.

## Installing Dependencies

To install the dependencies run:

```
$ npm install
```

## Preparing Storage

The storage fields which are required to be mentioned pre-deployment can be set in the `index.ts` file in the `src` folder. The fields to be set are

- `ADMIN` : Admin address for the auction contract.
- `BIDDING_START` : Timestamp at which the bidding begins.
- `BIDDING_END` : Timestamp at which the bidding ends.
- `MIN_BID_PRICE` : Minimum bid price / NFT in mutez.
- `NFT_CONTRACT_ADDRESS` : Address of the NFT contract.
- `TOTAL_SUPPLY` : Total supply of the NFT.

## Deployment

Once the storage is prepared, the deployment can be done by providing a private key as an environment variable and running `deploy:testnet` script:

```
$ PRIVATE_KEY=<Your private key> npm run deploy:testnet
```
