import requests
from web3 import Web3
from SecretAccessor import SecretAccessor


import os
import sys

packages = '/Users/mo/Documents/GitHub/rnbw/Modules'
module_path = os.path.abspath(os.path.join(packages))
if module_path not in sys.path:
    sys.path.append(module_path)


class Function(object):
    """docstring for Assets"""

    def __init__(self):
        super(Function, self).__init__()
        self.wallet = "0x200b0E0b2030c4F9fba3312C3C7505b9050aaFD6"
        self.ankr = SecretAccessor().get_secret("ANKR")
                
    def web3(self, Network):
        if Network == "sonic":
            rpc_url = f"https://rpc.ankr.com/sonic_mainnet/{self.ankr}"
            web3 = Web3(Web3.HTTPProvider(rpc_url))
            return web3
        elif Network == "base":
            rpc_url = f"https://rpc.ankr.com/base_mainnet/{self.ankr}"
            web3 = Web3(Web3.HTTPProvider(rpc_url))
            return web3
        elif Network == "arbitrum":
            rpc_url = f"https://rpc.ankr.com/arbitrum_mainnet/{self.ankr}"
            web3 = Web3(Web3.HTTPProvider(rpc_url))
            return web3
        elif Network == "optimism":
            rpc_url = f"https://rpc.ankr.com/optimism_mainnet/{self.ankr}"
            web3 = Web3(Web3.HTTPProvider(rpc_url))
            return web3
        else:
            raise ValueError(f"Invalid network: {Network}")

    def totalSupply(self, token_address, Network):
        web3 = self.web3(Network)
        abi_token_supply = [
                            {
                                'inputs': [],
                                'name': 'decimals',
                                'outputs': [
                                            {
                                                'internalType': 'uint8',
                                                'name': '',
                                                'type': 'uint8'
                                            }
                                            ],
                                'stateMutability': 'view',
                                'type': 'function'
                            },
                            {
                                'inputs': [],
                                'name': 'totalSupply',
                                'outputs': [
                                            {
                                                'internalType': 'uint256',
                                                'name': '',
                                                'type': 'uint256'
                                            }
                                            ],
                                'stateMutability': 'view',
                                'type': 'function'
                            }
                            ]
        contract = web3.eth.contract(
                                address=token_address,
                                abi=abi_token_supply
                                )
        raw_supply = contract.functions.totalSupply().call()
        decimals = contract.functions.decimals().call()
        total_supply = raw_supply/10**decimals
        return total_supply

    def balanceOf(self, token_address, Network):
        web3 = self.web3(Network)
        abi = [{
                    "constant": True,
                    "inputs": [
                                {
                                    "name": "_owner",
                                    "type": "address"
                                }],
                    "name": "balanceOf",
                    "outputs": [
                                {
                                    "name": "balance",
                                    "type": "uint256"
                                }
                                ],
                    "payable": False,
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [
                                {
                                    "name": "",
                                    "type": "uint8"
                                }
                                ],
                    "payable": False,
                    "stateMutability": "view",
                    "type": "function"
                }]
        contract = web3.eth.contract(
                                            address=token_address,
                                            abi=abi
                                            )
        decimal = contract.functions.decimals().call()
        balance = contract.functions.balanceOf(self.wallet).call()/10**decimal
        return balance

    def decimal(self, token_address, Network):
        web3 = self.web3(Network)
        abi = [{
                    "constant": True,
                    "inputs": [
                                {
                                    "name": "_owner",
                                    "type": "address"
                                }],
                    "name": "balanceOf",
                    "outputs": [
                                {
                                    "name": "balance",
                                    "type": "uint256"
                                }
                                ],
                    "payable": False,
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [
                                {
                                    "name": "",
                                    "type": "uint8"
                                }
                                ],
                    "payable": False,
                    "stateMutability": "view",
                    "type": "function"
                }]
        contract = web3.eth.contract(
                                            address=token_address,
                                            abi=abi
                                            )
        decimal = contract.functions.decimals().call()
        return decimal

def simple_oracle(tokenAddress, Network):
    #Network = 'sonic'
    #pairId = '0x94fb2a14d55288d9f7fa10ad79022b95f95c04cb'
    url = f"https://api.dexscreener.com/token-pairs/v1/{Network}/{tokenAddress}"
    # Dictionary of query parameters
    response = requests.get(url)
    response = response.json()
    #pair = response['pairs']
    price = sorted(response, key=lambda x: x['volume']['h24'], reverse = True)[0]
    price = price['priceUsd']
    return float(price)