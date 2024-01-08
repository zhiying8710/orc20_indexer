from environs import Env

import httpx_helper

env = Env()
env.read_env()
ord_endpoint = env.str("ORD_ENDPOINT")


async def _ret_response(response):
    return response


async def _ret_raw(response):
    return await response.content.read()


async def get_block(block: int):
    return await httpx_helper.get(f'/block/{block}', lambda x: x.json())


async def get_inscription_content(inscription_id):
    return await httpx_helper.get(f'/content/{inscription_id}', lambda x: x.content)


