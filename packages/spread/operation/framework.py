from asyncio import sleep


def looping_operation(function):
    async def wrapper(*args, **kwargs):
        while True:
            did_something = await function(*args, **kwargs)
            if did_something is False:
                await sleep(3)

    return wrapper
