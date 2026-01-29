import concurrent.futures
from multiprocessing import Manager
from kevin_toolbox.computer_science.data_structure import Executor
from kevin_toolbox.computer_science.algorithm.parallel_and_concurrent.utils import wrapper_for_mt as wrapper
from kevin_toolbox.computer_science.algorithm.parallel_and_concurrent.utils import DEFAULT_THREAD_NUMS


def multi_thread_execute(executors, worker_nums=DEFAULT_THREAD_NUMS, b_display_progress=True, timeout=None,
                         _hook_for_debug=None):
    """
        多线程执行

        参数：
            executors:                  <list/generator/iterator of Executor> 执行器序列
            worker_nums:                <int> 线程数
            b_display_progress:         <boolean> 是否显示进度条
            timeout:                    <int> 每个线程的最大等待时间，单位是s
                                            默认为 None，表示允许等待无限长的时间
            _hook_for_debug:            <dict/None> 当设置为非 None 值时，将保存中间的执行信息。
                                            包括：
                                                - "execution_order":    执行顺序
                                                - "completion_order":   完成顺序
                                            这些信息与最终结果无关，仅面向更底层的调试需求，任何人都不应依赖该特性
        返回：
            res_ls, failed_idx_ls
            执行结果列表，执行失败的执行器 idx
    """
    executor_ls = []
    for i in executors:
        assert isinstance(i, (Executor,))
        executor_ls.append(i)
    if b_display_progress:
        from tqdm import tqdm
        p_bar = tqdm(total=len(executor_ls))
    else:
        p_bar = None

    if isinstance(_hook_for_debug, dict):
        _execution_orders, _completion_orders = Manager().list(), Manager().list()
    else:
        _execution_orders, _completion_orders = None, None

    res_ls = [None] * len(executor_ls)
    failed_idx_ls = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_nums) as thread_pool:
        # 提交任务
        futures = []
        for i, executor in enumerate(executor_ls):
            future = thread_pool.submit(wrapper, executor, timeout, i, _execution_orders, _completion_orders)
            if b_display_progress:
                future.add_done_callback(lambda _: p_bar.update())
            futures.append(future)

        # 收集结果
        for i, future in enumerate(futures):
            try:
                res, b_success = future.result()
            except:
                b_success = False
            if b_success:
                res_ls[i] = res
            else:
                failed_idx_ls.append(i)

    if b_display_progress:
        p_bar.close()

    if isinstance(_hook_for_debug, (dict,)):
        _hook_for_debug.update({
            "execution_orders": list(_execution_orders),
            "completion_orders": list(_completion_orders)
        })

    return res_ls, failed_idx_ls


if __name__ == '__main__':
    import time


    def func_(i):
        # 模拟部分任务长时间运行，部分任务正常结束
        if i in [2, 3, 7]:
            time.sleep(100)
        elif i in [4, 5, 6]:
            time.sleep(0.01)
        else:
            time.sleep(0.05)
        print(f"任务 {i} 执行完成")
        return i * 2


    hook_for_debug = dict()
    a = time.time()
    results, failed = multi_thread_execute(
        executors=[Executor(func=func_, args=(i,)) for i in range(10)],
        worker_nums=5,
        timeout=0.2,
        _hook_for_debug=hook_for_debug
    )
    gap = time.time() - a
    print("执行结果:", results)
    print("超时失败的任务索引:", failed)
    print("调试信息:", hook_for_debug)
    print("总耗时:", gap)
