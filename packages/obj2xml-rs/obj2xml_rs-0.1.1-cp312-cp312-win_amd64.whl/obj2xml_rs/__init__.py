from ._obj2xml_rs import unparse

import asyncio
from functools import partial


async def unparse_async(*args, **kwargs):
    """
    Asynchronous wrapper for unparse.
    Runs the XML generation in a separate thread to avoid blocking the event loop.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(unparse, *args, **kwargs))


__all__ = ["unparse", "unparse_async"]
