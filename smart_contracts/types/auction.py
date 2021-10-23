import smartpy as sp

# quantity : Number of NFTs
# price    : The price of each NFT in mutez
# bidder   : Wallet address of the bidder
BID_TYPE = sp.TRecord(
    quantity=sp.TNat,
    price=sp.TMutez,
    bidder=sp.TAddress,
).layout(("quantity", ("price", "bidder")))
