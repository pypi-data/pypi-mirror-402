import numpy as np
import matplotlib.pyplot as plt
from kevin_toolbox.patches.for_matplotlib.common_charts.utils import save_plot, save_record, get_output_path, \
    log_scaling
from kevin_toolbox.patches.for_matplotlib.variable import COMMON_CHARTS

__name = ":common_charts:plot_contour"


@COMMON_CHARTS.register(name=__name)
def plot_contour(data_s, title, x_name, y_name, z_name, type_=("contour", "contourf"),
                 output_dir=None, output_path=None, **kwargs):
    """
        绘制等高线图
            
        
        参数：
            data_s:             <dict> 数据。
                                    形如 {<data_name>: <data list>, ...} 的字典
                                    需要包含 x、y、z 三个键值对，分别对应 x、y、z 轴的数据，值可以是 2D 的矩阵或者"" 1D 数据。 数组。
            title:              <str> 绘图标题。
            x_name:             <str> x 轴的数据键名。
            y_name:             <str> y 轴的数据键名。
            z_name:             <str> z 轴的数据键名。
            type_:              <str/list of str> 图表类型。
                                    目前支持以下取值，或者以下取值的列表：
                                        - "contour"         等高线
                                        - "contourf"        带颜色填充的等高线
                                    当指定列表时，将会绘制多个图表的混合。
            output_dir:         <str> 图片输出目录。
            output_path:        <str> 图片输出路径。
                        以上两个只需指定一个即可，同时指定时以后者为准。
                        当只有 output_dir 被指定时，将会以 title 作为图片名。
                        若同时不指定，则直接以 np.ndarray 形式返回图片，不进行保存。
                        在保存为文件时，若文件名中存在路径不适宜的非法字符将会被进行替换。

        其他可选参数：
            dpi:                <int> 保存图像的分辨率。
                                    默认为 200。
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
            contourf_cmap:      <str> 带颜色填充的等高线的颜色映射，默认 "viridis"。
            contourf_alpha:     <float> 颜色填充的透明度。
            linestyles:         <str> 等高线线形。
                                    可选值：
                                        - 'solid'   实线
                                        - 'dashed'  虚线（默认）
                                        - 'dashdot' 点划线
                                        - 'dotted'  点线
            b_clabel:           <boolean> 是否在等高线上显示数值。
            x_log_scale,y_log_scale,z_log_scale:    <int/float> 对 x,y,z 轴数据使用哪个底数进行对数显示。
                                    默认为 None，此时表示不使用对数显示。
            x_ticks,...:        <int/list of float or int> 在哪个数字下添加坐标记号。
                                    默认为 None，表示不添加记号。
                                    当设置为 int 时，表示自动根据 x,y,z 数据的范围，选取等间隔选取多少个坐标作为记号。
                                    特别地，可以通过 z_ticks 来指定等高线的数量和划分位置。
            x_tick_labels,...:  <int/list> 坐标记号的label。
    """
    # 默认参数设置
    paras = {
        "dpi": 200,
        "suffix": ".png",
        "b_generate_record": False,
        "b_show_plot": False,
        "b_bgr_image": True,
        "contourf_cmap": "viridis",
        "contourf_alpha": 0.5,
        "linestyles": "dashed",
        "b_clabel": True,
        "x_log_scale": None, "x_ticks": None, "x_tick_labels": None,
        "y_log_scale": None, "y_ticks": None, "y_tick_labels": None,
        "z_log_scale": None, "z_ticks": None, "z_tick_labels": None,
    }
    paras.update(kwargs)
    #
    _output_path = get_output_path(output_path=output_path, output_dir=output_dir, title=title, **kwargs)
    save_record(_func=plot_contour, _name=__name,
                _output_path=_output_path if paras["b_generate_record"] else None,
                **paras)
    data_s = data_s.copy()
    if isinstance(type_, str):
        type_ = [type_]

    d_s = dict()
    ticks_s = dict()
    tick_labels_s = dict()
    for k in ("x", "y", "z"):
        d_s[k], ticks_s[k], tick_labels_s[k] = log_scaling(
            x_ls=data_s[eval(f'{k}_name')], log_scale=paras[f"{k}_log_scale"],
            ticks=paras[f"{k}_ticks"], tick_labels=paras[f"{k}_tick_labels"]
        )
    X, Y, Z = [d_s[i] for i in ("x", "y", "z")]

    plt.clf()
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111)

    # 等高线
    if "contour" in type_:
        if X.ndim == 1:
            contour = ax.tricontour(X, Y, Z, colors='black', linestyles=paras["linestyles"], levels=ticks_s["z"])
        elif X.ndim == 2:
            contour = ax.contour(X, Y, Z, colors='black', linestyles=paras["linestyles"], levels=ticks_s["z"])
        else:
            raise ValueError("The dimension of X, Y, Z must be 1 or 2.")
        if paras["b_clabel"]:
            ax.clabel(contour, inline=True, fontsize=10, fmt={k: v for k, v in zip(ticks_s["z"], tick_labels_s["z"])})

    # 等高线颜色填充
    if "contourf" in type_:
        if X.ndim == 1:
            contourf = ax.tricontourf(X, Y, Z, cmap=paras["contourf_cmap"], alpha=paras["contourf_alpha"],
                                      levels=ticks_s["z"])
        elif X.ndim == 2:
            contourf = ax.contourf(X, Y, Z, cmap=paras["contourf_cmap"], alpha=paras["contourf_alpha"],
                                   levels=ticks_s["z"])
        else:
            raise ValueError("The dimension of X, Y, Z must be 1 or 2.")
        # 添加颜色条以展示平滑曲面颜色与 z 值的对应关系
        cbar = fig.colorbar(contourf, ax=ax, shrink=0.5, aspect=10)
        cbar.set_label(z_name, fontsize=12)

    # 设置坐标轴标签和图形标题
    ax.set_xlabel(x_name, fontsize=12)
    ax.set_ylabel(y_name, fontsize=12)
    ax.set_title(title, fontsize=14)
    for i in ("x", "y",):
        if ticks_s[i] is not None:
            getattr(ax, f'set_{i}ticks')(ticks_s[i])
            getattr(ax, f'set_{i}ticklabels')(tick_labels_s[i])

    return save_plot(plt=plt, output_path=_output_path, dpi=paras["dpi"], suffix=paras["suffix"],
                     b_bgr_image=paras["b_bgr_image"], b_show_plot=paras["b_show_plot"])


if __name__ == '__main__':
    # 生成示例数据
    x = np.linspace(1, 7, 100)
    y = np.linspace(-3, 3, 100)
    X, Y = np.meshgrid(x, y)
    # 这里定义一个函数，使得 Z 值落在 0 到 1 之间
    Z = np.exp(-(X ** 2 + Y ** 2))
    data = {
        'x': X,
        'y': Y,
        "z": Z,
    }
    plot_contour(data, x_name='x', y_name='y', z_name='z', title="Contour Plot", x_log_scale=None, z_ticks=10,
                 type_=("contour", "contourf"), output_dir="./temp")
