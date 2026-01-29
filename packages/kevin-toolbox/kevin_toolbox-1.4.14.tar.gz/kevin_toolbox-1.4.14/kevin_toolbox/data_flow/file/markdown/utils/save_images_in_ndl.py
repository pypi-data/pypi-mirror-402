import os
import warnings
import torch
import cv2
import numpy as np
from PIL import Image
from collections import defaultdict
from kevin_toolbox.data_flow.file import markdown
from kevin_toolbox.patches.for_os.path import replace_illegal_chars, find_illegal_chars
import kevin_toolbox.nested_dict_list as ndl


def save_images_in_ndl(var, plot_dir, doc_dir=None, setting_s=None):
    """
        将ndl结构叶节点下的图片对象保存到 plot_dir 中，并替换为该图片的markdown链接

        参数：
            var:                <dict> 待处理的 ndl 结构
            plot_dir:           <path> 图片保存的目录
            doc_dir:            <path> 输出的markdown文档保存的目录
                                    当有指定时，图片链接将以相对于 doc_dir 的相对路径的形式保存
                                    默认为 None，此时保存的markdown图片链接使用的是绝对路径
            setting_s:          <dict> 配置
                                    指定要在哪些节点下去寻找图片对象，以及转换图片对象时使用的参数
                                    形式为 {<node name>: {"b_is_rgb":<boolean>, ...}, ...}
                                    其中配置项支持：
                                        - b_is_rgb:             待保存的图片是RGB顺序还是BGR顺序
                                        - saved_image_format:   保存图片时使用的格式
                                    默认为 None，此时等效于 {"": {"b_is_rgb": False, "saved_image_format": ".jpg"}}
    """
    if len(find_illegal_chars(file_name=plot_dir, b_is_path=True)) > 0:
        warnings.warn(f'plot_dir {plot_dir} contains illegal symbols, '
                      f'which may cause compatibility issues on certain systems.', UserWarning)
    setting_s = setting_s or {"": {"b_is_rgb": False, "saved_image_format": ".jpg"}}

    # 将配置解释到各个叶节点
    #   从最浅的路径开始，若更深的路径有另外的设置，则以更新的为准
    root_ls = list(setting_s.keys())
    root_ls.sort(key=lambda x: len(ndl.name_handler.parse_name(name=x)[-1]))
    root_to_leaf_s = defaultdict(set)
    leaf_to_root_s = dict()
    leaf_to_value_s = dict()
    for root in root_ls:
        for leaf, v in ndl.get_nodes(var=ndl.get_value(var=var, name=root, b_pop=False), level=-1, b_strict=True):
            leaf = root + leaf
            if leaf in leaf_to_root_s:
                root_to_leaf_s[leaf_to_root_s[leaf]].remove(leaf)
            root_to_leaf_s[root].add(leaf)
            leaf_to_root_s[leaf] = root
            leaf_to_value_s[leaf] = v

    for root, leaf_ls in root_to_leaf_s.items():
        setting_ = setting_s[root]
        for leaf in leaf_ls:
            v = leaf_to_value_s[leaf]
            if isinstance(v, Image.Image):
                v = np.asarray(v)
            elif torch.is_tensor(v):
                v = v.detach().cpu().numpy()
            #
            if isinstance(v, np.ndarray):
                image_path = os.path.join(
                    plot_dir, replace_illegal_chars(
                        file_name=f'{leaf}_{setting_["saved_image_format"]}', b_is_path=False)
                )
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                if setting_["b_is_rgb"]:
                    v = cv2.cvtColor(v, cv2.COLOR_RGB2BGR)
                cv2.imwrite(image_path, v)
                v_new = markdown.generate_link(
                    name=os.path.basename(image_path),
                    target=os.path.relpath(image_path, doc_dir) if doc_dir is not None else image_path, type_="image")
            elif v is None:
                v_new = "/"
            else:
                v_new = v
            ndl.set_value(var=var, name=leaf, b_force=False, value=v_new)
    return var



