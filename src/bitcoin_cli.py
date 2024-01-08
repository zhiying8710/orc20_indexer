from environs import Env

import httpx_helper
from util import random_string

env = Env()
env.read_env()
bitcoind_endpoint = env.str("BITCOIND_ENDPOINT")
bitcoind_username = env.str("BITCOIND_USERNAME")
bitcoind_password = env.str("BITCOIND_PASSWORD")


async def _request(method, params, ret_plain=False):
    data = {
        'id': f'{method}_{random_string(8)}',
        'method': method,
    }
    if params is not None:
        data['params'] = params
    return await httpx_helper.post(bitcoind_endpoint, lambda x: x.json().get('result') if not ret_plain else x.json(),
                                   data, retry=2,
                                   auth=(bitcoind_username, bitcoind_password))


async def get_tx_detail(txid):
    return await _request('getrawtransaction', [txid, True])


async def get_block_count():
    return await _request('getblockcount', None)


async def get_block_hash(height):
    return await _request('getblockhash', [int(height)])


async def get_block(block_hash, verbosity=1):
    return await _request('getblock', [block_hash, verbosity])




