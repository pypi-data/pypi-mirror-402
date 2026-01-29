from multiprocessing import Process, Queue


def __inner_wrapper(q, executor):
    try:
        res = executor.run()
        q.put((res, True))
    except:
        q.put((None, False))


def wrapper_with_timeout_2(executor, timeout=None, idx=-1, _execution_orders=None, _completion_orders=None):
    """
        限制执行时间，使用 multiprocessing.Process 强制终止超时任务
            该函数适用于多线程、多进程以及所有操作系统，但是效率相较于 wrapper_with_timeout_1 较差

        参数:
            executor:               <Executor>执行器，需实现 run() 方法
            idx:                    <int> 任务索引（用于调试）
            timeout:                <int/float>最大等待时间（单位：秒，支持 float）
            _execution_orders, _completion_orders: 用于记录调试信息的 Manager.list
        返回:
            (result, b_success)     若超时或异常则 b_success 为 False
    """
    if _execution_orders is not None:
        _execution_orders.append(idx)

    res, b_success = None, False
    if timeout is not None:
        q = Queue()
        p = Process(target=__inner_wrapper, args=(q, executor))
        p.start()
        p.join(timeout)  # 最多等待 timeout 秒

        if q.qsize():
            try:
                res, b_success = q.get_nowait()
            except:
                pass
        if p.is_alive():
            p.terminate()
            p.join()
    else:
        try:
            res, b_success = executor.run(), True
        except:
            pass

    if b_success:
        if _completion_orders is not None:
            _completion_orders.append(idx)
    return res, b_success


if __name__ == '__main__':
    import time


    def func_(i):
        if i in [2, 3, 7]:
            time.sleep(300)
        else:
            time.sleep(0.5)
        return i * 2


    from kevin_toolbox.computer_science.data_structure import Executor

    print(wrapper_with_timeout_2(Executor(func=func_, args=(2,)), timeout=1))
    print(wrapper_with_timeout_2(Executor(func=func_, args=(1,)), timeout=1))

    execution_orders = []
    completion_orders = []
    print(wrapper_with_timeout_2(Executor(func=func_, args=(2,)), timeout=1, _execution_orders=execution_orders,
                                 _completion_orders=completion_orders))
    print(execution_orders, completion_orders)
