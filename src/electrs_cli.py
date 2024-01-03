import urllib.parse

import aiohttp
from environs import Env

env = Env()
env.read_env()
electrs_endpoint = env.str("ELECTRS_ENDPOINT")


async def _request(_path, data=None, method='get', response_callback=None):
    async with aiohttp.ClientSession() as session:
        if method == 'post':
            async with session.post(f'{electrs_endpoint}{_path}', json=data, headers={
                'accept': 'application/json'
            }) as response:
                if response_callback:
                    return await response_callback(response)
                return await response.json()
        else:
            url = f'{electrs_endpoint}{_path}'
            if data:
                url += '?'
                for key in data:
                    url += f'{key}={urllib.parse.quote(data[key])}'
            async with session.get(url, headers={
                'accept': 'application/json'
            }) as response:
                if response_callback:
                    return await response_callback(response)
                return await response.json()


async def get_tx(txid: str):
    return await _request(f'/tx/{txid}')




