import os
from collections import defaultdict
import warnings
import time
from kevin_toolbox.patches.for_os import find_files_in_dir, copy, remove

# 获取文件的时间,返回time.struct_time格式
get_timestamp_method_s = dict(
    c=lambda file_path: time.localtime(max(os.path.getctime(file_path), 0)),
    a=lambda file_path: time.localtime(max(os.path.getatime(file_path), 0)),
    m=lambda file_path: time.localtime(max(os.path.getmtime(file_path), 0))
)


def group_files_by_timestamp(input_dir, output_dir=None, suffix_ls=None, b_ignore_case=True,
                             grouping_rule=("%Y", "%m_%d"), timestamp_type="m", b_keep_source=True, b_verbose=False):
    """
        将 input_dir 中的文件按照时间戳信息进行分组，输出到 output_dir 中

        参数：
            input_dir:              输入目录
            output_dir:             输出目录
                                        当设置为 None 时，将进行空跑，不实际复制文件到 output_dir 中
            suffix_ls:              <list of path/None> 指定要对带有哪些后缀的文件进行处理
                                        默认为 None 表示对所有文件都进行处理
            b_ignore_case:          <boolean> 忽略大小写
                                        默认为 True
            grouping_rule:          <str/list of str>分组规则
                                        默认为 ("%Y", "%m_%d")，此时将按照年月日进行分组。
                                        比如时间戳为 2016-03-20 11:45:39 的文件将被保存到 <output_dir>/2016/03_20 目录下
                                        其他可选样式：
                                            - "%Y_%m"   精确到月
                                            - ("%Y", "%m_%d", "%H-%M-%S")   精确到秒
                                            依次类推
            timestamp_type:         使用哪个维度的时间戳
                                        有以下可选值：
                                            - "m"       文件的修改时间
                                            - "a"       文件的最近访问时间
                                            - "c"       文件的创建时间
                                        默认为 "m"。
            b_keep_source:          <boolean> 是否保留 input_dir 中的原始文件
    """
    if isinstance(grouping_rule, str):
        grouping_rule = [grouping_rule]
    assert timestamp_type in ['m', 'a', 'c']
    global get_timestamp_method_s
    os.makedirs(output_dir, exist_ok=True)

    get_timestamp = get_timestamp_method_s[timestamp_type]
    res_s = defaultdict(lambda: dict(src_ls=[], dst_ls=[], b_success_ls=[]))
    for file in find_files_in_dir(input_dir=input_dir, suffix_ls=suffix_ls, b_ignore_case=b_ignore_case,
                                  b_relative_path=True):
        src = os.path.join(input_dir, file)
        timestamp = get_timestamp(src)
        group_name = tuple(f'{time.strftime(i, timestamp)}' for i in grouping_rule)
        out_folder = os.path.join(output_dir, *group_name)
        dst = os.path.join(out_folder, os.path.basename(file))
        os.makedirs(out_folder, exist_ok=True)
        b_success = False
        try:
            copy(src=src, dst=dst)
            if b_verbose:
                print(f'{file} -> {out_folder}')
            b_success = True
        except:
            warnings.warn(f'failed to copy file {file} to {out_folder}')
        if not b_keep_source:
            remove(path=dst, ignore_errors=True)
        res_s[group_name]['b_success_ls'].append(b_success)
        res_s[group_name]['src_ls'].append(file)
        res_s[group_name]['dst_ls'].append(os.path.relpath(path=dst, start=output_dir))
    return res_s


if __name__ == "__main__":
    res = group_files_by_timestamp(suffix_ls=['.jpg', '.mp4', '.png', '.jpeg', '.mov', '.cr2', ".bmp"],
                                   grouping_rule=("%Y-%m", "%Y_%m_%d"),
                                   # "%Y-%m-%d %H:%M:%S" 2016-03-20 11:45:39 #"%a %b"  Sat Mar
                                   input_dir="/home/SENSETIME/xukaiming/Desktop/my_repos/python_projects/kevin_toolbox/kevin_toolbox/developing/photo_organization/test/test_data",
                                   output_dir="/home/SENSETIME/xukaiming/Desktop/my_repos/python_projects/kevin_toolbox/kevin_toolbox/developing/photo_organization/test/test_data1",
                                   timestamp_type="m")
    print(res)

    # timestamp_type = input("分类标准：m for modifytime \n c for createtime\n a for accesstime\n")
    # copy_path_root = os.path.join(output_dir, \
    #                               'deal' + str(time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime())))
    # group_by_timestamp(suffix_ls=['.MP4', '.jpg', '.mp4', '.png', '.JPG', '.MOV', '.CR2'],
    #                    grouping_rule="%Y_%m_%d",  # "%Y-%m-%d %H:%M:%S" 2016-03-20 11:45:39 #"%a %b"  Sat Mar
    #                    input_dir=input("please input the root path\n"),
    #                    output_dir=input("please input the target_path\n"), timestamp_type=timestamp_type)
