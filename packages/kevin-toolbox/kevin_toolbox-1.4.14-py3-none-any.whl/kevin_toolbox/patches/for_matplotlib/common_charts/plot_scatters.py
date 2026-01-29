import matplotlib.pyplot as plt
from kevin_toolbox.patches.for_matplotlib.color import generate_color_list
from kevin_toolbox.patches.for_matplotlib.common_charts.utils import save_plot, save_record, get_output_path
from kevin_toolbox.patches.for_matplotlib.variable import COMMON_CHARTS

__name = ":common_charts:plot_scatters"


@COMMON_CHARTS.register(name=__name)
def plot_scatters(data_s, title, x_name, y_name, cate_name=None, output_dir=None, output_path=None, **kwargs):
    """
        绘制散点图
            不同类别的数据点

        参数：
            data_s: <dict>
                数据字典，其中每个键对应一个数据列表。必须包含 x_name 和 y_name 对应的键，
                如果指定了 cate_name，还需要包含 cate_name 对应的键，用于按类别对散点图上数据点着色。
            title: <str>
                图形标题，同时用于生成保存图像时的文件名（标题中的非法字符会被替换）。
            x_name:             <str> 以哪个 data_name 作为数据点的 x 轴。
            y_name:             <str> 以哪个 data_name 作为数据点的 y 轴。
            cate_name:          <str> 以哪个 data_name 作为数据点的类别。
            output_dir:         <str or None> 图片输出目录。
            output_path:        <str or None> 图片输出路径。
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
            scatter_size:       <int> 散点的大小。
                                    默认 5。

        示例：
            >>> data = {
            ...     "age": [25, 30, 22, 40],
            ...     "income": [50000, 60000, 45000, 80000],
            ...     "gender": ["M", "F", "M", "F"]
            ... }
            >>> path = plot_scatters(data, "Age vs Income", "age", "income", cate_name="gender", output_dir="./plots")
    """
    paras = {
        "dpi": 200,
        "suffix": ".png",
        "b_generate_record": False,
        "b_show_plot": False,
        "b_bgr_image": True,
        "scatter_size": 5
    }
    paras.update(kwargs)
    #
    _output_path = get_output_path(output_path=output_path, output_dir=output_dir, title=title, **kwargs)
    save_record(_func=plot_scatters, _name=__name,
                _output_path=_output_path if paras["b_generate_record"] else None,
                **paras)

    plt.clf()
    #
    color_s = None
    if cate_name is not None:
        cates = list(set(data_s[cate_name]))
        color_s = {i: j for i, j in zip(cates, generate_color_list(nums=len(cates)))}
        c = [color_s[i] for i in data_s[cate_name]]
    else:
        c = "blue"
    # 创建散点图
    plt.scatter(data_s[x_name], data_s[y_name], s=paras["scatter_size"], c=c, alpha=0.8)
    #
    plt.xlabel(f'{x_name}')
    plt.ylabel(f'{y_name}')
    plt.title(f'{title}')
    # 添加图例
    if cate_name is not None:
        plt.legend(handles=[
            plt.Line2D([0], [0], marker='o', color='w', label=i, markerfacecolor=j,
                       markersize=min(paras["scatter_size"], 5)) for i, j in color_s.items()
        ])

    return save_plot(plt=plt, output_path=_output_path, dpi=paras["dpi"], suffix=paras["suffix"],
                     b_bgr_image=paras["b_bgr_image"], b_show_plot=paras["b_show_plot"])


if __name__ == '__main__':
    import os

    data_s_ = dict(
        x=[1, 2, 3, 4, 5],
        y=[2, 4, 6, 8, 10],
        categories=['A', 'B', 'A', 'B', 'A']
    )

    plot_scatters(
        data_s=data_s_, title='test_plot_scatters', x_name='x', y_name='y', cate_name='categories',
        output_dir=os.path.join(os.path.dirname(__file__), "temp")
    )
