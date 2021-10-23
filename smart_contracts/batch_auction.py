import smartpy as sp

MinPriorityQueue = sp.io.import_script_from_url("file:utilities/min_priority_queue.py")
AuctionTypes = sp.io.import_script_from_url("file:types/auction.py")
Errors = sp.io.import_script_from_url("file:types/errors.py")
Addresses = sp.io.import_script_from_url("file:helpers/addresses.py")
Dummy = sp.io.import_script_from_url("file:helpers/dummy.py")
Fa2_NFT = sp.io.import_script_from_url("file:helpers/fa2_NFT.py")

#################
# Default Values
#################

# Minimum bid price per NFT
MIN_BID_PRICE = sp.mutez(100000)

# Timestamp at which bidding starts
BIDDING_START = sp.timestamp(0)

# Timestamp at which bidding ends
BIDDING_END = sp.timestamp(10)

# Total supply for the NFTs
TOTAL_SUPPLY = sp.nat(100)

###########
# Contract
###########


class BatchAuction(sp.Contract, MinPriorityQueue.MinPriorityQueue):
    def __init__(
        self,
        admin=Addresses.ADMIN,
        bidding_start=BIDDING_START,
        bidding_end=BIDDING_END,
        min_bid_price=MIN_BID_PRICE,
        next_bid_id=sp.nat(0),
        bids=sp.big_map(
            l={},
            tkey=sp.TNat,
            tvalue=AuctionTypes.BID_TYPE,
        ),
        bids_priority_queue=sp.map(
            l={},
            tkey=sp.TNat,
            tvalue=sp.TNat,
        ),
        owner_to_bids=sp.big_map(
            l={},
            tkey=sp.TAddress,
            tvalue=sp.TSet(sp.TNat),
        ),
        address_to_balance=sp.big_map(
            l={},
            tkey=sp.TAddress,
            tvalue=sp.TMutez,
        ),
        quantity_under_bid=sp.nat(0),
        total_supply=TOTAL_SUPPLY,
        mint_index=sp.nat(0),
        nft_contract_address=Addresses.NFT,
    ):
        self.init(
            admin=admin,
            bidding_start=bidding_start,
            bidding_end=bidding_end,
            min_bid_price=min_bid_price,
            next_bid_id=next_bid_id,
            bids=bids,
            bids_priority_queue=bids_priority_queue,
            owner_to_bids=owner_to_bids,
            address_to_balance=address_to_balance,
            quantity_under_bid=quantity_under_bid,
            total_supply=total_supply,
            mint_index=mint_index,
            nft_contract_address=nft_contract_address,
        )

        # TODO: write init_type

    @sp.entry_point
    def place_bid(self, params):
        sp.set_type(params, sp.TRecord(price=sp.TNat, quantity=sp.TNat))

        # Verify that bidding period is on-going
        sp.verify(
            (sp.now >= self.data.bidding_start) & (sp.now < self.data.bidding_end),
            Errors.BIDDING_IS_NOT_ACTIVE,
        )

        # Verify that the price is greater than or equals the minimum bid price
        sp.verify(sp.utils.nat_to_mutez(params.price) >= self.data.min_bid_price, Errors.BID_PRICE_BELOW_MINIMUM)

        # Verify that the sent tez amount is correct
        sp.verify(
            sp.amount == (sp.utils.nat_to_mutez(params.price * params.quantity)),
            Errors.INVALID_TEZ_AMOUNT,
        )

        # Track locked funds for the sender
        with sp.if_(~self.data.address_to_balance.contains(sp.sender)):
            self.data.address_to_balance[sp.sender] = sp.mutez(0)
        self.data.address_to_balance[sp.sender] += sp.amount

        # Supply available for bid
        available_for_bid = sp.as_nat(self.data.total_supply - self.data.quantity_under_bid)

        # Quantity that would remain unfilled due to limited supply
        unfilled = sp.local("unfilled", sp.nat(0))
        with sp.if_(params.quantity > available_for_bid):
            unfilled.value = sp.as_nat(params.quantity - available_for_bid)

        # If there is unfilled bid quantity, check if smallest bids can be removed and the current bid
        # be accomodated
        with sp.if_(unfilled.value > 0):
            # Allows breaking of loop
            break_loop = sp.local("break_loop", False)
            with sp.while_((unfilled.value > 0) & ~break_loop.value):
                # Smallest bid
                min_bid = self.data.bids[self.data.bids_priority_queue[1]]

                with sp.if_(min_bid.price >= sp.utils.nat_to_mutez(params.price)):
                    break_loop.value = True
                with sp.else_():
                    # If the smallest bid's quantity is less than or equals the unfilled amount,
                    # delete the entire bid
                    with sp.if_(min_bid.quantity <= unfilled.value):
                        unfilled.value = sp.as_nat(unfilled.value - min_bid.quantity)
                        self.data.quantity_under_bid = sp.as_nat(self.data.quantity_under_bid - min_bid.quantity)
                        self.delete()
                    # Else reduce the quantity for the smallest bid and set unfilled to zero
                    with sp.else_():
                        min_bid.quantity = sp.as_nat(min_bid.quantity - unfilled.value)
                        self.data.quantity_under_bid = sp.as_nat(self.data.quantity_under_bid - unfilled.value)
                        unfilled.value = 0

        # Verify that at least one bid slot is fillable i.e unfilled != quantity
        sp.verify(unfilled.value != params.quantity, Errors.BID_PRICE_TOO_LOW)

        self.data.next_bid_id += 1
        self.data.bids[self.data.next_bid_id] = sp.record(
            quantity=sp.as_nat(params.quantity - unfilled.value),
            price=sp.utils.nat_to_mutez(params.price),
            bidder=sp.sender,
        )

        self.insert(self.data.next_bid_id)

        self.data.quantity_under_bid += sp.as_nat(params.quantity - unfilled.value)

    @sp.entry_point
    def claim(self):
        # Verify that the bidding period is over
        sp.verify(sp.now >= self.data.bidding_end, Errors.BIDDING_IS_STILL_ACTIVE)

        # Verify that claiming is possible for the sender
        sp.verify(self.data.address_to_balance.contains(sp.sender), Errors.CANNOT_CLAIM)

        # NFT contract instance
        c = sp.contract(
            sp.TRecord(
                token_id=sp.TNat,
                amount=sp.TNat,
                address=sp.TAddress,
                metadata=sp.TMap(sp.TString, sp.TBytes),
            ),
            self.data.nft_contract_address,
            "mint",
        ).open_some()

        # Total cost of bought NFTs
        cost = sp.local("cost", sp.nat(0))

        # Clearing price based on the priority queue
        clearing_price = self.data.bids[self.data.bids_priority_queue[1]].price

        # Loop through winning bids and mint the NFTs
        with sp.for_("bid_id", self.data.owner_to_bids[sp.sender].elements()) as bid_id:
            cost.value += self.data.bids[bid_id].quantity * sp.utils.mutez_to_nat(clearing_price)
            with sp.for_("x", sp.range(1, self.data.bids[bid_id].quantity + 1)):
                sp.transfer(
                    sp.record(
                        token_id=self.data.mint_index,
                        amount=sp.nat(1),
                        address=sp.sender,
                        metadata={"": sp.utils.bytes_of_string("https://example.com")},
                    ),
                    sp.tez(0),
                    c,
                )
                self.data.mint_index += 1

        # Send price cost to admin
        sp.send(self.data.admin, sp.utils.nat_to_mutez(cost.value))

        # Return left over funds to bid owner
        sp.send(sp.sender, self.data.address_to_balance[sp.sender] - sp.utils.nat_to_mutez(cost.value))

        # Delete owner from balances big map
        del self.data.address_to_balance[sp.sender]


