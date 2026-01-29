import time
import functools
from kevin_toolbox.patches.for_logging import build_logger

default_logger = build_logger(
    name=":retry",
    handler_ls=[
        dict(target=None, level="INFO", formatter="%(name)s - %(levelname)s - %(message)s"),
    ]
)


def retry(retries=3, delay=0.5, exceptions=(Exception,), logger=None):
    """
        在函数执行失败时，等待一定时间后重试多次

        参数：
            retries:            <int> 重试次数
                                    默认重试3次
            delay:              <int/float> 每次重试前等待的秒数
                                    默认0.5秒
            exceptions:         <list> 捕获的异常类型
                                    默认捕获所有 Exception

        使用示例：
            @retry(retries=5, delay=2)
            def func():
                ...
    """
    logger = default_logger if logger == "default" else logger

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if logger is not None:
                        logger.info(f"第 {attempt} 次调用 {func.__name__} 失败\n\t异常：{e}\n\t等待 {delay} 秒后重试...")
                    time.sleep(delay)
            # 如果所有重试均失败，则抛出最后一次捕获的异常
            raise last_exception

        return wrapper

    return decorator


if __name__ == '__main__':
    @retry(retries=2, delay=0.3, logger="default")
    def func_(*args, **kwargs):
        if args or kwargs:
            return args, kwargs
        else:
            raise ValueError("no paras")


    print(func_(123))
    func_()
