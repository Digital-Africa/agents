import requests
from web3 import Web3
import json

import os
import sys

packages = '/Users/mo/Documents/GitHub/rnbw/Modules'
module_path = os.path.abspath(os.path.join(packages))
if module_path not in sys.path:
    sys.path.append(module_path)
from puppy_utils.ReadNotion import ReadNotion
from puppy_utils.WriteNotion import WriteNotion
from puppy_utils.PuppyNotion import PuppyNotion
from puppy_utils.Function import Function
from puppy_utils.SecretsAccess import SecretAccess


reader = ReadNotion.ReadNotion()
writer = WriteNotion.WriteNotion()
pull = PuppyNotion.PullNotion()
push = PuppyNotion.PushNotion()
secrets = SecretAccess()

def initiate_web3(network):
    if network == 'Sonic':
        network = 'sonic_mainnet'
    elif network == 'Arbitrum':
        network = 'arbitrum'
    else:
        return None

    ankr_key = secrets.get_token('ANKR')
    ankr = f"https://rpc.ankr.com/{network}/{ankr_key}"
    web3 = Web3(Web3.HTTPProvider(ankr))
    return web3


def human_readable_abbreviated(number) -> str:
    """
    Convert a large integer (like a BigNumber) into a human-readable abbreviated string.

    :param value: The raw integer value.
    :param decimals: Number of token decimals (default is 18 for ETH).
    :return: Abbreviated human-readable string.
    """
    
    # Define suffixes
    suffixes = ['', 'K', 'M', 'B', 'T']
    magnitude = 0
    
    while abs(number) >= 1000 and magnitude < len(suffixes) - 1:
        number /= 1000.0
        magnitude += 1
    
    return f"{number:.2f}{suffixes[magnitude]}".rstrip('0').rstrip('.')

def push_to_contract(token):
    
    token['totalSupply'] = Function().totalSupply(CONTEXT[token['Network']], token['Address'])
    token['balanceOf'] = Function().balanceOf(CONTEXT[token['Network']], token['Address'])
    if token['Address'] == '0x51F5DC1c581e309D73E1c6Ea74176077b3c44e60':
        token['totalSupply'] = token['totalSupply']/1000
        token['balanceOf'] = token['balanceOf']/1000
        
    page_id = token['page_id']

    properties = dict()
    properties['totalSupply'] = writer.number(token['totalSupply'])
    properties['balanceOf'] = writer.number(token['balanceOf'])
    visual_supply = human_readable_abbreviated(token['totalSupply'])
    visual_balance = round(token['balanceOf'], 5)
    properties['Actual Supply'] = writer.text(f"{visual_supply} {token['Name']}")
    properties['Actual Balance'] = writer.text(f"{visual_balance} {token['Name']}")

    body = {'parent': {'database_id': "1b50fcf38494801e843cda14be531c4a"},
            'properties': properties}

    response = push.push_to_notion(body, page_id)
    log = {'status code':response.status_code, 'response': response}
    return log