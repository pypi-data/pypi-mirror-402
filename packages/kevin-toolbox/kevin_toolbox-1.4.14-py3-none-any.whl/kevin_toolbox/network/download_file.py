import os
import time
from tqdm import tqdm
from kevin_toolbox.network import fetch_metadata, fetch_content, get_response
from kevin_toolbox.patches.for_os.path import replace_illegal_chars
from kevin_toolbox.patches import for_os
from kevin_toolbox.nested_dict_list import get_hash

default_option_func_s = {
    "hash_name": lambda url, _, option_s: {"hash_name": get_hash(option_s["name"], length=12)},
    "hash_url": lambda url, _, option_s: {"hash_url": get_hash(url, length=12)},
    "timestamp": lambda *arg, **kwargs: {"timestamp": f'{time.time()}'},
    "legalized_name": lambda url, _, option_s: {
        "legalized_name": replace_illegal_chars(file_name=option_s["name"], b_is_path=False)}
}


def download_file(
        output_dir, url=None, response=None, chunk_size=1024 * 10,
        file_name=None, file_name_format="{legalized_name:.100}{suffix}", format_option_generate_func_ls=None,
        b_allow_overwrite=False, b_display_progress=False, **kwargs
):
    """
        下载文件
            支持以下高级功能：
                1. 自动识别文件类型并命名。
                2. 多次重试。
                3. TODO:断点续传（待实现）。

        参数：
            output_dir:             <path> 文件保存的目录
            url:                    <str> 下载的 URL 地址。
            response:               响应。
                        以上两个参数只需要指定其一即可，建议使用后者。
            chunk_size:             <int> 采用分块下载时，块的大小
                                        默认为 1024 * 10
            file_name:              <str> 文件名
                                        默认为 None，此时将根据 file_name_format 自动生成名字。
            file_name_format:       <str> 保存的文件的命名方式。
                                        基本结构为：  '{<part_0>}...{<part_1>}...'
                                        其中 {} 内将根据 part 指定的选项进行自动填充。目前支持以下几种选项：
                                            - "name"            文件名（不含后缀）。
                                            - "suffix"          后缀。
                                            - "timestamp"       下载的时间戳。
                                            - "hash_name"       文件名的hash值。
                                            - "legalized_name"  经过合法化处理的文件名（对其中特殊符号进行了替换）。
                                            - "hash_url"        url的hash值。
                                        ！！注意：
                                            "name" 该选项由于其可能含有 : 和 / 等特殊符号，当以其作为文件名时，可能会引发错误。
                                                因此对于 windows 用户，请慎重使用该选项，对于 mac 和 linux 用户，同样也不建议使用该选项。
                                                相较而言，"legalized_name" 是一个更好的选择。
                                            "hash_name" 和 "hash_url" 有极低但非0的可能会发生 hash 碰撞。
                                        综合而言：
                                            建议使用 "legalized_name" 和 "suffix" 以及 "timestamp" 的组合。
                                        高级设置：
                                            1. 如果想限制文件名中某部分的长度（避免文件名过长在某些系统下引发报错），应该如何做？
                                                本命名方式兼容 str.format() 语法，比如你可以通过 {name:.10} 来限制名字的长度不大于10个字符。
                                            2. 如果已有的选项无法满足你的需求，如何新增选项？
                                                本函数支持通过设置 format_option_generate_func_ls 来补充或者覆盖默认选项。
                                        默认值为：
                                            '{legalized_name:.100}{suffix}'
            format_option_generate_func_ls: <list of callable> 函数列表，将使用这些函数的结果来对 file_name_format 中的选项进行补充或者覆盖。
                                        函数需要接受 url, response, option_s（已有的选项键值对） 三个参数，并返回一个包含选项名和选项值的 dict。
                                        默认为 None
            b_allow_overwrite:          <boolean> 是否允许覆盖已有文件。
            b_display_progress:         <boolean> 显示进度条。


        返回：
          文件完整路径（下载成功）或空字符串（失败）
    """
    global default_option_func_s
    assert url is not None or response is not None
    if url is not None:
        response = response or get_response(url=url, **kwargs)
    assert response is not None
    output_dir = os.path.expanduser(output_dir)
    #
    metadata_s = fetch_metadata(url=url, response=response, default_name="", default_suffix="")
    if file_name is None:
        option_s = metadata_s.copy()
        for k, func in default_option_func_s.items():
            if k in file_name_format:
                option_s.update(func(url, response, option_s))
        if isinstance(format_option_generate_func_ls, (list, tuple,)):
            for func in format_option_generate_func_ls:
                assert callable(func)
                option_s.update(func(url, response, option_s))
        file_name = file_name_format.format(**option_s)
    #
    os.makedirs(output_dir, exist_ok=True)
    #
    file_path = os.path.join(output_dir, file_name)
    if os.path.exists(file_path):
        if b_allow_overwrite:
            for_os.remove(path=file_path, ignore_errors=True)
        else:
            raise FileExistsError(f"target {file_path} already exists")

    if metadata_s["content_length"] and b_display_progress:
        pbar = tqdm(total=metadata_s["content_length"], unit="B", unit_scale=True, desc="下载进度")
    else:
        pbar = None

    with open(file_path, "wb") as f:
        for chunk in fetch_content(response=response, chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                if pbar is not None:
                    pbar.update(len(chunk))

    return file_path


# 示例用法
if __name__ == "__main__":
    url_ = "https://i.pinimg.com/736x/28/6a/b1/286ab1eb816dc59a1c72374c75645d80.jpg"
    output_dir = r'./temp/123'
    downloaded_file = download_file(url=url_, output_dir=output_dir, file_name="233.jpg", b_allow_overwrite=True,
                                    b_display_progress=True, chunk_size=100)
