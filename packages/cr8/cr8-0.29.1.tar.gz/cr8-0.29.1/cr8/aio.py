
import functools
import os
import asyncio
import signal
import sys
from collections.abc import Coroutine
try:
    import uvloop

    def run(coro: Coroutine):
        uvloop.run(coro)
except ImportError:

    def run(coro: Coroutine):
        asyncio.run(coro)

from tqdm import tqdm
tqdm = functools.partial(
    tqdm,
    unit=' requests',
    smoothing=0.1,
    disable=os.environ.get('CR8_NO_TQDM') == 'True'
)


async def measure(stats, f, *args, **kws):
    r = await f(*args, **kws)
    duration = r['duration']
    stats.measure(duration)
    return r


async def qmap(q, corof, iterable):
    for i in iterable:
        task = asyncio.ensure_future(corof(*i))
        await q.put(task)
    await q.put(None)


async def consume(q, total=None):
    last_error = None
    with tqdm(total=total) as t:
        while True:
            task = await q.get()
            if task is None:
                break
            try:
                await task
            except Exception as e:
                last_error = e
            t.update(1)
        if last_error:
            raise last_error


async def amap(coro, iterable, total=None):
    for i in tqdm(iterable, total=total):
        await coro(*i)


def interruptable(iterable, is_active):
    for i in iterable:
        if not is_active:
            return
        yield i


def setup_sigint_handling(loop, q, iterable):
    if sys.platform == 'win32':
        return iterable
    is_active = [True]
    iterable = interruptable(iterable, is_active)

    def stop():
        asyncio.ensure_future(q.put(None))
        is_active.clear()
        loop.remove_signal_handler(signal.SIGINT)
    loop.add_signal_handler(signal.SIGINT, stop)
    return iterable


def remove_sigint_handler(loop):
    if sys.platform == 'win32':
        return
    loop.remove_signal_handler(signal.SIGINT)


async def run_many(coro, iterable, concurrency, num_items=None):
    loop = asyncio.get_running_loop()
    if concurrency == 1:
        return await amap(coro, iterable, total=num_items)
    q = asyncio.Queue(maxsize=concurrency)
    iterable = setup_sigint_handling(loop, q, iterable)
    tasks = asyncio.gather(
        qmap(q, coro, iterable),
        consume(q, total=num_items)
    )
    try:
        await tasks
    except KeyboardInterrupt:
        tasks.cancel()
    remove_sigint_handler(loop)
