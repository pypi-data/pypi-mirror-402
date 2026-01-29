import numpy as np
import matplotlib.pyplot as plt
from kevin_toolbox.patches.for_matplotlib.color import generate_color_list
from kevin_toolbox.patches.for_matplotlib.common_charts.utils import save_plot, save_record, get_output_path
from kevin_toolbox.patches.for_matplotlib.variable import COMMON_CHARTS
from kevin_toolbox.patches.for_matplotlib.common_charts.plot_lines import log_scaling_for_x_y

__name = ":common_charts:plot_mean_std_lines"


@COMMON_CHARTS.register(name=__name)
def plot_mean_std_lines(data_s, title, x_name, mean_name_ls, std_name_ls, output_dir=None, output_path=None, **kwargs):
    """
        绘制均值和标准差折线图及其区域填充

        参数：
            data_s:             <dict> 数据。
                                    格式为：{
                                        x_name: [...],
                                        "name1_mean": [...], "name1_std": [...],
                                        "name2_mean": [...], "name2_std": [...],
                                        ...
                                    }
            title:              <str> 绘图标题，同时用于保存图片的文件名。
            x_name:             <str> 以哪个 data_name 作为 x 轴。
            mean_name_ls:       <list of str> 哪些名字对应的数据作为均值。
            std_name_ls:        <list of str> 哪些名字对应的数据作为标准差。
                        上面两参数要求大小相同，其同一位置表示该均值和标准差作为同一分组进行展示。
            output_dir:         <str> 图片输出目录。
            output_path:        <str> 图片输出路径。
                        以上两个只需指定一个即可，同时指定时以后者为准。
                        当只有 output_dir 被指定时，将会以 title 作为图片名。
                        若同时不指定，则直接以 np.ndarray 形式返回图片，不进行保存。
                        在保存为文件时，若文件名中存在路径不适宜的非法字符将会被进行替换。

        可选参数：
            dpi, suffix, b_generate_record, b_show_plot, b_bgr_image, color_ls, marker_ls, linestyle_ls 等（参考 plot_lines 的说明）
    """
    assert x_name in data_s
    y_names = set(mean_name_ls).union(set(std_name_ls))
    assert y_names.issubset(data_s.keys())
    assert len(mean_name_ls) == len(std_name_ls)
    line_nums = len(mean_name_ls)
    y_names = list(y_names)

    paras = {
        "dpi": 200,
        "suffix": ".png",
        "b_generate_record": False,
        "b_show_plot": False,
        "b_bgr_image": True,
        "color_ls": generate_color_list(nums=line_nums),
        "marker_ls": None,
        "linestyle_ls": '-',
        #
        "x_label": f'{x_name}',
        "y_label": "value",
        "x_log_scale": None,
        "x_ticks": None,
        "x_tick_labels": None,
        "x_label_formatter": None,
        "y_log_scale": None,
        "y_ticks": None,
        "y_tick_labels": None,
        "y_label_formatter": None,
    }
    paras.update(kwargs)
    for k, v in paras.items():
        if k.endswith("_ls") and not isinstance(v, (list, tuple)):
            paras[k] = [v] * line_nums
    assert line_nums == len(paras["color_ls"]) == len(paras["marker_ls"]) == len(paras["linestyle_ls"])

    _output_path = get_output_path(output_path=output_path, output_dir=output_dir, title=title, **kwargs)
    save_record(_func=plot_mean_std_lines, _name=__name,
                _output_path=_output_path if paras["b_generate_record"] else None,
                **paras)
    data_s = data_s.copy()
    #
    data_s, ticks_s, tick_labels_s = log_scaling_for_x_y(data_s=data_s, x_name=x_name, y_names=y_names, **paras)

    plt.clf()
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111)

    #
    x_all_ls = data_s.pop(x_name)
    for i, (mean_name, std_name) in enumerate(zip(mean_name_ls, std_name_ls)):
        mean_ls, std_ls, x_ls = [], [], []
        for mean, std, x in zip(data_s[mean_name], data_s[std_name], x_all_ls):
            if mean is None or std is None or x is None:
                continue
            mean_ls.append(mean)
            std_ls.append(std)
            x_ls.append(x)
        if len(x_ls) == 0:
            continue
        mean_ls = np.array(mean_ls)
        std_ls = np.array(std_ls)
        ax.plot(x_ls, mean_ls, label=f'{mean_name}', color=paras["color_ls"][i], marker=paras["marker_ls"][i],
                linestyle=paras["linestyle_ls"][i])
        ax.fill_between(x_ls, mean_ls - std_ls, mean_ls + std_ls, color=paras["color_ls"][i], alpha=0.2)

    ax.set_xlabel(paras["x_label"])
    ax.set_ylabel(paras["y_label"])
    ax.set_title(f'{title}')
    ax.grid(True)
    for i in ("x", "y",):
        if ticks_s[i] is not None:
            getattr(ax, f'set_{i}ticks')(ticks_s[i])
            getattr(ax, f'set_{i}ticklabels')(tick_labels_s[i])
    # 显示图例
    plt.legend()
    plt.tight_layout()

    return save_plot(plt=plt, output_path=_output_path, dpi=paras["dpi"], suffix=paras["suffix"],
                     b_bgr_image=paras["b_bgr_image"], b_show_plot=paras["b_show_plot"])


if __name__ == '__main__':
    import os

    plot_mean_std_lines(data_s={
        'a': [0.1, 0.5, 1.0, 2.0, 5.0],
        'model1': [0.3, 0.45, 0.5, 0.55, 0.6],
        'model1_std': [0.05, 0.07, 0.08, 0.06, 0.04],
        'model2': [0.25, 0.4, 0.48, 0.52, 0.58],
        'model2_std': [0.04, 0.06, 0.07, 0.05, 0.03]
    },
        x_name='a',
        mean_name_ls=['model1', 'model2'],
        std_name_ls=['model1_std', 'model2_std'],
        title='test_plot_mean_std_lines',
        output_dir=os.path.join(os.path.dirname(__file__), "temp"),
        b_generate_record=True, b_show_plot=True
    )
