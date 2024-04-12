from typing import Iterable, Optional, Callable
import aiohttp
import asyncio
from asyncio import BoundedSemaphore
import ujson
from aioconsole import aprint


class OptimisedClientError(Exception):
    """Base Error type"""
    pass

class HttpError(OptimisedClientError):
    """Http Related Errors"""
    def __init__(self, custom_message: str, error: Exception, base_class: str) -> None:
        self.message = custom_message
        self.error = error
        self.base_class = base_class

class DeserialisationError(OptimisedClientError):
    """When calling .json() fails"""
    def __init__(self, custom_message: str, error: Exception, base_class: str) -> None:
        self.message = custom_message
        self.error = error
        self.base_class = base_class





class OptimisedHTTP:
    """Aiohttp Wrapper designed with optimisations in mind. 
    """
    def __init__(self, semaphore: int) -> None:
        """
        Args:
            semaphore (int): How many concurrent tasks to be ran at once.
        """
        self.semaphore = BoundedSemaphore(semaphore)

    def __repr__(self) -> str:
        return f"{self.semaphore}"


    async def request(
        self,
        **kwargs,
    ) -> Optional[str]:
        """Sending of request, utilises aiohttp.ClientRequest arguments. Handles ratelimits also.
        Utilises a semaphore to avoid sending too many requests to discord API to avoid connection closes.

        Raises:
            DeserialisationError: Could not get a json response
            HttpError: Http request did not complete

        Returns:
            Optional[str]: Returns OK if successful, else None
        """
        # Semaphore makes sure only n amount of requests are being handled at once, where n is the value set upon instantiation
        # Anything extra means that the semaphore will lock, and they will be waiting in queue 

        async with self.semaphore:
            while True:
                try:
                    async with aiohttp.ClientSession(
                        connector=aiohttp.TCPConnector(
                            ssl=True,
                            keepalive_timeout=10,
                            ttl_dns_cache=204,
                            limit=0,
                            limit_per_host=0,
                        ),
                        trust_env=False,
                        skip_auto_headers=None,
                        json_serialize=ujson.dumps,
                        auto_decompress=True,
                    ) as session:
                        async with session.request(**kwargs) as resp:
                            # await aprint(resp.status, )
                            # await aprint((await resp.text()))
                            if resp.ok:
                                try:
                                    # await aprint((await resp.text()))
                                    return await resp.json()
                                except Exception as e:
                                    return "OK"
                            elif resp.status == 429:
                                try:
                                    json = await resp.json()
                                    await asyncio.sleep(json['retry_after'])
                                except Exception as e:
                                    raise DeserialisationError("Could not retrieve retry_after. Aborting this request", e, self)
                            else:
                                return
                except Exception as e:
                    raise HttpError("HTTP Request failed. Aborting this request", e, self)


    async def requests(
        self, 
        reqs: list[aiohttp.ClientRequest]
    ) -> list[Optional[str]]:
        """Concurrently sends multiple asynchronous requests. Utilises asyncio.gather. Requires a list of aiohttp.ClientRequest objects. See aiohttp docs.

        Args:
            reqs (list[aiohttp.ClientRequest]):  List of aiohttp.ClientRequest objects

        Returns:
            list[Optional[str]]: Returns a list of self.request. OK if successful, None if failed.
        """

        return await asyncio.gather(*(asyncio.create_task(self.request(**req)) for req in reqs), return_exceptions=True)
