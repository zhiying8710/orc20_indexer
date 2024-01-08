import random
import string
import urllib.parse
from typing import Union

import aiohttp
from environs import Env

env = Env()
env.read_env()
ord_endpoint = env.str("ORD_ENDPOINT")


async def _ret_response(response):
    return response


async def _ret_raw(response):
    return await response.content.read()


async def _request(_path, data: Union[dict, None], method='get', response_callback=None):
    async with aiohttp.ClientSession() as session:
        if method == 'post':
            async with session.post(f'{ord_endpoint}{_path}', json=data, headers={
                'accept': 'application/json'
            }) as response:
                if response_callback:
                    return await response_callback(response)
                return await response.json()
        else:
            url = f'{ord_endpoint}{_path}?{data}'
            if data:
                url += '?'
                for key in data:
                    url = f'{key}={urllib.parse.quote(data[key])}'
            async with session.get(url, headers={
                'accept': 'application/json'
            }) as response:
                if response_callback:
                    return await response_callback(response)
                return await response.json()


async def get_block(block: int):
    return await _request(f'/block/{block}', None, response_callback=_ret_response)


async def get_inscription_content(inscription_id):
    return await _request(f'/content/{inscription_id}', None, response_callback=_ret_raw)


