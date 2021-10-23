# NFT Smart Batch Auction

Smart Batch Auctions are an improvement over the traditional first come first serve (FCFS) NFT drops. FCFS design has been in use for a while, but with crypto gaining popularity, the race to occupy block space has been intensifying during NFT drops. Besides leading to general loss of funds due to failed transactions, FCFS strategy is usually timezone dependent and makes it inconvenient for a majority to participate.

A [recent article](https://www.paradigm.xyz/2021/10/a-guide-to-designing-effective-nft-launches/) by Paradigm suggested the use of batch-auctions to alleviate this issue and make NFT launches more efficient and light on the chain. This repo provides a sample implementation of the same on **Tezos blockchain**. The implementation is inspired by a Min Priority Queue based solution given by [FrankIsLost](https://github.com/FrankieIsLost) in a [tweet](https://twitter.com/FrankieIsLost/status/1450490193136422918).

## How does it work?

In a fixed period of time (preferrably spanning at least 24 hours to be timezone agnostic), the participants are asked to place their bids to buy the NFT. A bid consists of two values - **price per NFT** & **quantity**. The participants have to lock up the total value of the proposed bid (i.e quantity \* price) in the smart contract.
Once the bidding period is over, a clearing price is decided and an eligible batch of top bids is cleared at the that uniform price. All unused funds are returned to the bidders irrespective of whether they win or lose.

## Sample Auction

**Total Supply of NFT:** 100

**Minimum Bid Price:** 0.1 tez / NFT

### Bids

| ID  | Price (tez) / NFT | Quantity (NFTs) |
| --- | ----------------- | --------------- |
| 1   | 1                 | 20              |
| 2   | 1.5               | 40              |
| 3   | 2                 | 15              |
| 4   | 1.5               | 25              |
| 5   | 2.5               | 10              |
| 6   | 1.5               | 45              |

### Result

**Clearing Price:** 1.5 tez / NFT

### Final Status

| ID  | NFTs Received | Balance Refunded (tez) |
| --- | ------------- | ---------------------- |
| 1   | 0 / 20        | 20                     |
| 2   | 40 / 40       | 0                      |
| 3   | 15 / 15       | 0                      |
| 4   | 25 / 25       | 0                      |
| 5   | 10 / 10       | 0                      |
| 6   | 10 / 45       | 52.5                   |
