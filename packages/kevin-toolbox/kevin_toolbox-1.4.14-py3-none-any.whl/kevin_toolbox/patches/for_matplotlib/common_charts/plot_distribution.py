import math
import matplotlib.pyplot as plt
import numpy as np
from kevin_toolbox.patches.for_matplotlib.common_charts.utils import save_plot, save_record, get_output_path
from kevin_toolbox.patches.for_matplotlib.variable import COMMON_CHARTS

__name = ":common_charts:plot_distribution"


@COMMON_CHARTS.register(name=__name)
def plot_distribution(data_s, title, x_name=None, x_name_ls=None, type_="hist", output_dir=None, output_path=None,
                      **kwargs):
    """
        概率分布图
            支持以下几种绘图类型：
                  1. 数字数据，绘制概率分布图： type_ 参数为 "hist" 或 "histogram" 时。
                  2. 字符串数据，绘制概率直方图：type_ 参数为 "category" 或 "cate" 时。

        参数：
            data_s:             <dict> 数据。
                                    形如 {<data_name>: <data list>, ...} 的字典，
            title:              <str> 绘图标题，同时用于保存图片的文件名。
            x_name:             <str> 以哪个 data_name 作为待绘制数据。
            x_name_ls:          <list or tuple> 以多个 data_name 对应的多组数据在同一图中绘制多个概率分布图。
            type_:              <str> 指定绘图类型。
                                    支持的取值有：
                                        - "hist" 或 "histogram"：     需要 <data list> 为数值数据，将绘制概率分布图。
                                                                        需要进一步指定 steps 步长参数，
                                                                        或者 min、max、bin_nums 参数。
                                        - "category" 或 "cate"：      需要 <data list> 为字符串数据，将绘制概率直方图。
            output_dir:         <str> 图片输出目录。
            output_path:        <str> 图片输出路径。
                        以上两个只需指定一个即可，同时指定时以后者为准。
                        当只有 output_dir 被指定时，将会以 title 作为图片名。
                        若同时不指定，则直接以 np.ndarray 形式返回图片，不进行保存。
                        在保存为文件时，若文件名中存在路径不适宜的非法字符将会被进行替换。

        其他可选参数：
            dpi:                <int> 图像保存的分辨率。
            suffix:             <str> 图片保存后缀。
                                    目前支持的取值有 ".png", ".jpg", ".bmp"，默认为第一个。
            b_generate_record:  <boolean> 是否保存函数参数为档案。
                                    默认为 False，当设置为 True 时将会把函数参数保存成 [output_path].record.tar。
                                    后续可以使用 plot_from_record() 函数或者 Serializer_for_Registry_Execution 读取该档案，并进行修改和重新绘制。
                                    该参数仅在 output_dir 和 output_path 非 None 时起效。
            b_show_plot:        <boolean> 是否使用 plt.show() 展示图片。
                                    默认为 False
            b_bgr_image:        <boolean> 以 np.ndarray 形式返回图片时，图片的channel顺序是采用 bgr 还是 rgb。
                                    默认为 True

        返回值：
            <str> 图像保存的完整文件路径。如果 output_dir 或 output_path 被指定，
                 则图像会保存到对应位置并返回保存路径；否则可能直接显示图像，
                 返回值依赖于 save_plot 函数的具体实现。
    """
    paras = {
        "dpi": 200,
        "suffix": ".png",
        "b_generate_record": False,
        "b_show_plot": False,
        "b_bgr_image": True
    }
    paras.update(kwargs)
    #
    _output_path = get_output_path(output_path=output_path, output_dir=output_dir, title=title, **kwargs)
    save_record(_func=plot_distribution, _name=__name,
                _output_path=_output_path if paras["b_generate_record"] else None,
                **paras)
    data_s = data_s.copy()
    if x_name is not None:
        x_name_ls = [x_name, ]
    assert isinstance(x_name_ls, (list, tuple)) and len(x_name_ls) > 0

    plt.clf()

    alpha = max(1 / len(x_name_ls), 0.3)
    # 检查数据类型
    if type_ in ["histogram", "hist"]:
        # 数字数据，绘制概率分布图
        for x_name in x_name_ls:
            data = data_s[x_name]
            assert all(isinstance(x, (int, float)) for x in data), \
                f'输入数组中的元素类型不一致'
            if "steps" in paras:
                min_ = math.floor(min(data) / paras["steps"]) * paras["steps"]
                max_ = math.ceil(max(data) / paras["steps"]) * paras["steps"]
                bins = np.arange(min_, max_ + paras["steps"], paras["steps"])
            else:
                bins = np.linspace(paras.get("min", min(data)), paras.get("max", max(data)), paras["bin_nums"] + 1)
            plt.hist(data, density=True, bins=bins, alpha=alpha, label=x_name)
    elif type_ in ["category", "cate"]:
        # 字符串数据，绘制概率直方图
        for x_name in x_name_ls:
            data = data_s[x_name]
            unique_values, counts = np.unique(data, return_counts=True)
            probabilities = counts / len(data)
            plt.bar([f'{i}' for i in unique_values], probabilities, label=x_name, alpha=alpha)
    else:
        raise ValueError(f'unsupported plot type {type_}')

    plt.xlabel(f'value')
    plt.ylabel('prob')
    plt.title(f'{title}')
    # 显示图例
    plt.legend()

    return save_plot(plt=plt, output_path=_output_path, dpi=paras["dpi"], suffix=paras["suffix"],
                     b_bgr_image=paras["b_bgr_image"], b_show_plot=paras["b_show_plot"])


if __name__ == '__main__':
    import os
    import cv2

    image_ = plot_distribution(
        data_s={
            'a': [0.1, 2, 3, 4, 5, 3, 2, 1],
            'c': [1, 2, 3, 4, 5, 0, 0, 0]},
        title='test_plot_distribution', x_name_ls=['a', 'c'],
        # type_="category",
        # output_dir=os.path.join(os.path.dirname(__file__), "temp"),
        # b_show_plot=True
        type_="hist", steps=1,
    )
    cv2.imwrite(os.path.join(os.path.dirname(__file__), "temp", "233.png"), image_)
