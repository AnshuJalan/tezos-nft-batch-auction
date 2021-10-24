import { TezosToolkit } from "@taquito/taquito";
import { InMemorySigner } from "@taquito/signer";

// Types and utlities
import { deploy, DeployParams } from "./deploy";

const Tezos = new TezosToolkit(`https://${process.argv[2]}.smartpy.io`);

Tezos.setProvider({
  signer: new InMemorySigner(process.env.PRIVATE_KEY as string),
});

// Admin address of the contract
const ADMIN = "tz1ZczbHu1iLWRa88n9CUiCKDGex5ticp19S";

// Timestamp at which the bidding begins
const BIDDING_START = "2021-10-24T13:00:00+05:30";

// Timestamp at which bidding ends
const BIDDING_END = "2021-10-24T18:00:00+05:30";

// Minimum bid price / NFT in mutez
const MIN_BID_PRICE = "1000000";

// Address of the NFT contract
const NFT_CONTRACT_ADDRESS = "KT1VcBHBPDnzqYi51gdeNbq7pohKUToH4PN1";

// Total supply of the NFT
const TOTAL_SUPPLY = "100";

const deployParams: DeployParams = {
  tezos: Tezos,
  admin: ADMIN,
  biddingStart: BIDDING_START,
  biddingEnd: BIDDING_END,
  minBidPrice: MIN_BID_PRICE,
  nftContractAddress: NFT_CONTRACT_ADDRESS,
  totalSupply: TOTAL_SUPPLY,
};

void deploy(deployParams);
