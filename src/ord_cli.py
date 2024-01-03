import random
import string

import aiohttp
from environs import Env

env = Env()
env.read_env()
ord_endpoint = env.str("ORD_ENDPOINT")


async def _ret_response(response):
    return response


async def _request(_path, data, method='get', response_callback=None):
    async with aiohttp.ClientSession() as session:
        if method == 'post':
            async with session.post(f'{ord_endpoint}{_path}', json=data, headers={
                'accept': 'application/json'
            }) as response:
                if response_callback:
                    return await response_callback(response)
                return await response.json()
        else:
            async with session.get(f'{ord_endpoint}{_path}?{data}', headers={
                'accept': 'application/json'
            }) as response:
                if response_callback:
                    return await response_callback(response)
                return await response.json()


async def get_block(block: int):
    await _request(f'/block/{block}', response_callback=_ret_response)




