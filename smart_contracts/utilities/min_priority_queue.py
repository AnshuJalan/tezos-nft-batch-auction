import smartpy as sp

#########################################
# Implementation of a min priority queue
#########################################


class MinPriorityQueue:
    def swap(self, i, j):
        bids_pq = self.data.bids_priority_queue
        bids_pq[i] = bids_pq[i] + bids_pq[j]
        bids_pq[j] = sp.as_nat(bids_pq[i] - bids_pq[j])
        bids_pq[i] = sp.as_nat(bids_pq[i] - bids_pq[j])

    @sp.sub_entry_point
    def insert(self, bid_id):
        bids = self.data.bids
        bids_pq = self.data.bids_priority_queue

        k = sp.local("k", sp.len(bids_pq) + 1)
        bids_pq[sp.len(bids_pq) + 1] = bid_id

        # Swim newly inserted value
        with sp.while_(k.value > 1):
            bid_1 = self.data.bids[bids_pq[k.value // 2]]
            bid_2 = self.data.bids[bids_pq[k.value]]
            with sp.if_(
                (bid_1.price > bid_2.price) | ((bid_1.price == bid_2.price) & (bid_1.quantity > bid_2.quantity))
            ):
                self.swap(k.value // 2, k.value)
                k.value = k.value // 2
            with sp.else_():
                k.value = 0

        # Map the bid id to owner's address
        with sp.if_(~self.data.owner_to_bids.contains(bids[bid_id].bidder)):
            self.data.owner_to_bids[bids[bid_id].bidder] = sp.set()
        self.data.owner_to_bids[bids[bid_id].bidder].add(bid_id)

    @sp.sub_entry_point
    def delete(self):
        bids = self.data.bids
        bids_pq = self.data.bids_priority_queue

        last_index = sp.len(bids_pq)
        root_index = 1

        # Remove smallest bid from its owner's mapping
        min_id = bids_pq[root_index]
        self.data.owner_to_bids[bids[min_id].bidder].remove(min_id)

        self.swap(last_index, root_index)
        del bids_pq[last_index]

        k = sp.local("k", 1)
        j = sp.local("j", 2 * k.value)

        # Sink the root
        with sp.while_((2 * k.value) <= sp.len(bids_pq)):
            with sp.if_(j.value < sp.len(bids_pq)):
                child_1 = bids[bids_pq[j.value]]
                child_2 = bids[bids_pq[j.value + 1]]
                with sp.if_(
                    (child_1.price > child_2.price)
                    | ((child_1.price == child_2.price) & (child_1.quantity > child_2.quantity))
                ):
                    j.value = j.value + 1
                parent = bids[bids_pq[k.value]]
                child = bids[bids_pq[j.value]]
            with sp.if_(
                (parent.price > child.price) | ((parent.price == child.price) & (parent.quantity > child.quantity))
            ):
                self.swap(j.value, k.value)
            with sp.else_():
                # Inflate k so that the loop breaks
                k.value = sp.len(bids_pq)
