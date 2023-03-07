from web3.auto import w3
from eth_account import Account
from mnemonic import Mnemonic

Account.enable_unaudited_hdwallet_features()

mnemonic = Mnemonic("english")
mnemonic_phrase = mnemonic.generate()
print("mnemonic_phrase: ", mnemonic_phrase)

private_key = Account.from_mnemonic(mnemonic_phrase).privateKey.hex()
print("private_key: ", private_key)

public_key = Account.from_key(private_key).address
print("public_key: ", public_key)


