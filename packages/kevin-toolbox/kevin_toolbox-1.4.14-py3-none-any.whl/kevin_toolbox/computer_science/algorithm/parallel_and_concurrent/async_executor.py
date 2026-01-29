import asyncio
from tqdm import tqdm


def async_executor(func, paras_generator, b_use_tqdm=True):
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(_execute(func, paras_generator, b_use_tqdm))
    return res


async def _execute(func, paras_generator, b_use_tqdm):
    async def wrapper(*args, **kwargs):
        res = await func(*args, **kwargs)
        return res

    tasks = []
    if b_use_tqdm:
        paras_generator = tqdm(paras_generator)
    for paras in paras_generator:
        tasks.append(asyncio.ensure_future(wrapper(*paras.get("args", tuple()), **paras.get("kwargs", dict()))))

    res_ls = await asyncio.gather(*tasks)
    return res_ls


if __name__ == '__main__':
    async def func_(i):
        print(i)
        await asyncio.sleep(2)

        return i * 2


    print(async_executor(func=func_, paras_generator=[{"args": [i]} for i in range(1, 10)]))
