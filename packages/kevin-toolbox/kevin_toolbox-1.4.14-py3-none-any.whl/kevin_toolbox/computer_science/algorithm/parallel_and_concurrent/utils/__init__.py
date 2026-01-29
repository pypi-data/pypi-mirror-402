from .wrapper_with_timeout_1 import wrapper_with_timeout_1
from .wrapper_with_timeout_2 import wrapper_with_timeout_2

import signal
import multiprocessing

if callable(getattr(signal, "setitimer", None)):
    wrapper_for_mp = wrapper_with_timeout_1  # 效率更高，优先选择
else:
    wrapper_for_mp = wrapper_with_timeout_2

wrapper_for_mt = wrapper_with_timeout_2

DEFAULT_PROCESS_NUMS = multiprocessing.cpu_count() + 2
DEFAULT_THREAD_NUMS = DEFAULT_PROCESS_NUMS * 2
