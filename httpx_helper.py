import asyncio

import httpx
from loguru import logger

_timeout = httpx.Timeout(None, connect=8, read=60)


class HttpNotFound(Exception):
    pass


async def get(url, callback, retry=0, slp=3, **kwargs):
    if 'timeout' in kwargs:
        timeout = kwargs.pop('timeout')
    else:
        timeout = _timeout
    while retry >= 0:
        try:
            async with httpx.AsyncClient(verify=False, timeout=timeout, **kwargs) as client:
                response: httpx.Response = await client.get(url)
                if response.status_code == 404:
                    raise HttpNotFound()
                if asyncio.iscoroutinefunction(callback):
                    ret = await callback(response)
                else:
                    ret = callback(response)
                if ret is not None:
                    return ret
        except Exception as e:
            logger.exception(f"请求url: [{url}]报错")
            if retry > 0 and slp:
                await asyncio.sleep(slp)
        finally:
            retry -= 1


async def post(url, callback, data=None, content=None, retry=0, **kwargs):
    if 'silent' in kwargs:
        silent = kwargs.pop('silent')
    else:
        silent = False
    if 'timeout' in kwargs:
        timeout = kwargs.pop('timeout')
    else:
        timeout = _timeout
    while retry >= 0:
        try:
            async with httpx.AsyncClient(verify=False, timeout=timeout, **kwargs) as client:
                response: httpx.Response = await client.post(url, json=data, content=content)
                ret = callback(response)
                if ret is not None:
                    return ret
        except Exception as e:
            if not silent:
                logger.exception(f"请求url: [{url}]报错")
        finally:
            retry -= 1



