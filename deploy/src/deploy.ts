import { TezosToolkit } from "@taquito/taquito";
import { loadContract, deployContract } from "./utils";

export type DeployParams = {
  // Admin address
  admin: string;

  // TezosToolkitInstance instance
  tezos: TezosToolkit;

  // Timestamp when bidding starts
  biddingStart: string;

  // Timestamp when bidding ends
  biddingEnd: string;

  // Minimum bid price / NFT in mutez
  minBidPrice: string;

  // Tezos address of the NFT contract
  nftContractAddress: string;

  // Total supply of the NFT
  totalSupply: string;
};

export const deploy = async (deployParams: DeployParams): Promise<void> => {
  try {
    // Prepare storage
    const batchAuctionStorage = `(Pair (Pair (Pair {} (Pair "${deployParams.admin}" "${deployParams.biddingEnd}")) (Pair "${deployParams.biddingStart}" (Pair {} {}))) (Pair (Pair ${deployParams.minBidPrice} (Pair 0 0)) (Pair (Pair "${deployParams.nftContractAddress}" {}) (Pair 0 ${deployParams.totalSupply}))))`;

    // Load compiled michelson source code
    const batchAuctionCode = loadContract(`${__dirname}/../../smart_contracts/michelson/batch_auction.tz`);

    console.log(">> Deploying BatchAuction Contract \n\n");

    // Deploy using the taquito utility
    const batchAuctionAddress = await deployContract(batchAuctionCode, batchAuctionStorage, deployParams.tezos);

    console.log(`BatchAuction deployed at: ${batchAuctionAddress}\n\n`);
  } catch (err) {
    console.log(err.message);
  }
};
