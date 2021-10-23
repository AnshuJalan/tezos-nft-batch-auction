# Smart Contracts

`batch_auction.py` is the primary contract that handles the NFT auction. This contract should in theory replace the traditional NFT crowdsale contract. The implementation provided here is 'raw', and needs to be customized to suit the associated project.

All contracts are written in [SmartPy](https://smartpy.io). Refer to there elaborate [documentation](https://docs.smartpy.io) for further understanding.

## Folder Structure

- `helpers` : Consists of test helpers like an FA2 NFT contract, a dummy contract to handle tez transfers and dummy addresses.
- `michelson` : Compiled michelson code for the Batch Auction contract.
- `types` : Types and error statements used across the contract.
- `utilities` : Files consisting of logic that is required in `batch_auction.py`

## Compilation

A shell script has been provided to assist compilation and testing of the contracts. The script can be run using-

```shell
$ bash compile.sh
```

## Design

The batch auction contract makes use of a min priority queue to track the top N bids (N being the total supply). This enables us to find the clearing price in constant time, since the Nth largest bid would be the root of the associated heap.

### Storage

- **admin** : Address of the auction administrator. All NFT sale income is relayed to the admin address.
- **bidding_start** : Timestamp at which the bidding starts.
- **bidding_end** : Timestamp at which the bidding end.
- **min_bid_price** : Minimum bid price (tez / NFT).
- **next_bid_id** : Incrementing non-zero key ID for `bids` big_map.
- **bids** : big_map to store the bids.
- **bids_priority_queue** : map based priority queue abstraction.
- **owner_to_bids** : big_map storing the winning bids.
- **address_to_balance** : big_map keeping track of the total balance locked in the contract for an address.
- **quantity_under_bid** : NFT supply that has already been bidded upon.
- **total_supply** : The total supply of the NFT.
- **mint_index** : token_id for the next NFT that would be minted.
- **nft_contract_address**: Tezos address of the NFT contract.

### Entrypoints

- **place_bid**
  - Parameters: price per NFT in tez, quantity of NFTs
  - Usage: Registers a bid and inserts it at the right position in the priortiy queue.
- **claim**
  - Usage: Allows owners of winning bids to mint the respective NFTs and refunds unused balance to winners and losers alike.
- **reveal_metadata**
  - Parmeters: A list containing the metadata info (token_id, token_info) of the NFTs.
  - Usage: Used to reveal or essentially update the metadata of the tokens, post sale.
