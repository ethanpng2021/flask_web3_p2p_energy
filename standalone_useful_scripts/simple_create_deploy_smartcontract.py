from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
from solcx import compile_standard
from solcx import install_solc
import json
import os
import datetime
import time

# Connect to an Ethereum client (Sign up for an account at Infura and copy your link here)
w3 = Web3(Web3.HTTPProvider("https://goerli.infura.io/v3/309c3e539......cf7b7ee265"))

# The address that will deploy the contract
deployer_address = '0xC0B7B0B742e6b323536Ad02f3'

# The private key of the deployer
private_key = '0x95a109dae774a2ddc32ea80e0f1f60f0c62ce1a0ff1efed6c5f10ec552603246'

# The gas price and gas limit for the deployment transaction
# You have to modify the gas price and gas limit at different times of the day.
gas_price = w3.toWei('20', 'gwei')
gas_limit = 1000000

contract_source_code = '''
pragma solidity ^0.5.3;

contract EcommerceStore {
    // The mapping of product IDs to product information
    mapping (uint256 => Product) public products;

    // The struct that defines the product information
    struct Product {
        uint256 id;
        string name;
        uint256 price;
    }

    // The event that is emitted when a product is added
    event ProductAdded(uint256 id, string name, uint256 price);

    // The function that adds a new product to the store
    function addProduct(uint256 id, string memory name, uint256 price) public {
        products[id] = Product(id, name, price);
        emit ProductAdded(id, name, price);
    }

    // The function that returns the information of a product
    function getProduct(uint256 id) public view returns (string memory, uint256) {
        Product memory product = products[id];
        return (product.name, product.price);
    }
}
'''

# Compile the smart contract
compiled_contract = compile_standard({
    "language": "Solidity",
    "sources": {
        "Info.sol": {
            "content": contract_source_code
        }
    },
    "settings": {
        "outputSelection": {
            "*": {
                "*": [
                    "abi",
                    "evm.bytecode"
                ]
            }
        }
    }
})

contract_interface = compiled_contract["contracts"]["Info.sol"]["EcommerceStore"]
contract_bytecode = contract_interface["evm"]["bytecode"]["object"]
contract_abi = contract_interface["abi"]

# Prepare the contract deployment transaction
contract = w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)
transaction = contract.constructor().buildTransaction({
    'from': deployer_address,
    'gas': gas_limit,
    'gasPrice': gas_price,
    'nonce': w3.eth.getTransactionCount(deployer_address)
})

# Sign and send the deployment transaction
signed_transaction = w3.eth.account.signTransaction(transaction, private_key=private_key)
tx_hash = w3.eth.sendRawTransaction(signed_transaction.rawTransaction)

# Wait for the contract deployment transaction to be mined
tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)

# The contract address is the address of the deployed contract
contract_address = tx_receipt['contractAddress']
print("Contract deployed at", contract_address)

# Verify the deployment
contract_instance = w3.eth.contract(
    address=contract_address,
    abi=contract_interface['abi']
)

product_id = 8
product_name = "Uniqlo S Shirt"
product_price = 95

# 5. Build increment tx
increment_tx = contract_instance.functions.addProduct(product_id, product_name, product_price).buildTransaction(
    {
        'from': deployer_address,
        'gas': gas_limit,
        'gasPrice': gas_price,
        'nonce': w3.eth.getTransactionCount(deployer_address)
    }
)

# 6. Sign tx with PK
tx_create = w3.eth.account.sign_transaction(increment_tx, private_key=private_key)

# 7. Send tx and wait for receipt
tx_hash = w3.eth.send_raw_transaction(tx_create.rawTransaction)
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

#print(f'Tx successful with hash: { tx_receipt.transactionHash.hex() }')

# 8. Call product id to check
product = contract_instance.functions.getProduct(8).call()
print(f"Product name: {product[0]}, Price: {product[1]}")
#print(product)

# 9. Finally,
# Verify at https://goerli.etherscan.io/ by entering the contract address