if __name__ == "__main__":
    ##########################
    # place_bid (no unfilled)
    ##########################

    @sp.add_test(name="place_bid works correctly when there is no unfilled supply")
    def test():
        scenario = sp.test_scenario()

        auction = BatchAuction()
        scenario += auction

        # When ALICE places a bid for 20 NFTs at 1000000 mutez each
        scenario += auction.place_bid(price=1000000, quantity=20).run(
            sender=Addresses.ALICE,
            amount=sp.tez(20),
        )

        # The storage is updated properly
        scenario.verify(
            auction.data.bids[1]
            == sp.record(
                price=sp.mutez(1000000),
                quantity=20,
                bidder=Addresses.ALICE,
            )
        )
        scenario.verify(auction.data.bids_priority_queue[1] == 1)
        scenario.verify_equal(auction.data.owner_to_bids[Addresses.ALICE], sp.set([1]))
        scenario.verify(auction.data.address_to_balance[Addresses.ALICE] == sp.tez(20))
        scenario.verify(auction.data.quantity_under_bid == 20)

        # When BOB places a bid for 30 NFTs at 500000 mutez each
        scenario += auction.place_bid(price=500000, quantity=30).run(
            sender=Addresses.BOB,
            amount=sp.tez(15),
        )

        # The storage is updated properly
        scenario.verify(
            auction.data.bids[2]
            == sp.record(
                price=sp.mutez(500000),
                quantity=30,
                bidder=Addresses.BOB,
            )
        )
        scenario.verify_equal(auction.data.owner_to_bids[Addresses.BOB], sp.set([2]))
        scenario.verify(auction.data.address_to_balance[Addresses.BOB] == sp.tez(15))
        scenario.verify(auction.data.quantity_under_bid == 50)

        # BOB's bid takes up the minimal position in the queue
        scenario.verify(auction.data.bids_priority_queue[1] == 2)
        scenario.verify(auction.data.bids_priority_queue[2] == 1)

        scenario += auction.place_bid(price=800000, quantity=30).run(
            sender=Addresses.BOB,
            amount=sp.tez(24),
        )

    #######################
    # place_bid (unfilled)
    #######################

    @sp.add_test(name="place_bid works correctly when smallest bid is partially removed")
    def test():
        scenario = sp.test_scenario()

        # Add two bids such that they leave only 10 NFTs in remaining supply
        auction = BatchAuction(
            bids=sp.big_map(
                {
                    1: sp.record(price=sp.mutez(1000000), quantity=50, bidder=Addresses.ALICE),
                    2: sp.record(price=sp.mutez(2000000), quantity=40, bidder=Addresses.BOB),
                }
            ),
            bids_priority_queue=sp.map({1: 1, 2: 2}),
            quantity_under_bid=90,
            next_bid_id=2,
        )
        scenario += auction

        # When JOHN bids for 20 NFTs at a price of 1500000 per NFT
        scenario += auction.place_bid(price=1500000, quantity=20).run(
            sender=Addresses.JOHN,
            amount=sp.tez(30),
        )

        # Then ALICE's bid drops by 10 NFTs
        scenario.verify(auction.data.bids[1].quantity == 40)

        # The storage is updated correctly
        scenario.verify_equal(auction.data.bids_priority_queue, {1: 1, 2: 2, 3: 3})
        scenario.verify(auction.data.quantity_under_bid == 100)

    @sp.add_test(name="place_bid works correctly when smallest bid is completely removed")
    def test():
        scenario = sp.test_scenario()

        # Add two bids such that they leave only 10 NFTs in remaining supply
        auction = BatchAuction(
            bids=sp.big_map(
                {
                    1: sp.record(price=sp.mutez(1000000), quantity=50, bidder=Addresses.ALICE),
                    2: sp.record(price=sp.mutez(2000000), quantity=40, bidder=Addresses.BOB),
                }
            ),
            bids_priority_queue=sp.map({1: 1, 2: 2}),
            owner_to_bids=sp.big_map(
                l={
                    Addresses.ALICE: sp.set([1]),
                    Addresses.BOB: sp.set([2]),
                }
            ),
            quantity_under_bid=90,
            next_bid_id=2,
        )
        scenario += auction

        # When JOHN bids for 70 NFTs at a price of 1500000 per NFT
        scenario += auction.place_bid(price=1500000, quantity=70).run(
            sender=Addresses.JOHN,
            amount=sp.tez(105),
        )

        # Then ALICE's bid is removed from the priority queue
        scenario.verify(sp.len(auction.data.owner_to_bids[Addresses.ALICE]) == 0)
        scenario.verify_equal(auction.data.bids_priority_queue, {1: 3, 2: 2})

        # JOHN's bid is only 60 NFTs (10 unfilled at the end)
        scenario.verify(auction.data.bids[3].quantity == 60)

        # The storage is updated correctly
        scenario.verify(auction.data.quantity_under_bid == 100)

    @sp.add_test(
        name="place_bid works correctly when smallest bid is completely removed and second smallest bid is partly removed"
    )
    def test():
        scenario = sp.test_scenario()

        # Add two bids such that they leave only 10 NFTs in remaining supply
        auction = BatchAuction(
            bids=sp.big_map(
                {
                    1: sp.record(price=sp.mutez(1000000), quantity=50, bidder=Addresses.ALICE),
                    2: sp.record(price=sp.mutez(2000000), quantity=40, bidder=Addresses.BOB),
                }
            ),
            bids_priority_queue=sp.map({1: 1, 2: 2}),
            owner_to_bids=sp.big_map(
                l={
                    Addresses.ALICE: sp.set([1]),
                    Addresses.BOB: sp.set([2]),
                }
            ),
            quantity_under_bid=90,
            next_bid_id=2,
        )
        scenario += auction

        # When JOHN bids for 70 NFTs at a price of 2500000 per NFT
        scenario += auction.place_bid(price=2500000, quantity=70).run(
            sender=Addresses.JOHN,
            amount=sp.tez(175),
        )

        # Then ALICE's bid is removed from the priority queue
        scenario.verify(sp.len(auction.data.owner_to_bids[Addresses.ALICE]) == 0)
        scenario.verify_equal(auction.data.bids_priority_queue, {1: 2, 2: 3})

        # and BOB's bid quantity is reduced by 10
        scenario.verify(auction.data.bids[2].quantity == 30)

        # and JOHN's bid is completely filled
        scenario.verify(auction.data.bids[3].quantity == 70)

        # The storage is updated correctly
        scenario.verify(auction.data.quantity_under_bid == 100)

    ########
    # claim
    ########

    @sp.add_test(name="claim works properly for just one winning bid")
    def test():
        scenario = sp.test_scenario()

        dummy1 = Dummy.Dummy()
        dummy2 = Dummy.Dummy()
        dummy_admin = Dummy.Dummy()
        fa2_nft = Fa2_NFT.FA2(
            Fa2_NFT.FA2_config(),
            sp.utils.metadata_of_url("https://example/com"),
            Addresses.ADMIN,
        )
        auction = BatchAuction(
            admin=dummy_admin.address,
            bids=sp.big_map(
                l={
                    1: sp.record(quantity=40, price=sp.mutez(1000000), bidder=dummy1.address),
                    2: sp.record(quantity=60, price=sp.mutez(1500000), bidder=dummy2.address),
                }
            ),
            bids_priority_queue=sp.map(l={1: 1, 2: 2}),
            owner_to_bids=sp.big_map(
                l={
                    dummy1.address: sp.set([1]),
                    dummy2.address: sp.set([2]),
                }
            ),
            address_to_balance=sp.big_map(
                l={
                    dummy1.address: sp.tez(40),
                    dummy2.address: sp.tez(90),
                }
            ),
            nft_contract_address=fa2_nft.address,
        )

        auction.set_initial_balance(sp.tez(130))

        scenario += fa2_nft
        scenario += dummy1
        scenario += dummy2
        scenario += dummy_admin
        scenario += auction

        # update admin of the NFT contract for minting
        scenario += fa2_nft.set_administrator(auction.address).run(sender=Addresses.ADMIN)

        # NOTICE: Clearing price is 1 tez or 1000000 mutez

        # When Dummy 1 claims their NFTs (40)
        scenario += auction.claim().run(sender=dummy1.address, now=sp.timestamp(10))

        # Dummy admin's balance equals the cost i.e 40 tez
        scenario.verify(dummy_admin.balance == sp.tez(40))

        # The auction contract's balance is reduced by 40 tez
        scenario.verify(auction.balance == sp.tez(90))

        # Dummy 1 is removed from address_to_balance mapping
        scenario.verify(~auction.data.address_to_balance.contains(dummy1.address))

        # Correct number of NFTs are minted for Dummy1
        scenario.verify(
            fa2_nft.data.ledger.contains((dummy1.address, 0)) & fa2_nft.data.ledger.contains((dummy1.address, 39))
        )

        # When Dummy 2 claims their NFTs (60)
        scenario += auction.claim().run(sender=dummy2.address, now=sp.timestamp(10))

        # Dummy admin's balance equals the previous cost + current cost(60 tez) i.e 100 tez
        scenario.verify(dummy_admin.balance == sp.tez(100))

        # Dummy 2 get a refund of 30 tez  i.e the remaining balance
        scenario.verify(dummy2.balance == sp.tez(30))

        # Correct number of NFTs are minted for Dummy2
        scenario.verify(
            fa2_nft.data.ledger.contains((dummy2.address, 40)) & fa2_nft.data.ledger.contains((dummy2.address, 99))
        )

        # The auction contract's balance is now zero
        scenario.verify(auction.balance == sp.tez(0))

        # Dummy 2 is removed from address_to_balance mapping
        scenario.verify(~auction.data.address_to_balance.contains(dummy2.address))

    @sp.add_test(name="claim works properly for zero winning bids and gives full refund")
    def test():
        scenario = sp.test_scenario()

        dummy1 = Dummy.Dummy()
        dummy_admin = Dummy.Dummy()
        fa2_nft = Fa2_NFT.FA2(
            Fa2_NFT.FA2_config(),
            sp.utils.metadata_of_url("https://example/com"),
            Addresses.ADMIN,
        )
        auction = BatchAuction(
            admin=dummy_admin.address,
            bids=sp.big_map(
                l={
                    1: sp.record(quantity=40, price=sp.mutez(1000000), bidder=dummy1.address),
                }
            ),
            owner_to_bids=sp.big_map(
                l={
                    dummy1.address: sp.set([]),
                }
            ),
            address_to_balance=sp.big_map(
                l={
                    dummy1.address: sp.tez(40),
                }
            ),
            nft_contract_address=fa2_nft.address,
        )

        auction.set_initial_balance(sp.tez(40))

        scenario += fa2_nft
        scenario += dummy1
        scenario += dummy_admin
        scenario += auction

        # update admin of the NFT contract for minting
        scenario += fa2_nft.set_administrator(auction.address).run(sender=Addresses.ADMIN)

        # When Dummy 1 calls claim
        scenario += auction.claim().run(sender=dummy1.address, now=sp.timestamp(10))

        # The auction contract's balance is reduced by 40 tez
        scenario.verify(auction.balance == sp.tez(0))

        # Dummy 1 gets full refund
        scenario.verify(dummy1.balance == sp.tez(40))

        # Dummy 1 is removed from address_to_balance mapping
        scenario.verify(~auction.data.address_to_balance.contains(dummy1.address))

        # Dummy admin's balance stays zero
        scenario.verify(dummy_admin.balance == sp.tez(0))

    @sp.add_test(name="claim works properly for multiple winning bids")
    def test():
        scenario = sp.test_scenario()

        dummy1 = Dummy.Dummy()
        dummy_admin = Dummy.Dummy()
        fa2_nft = Fa2_NFT.FA2(
            Fa2_NFT.FA2_config(),
            sp.utils.metadata_of_url("https://example/com"),
            Addresses.ADMIN,
        )
        auction = BatchAuction(
            admin=dummy_admin.address,
            bids=sp.big_map(
                l={
                    1: sp.record(quantity=40, price=sp.mutez(1000000), bidder=dummy1.address),
                    2: sp.record(quantity=60, price=sp.mutez(2000000), bidder=dummy1.address),
                }
            ),
            bids_priority_queue=sp.map({1: 1, 2: 2}),
            owner_to_bids=sp.big_map(
                l={
                    dummy1.address: sp.set([1, 2]),
                }
            ),
            address_to_balance=sp.big_map(
                l={
                    dummy1.address: sp.tez(160),
                }
            ),
            nft_contract_address=fa2_nft.address,
        )

        auction.set_initial_balance(sp.tez(160))

        scenario += fa2_nft
        scenario += dummy1
        scenario += dummy_admin
        scenario += auction

        # update admin of the NFT contract for minting
        scenario += fa2_nft.set_administrator(auction.address).run(sender=Addresses.ADMIN)

        # NOTICE: The clearing price is set to 1 tez or 1000000 mutez

        # When Dummy 1 calls claim
        scenario += auction.claim().run(sender=dummy1.address, now=sp.timestamp(10))

        # The auction contract's balance is reduced to 0 tez
        scenario.verify(auction.balance == sp.tez(0))

        # Dummy 1 gets refund of 80 tez
        scenario.verify(dummy1.balance == sp.tez(60))

        # Dummy 1 is removed from address_to_balance mapping
        scenario.verify(~auction.data.address_to_balance.contains(dummy1.address))

        # Correct NFTs are minted for dummy1
        scenario.verify(
            fa2_nft.data.ledger.contains((dummy1.address, 0)) & fa2_nft.data.ledger.contains((dummy1.address, 99))
        )

        # Dummy admin's balance is the cost price
        scenario.verify(dummy_admin.balance == sp.tez(100))


sp.add_compilation_target("batch_auction", BatchAuction())
