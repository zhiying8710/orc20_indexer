
import aiohttp
from environs import Env

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
    async with aiohttp.ClientSession() as session:
        async with session.post(bitcoind_endpoint, json=data, auth=aiohttp.BasicAuth(bitcoind_username, bitcoind_password)) as response:
            data = await response.json()
            if not ret_plain:
                data = data.get('result')
            return data


async def get_tx_detail(txid):
    return await _request('getrawtransaction', [txid, True])


async def get_block_count():
    return await _request('getblockcount', None)


async def get_block_hash(height):
    return await _request('getblockhash', [int(height)])


async def get_block(block_hash, verbosity=1):
    return await _request('getblock', [block_hash, verbosity])




