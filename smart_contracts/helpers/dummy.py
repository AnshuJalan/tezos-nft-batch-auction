import smartpy as sp


class Dummy(sp.Contract):
    @sp.entry_point
    def unknown(self):
        pass

    @sp.entry_point
    def default(self):
        pass
