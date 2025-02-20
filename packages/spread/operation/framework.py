from asyncio import sleep


async def loop_operation(operation, *args, **kwargs):
    while True:
        did_something = await operation(*args, **kwargs)
        if did_something is False:
            await sleep(3)
