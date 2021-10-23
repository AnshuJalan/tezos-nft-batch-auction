import smartpy as sp

Errors = sp.io.import_script_from_url("file:types/errors.py")

METADATA_BATCH_TYPE = sp.TList(
    sp.TRecord(
        token_id=sp.TNat,
        token_info=sp.TMap(sp.TString, sp.TBytes),
    )
)


###############################################
# Utility to update the metadata of the tokens
###############################################


class Reveal:
    @sp.entry_point
    def reveal_metadata(self, param):
        sp.set_type(param, METADATA_BATCH_TYPE)
        sp.verify(sp.sender == self.data.admin, Errors.NOT_AUTHORIZED)

        c = sp.contract(
            METADATA_BATCH_TYPE,
            self.data.nft_contract_address,
            "update_token_metadata",
        ).open_some(Errors.INVALID_NFT_CONTRACT)

        sp.transfer(param, sp.tez(0), c)
