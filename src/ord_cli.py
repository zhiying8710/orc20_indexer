from environs import Env

import httpx_helper

env = Env()
env.read_env()
ord_endpoint = env.str("ORD_ENDPOINT")
headers = {
    'accept': 'application/json'
}


async def _ret_response(response):
    return response


async def _ret_raw(response):
    return await response.content.read()


async def get_block(block: int):
    return await httpx_helper.get(f'{ord_endpoint}/block/{block}', lambda x: x.json(), headers=headers)


async def get_inscription_content(inscription_id):
    return await httpx_helper.get(f'{ord_endpoint}/content/{inscription_id}', lambda x: x.content, headers=headers)
