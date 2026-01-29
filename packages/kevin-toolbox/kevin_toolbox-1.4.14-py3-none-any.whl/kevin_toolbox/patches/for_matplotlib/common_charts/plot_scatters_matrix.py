import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from kevin_toolbox.patches.for_matplotlib.color import generate_color_list
from kevin_toolbox.patches.for_matplotlib.common_charts.utils import save_plot, save_record, get_output_path
from kevin_toolbox.patches.for_matplotlib.variable import COMMON_CHARTS

__name = ":common_charts:plot_scatters_matrix"


@COMMON_CHARTS.register(name=__name)
def plot_scatters_matrix(data_s, title, x_name_ls, cate_name=None, output_dir=None, output_path=None, cate_color_s=None,
                         **kwargs):
    """
        绘制散点图矩阵
            该函数用于展示多个变量之间的两两关系。

        参数：
            data_s:             <dict> 数据。
                                    形如 {<data_name>: <data list>, ...} 的字典
            title:              <str> 绘图标题。
            x_name_ls:          <list of str> 指定用于需要绘制哪些变量的两两关系。
            cate_name:          <str or None> 使用哪个 data_name 对应的取值作为类别。
            output_dir:         <str or None> 图片输出目录。
            output_path:        <str or None> 图片输出路径。
                        以上两个只需指定一个即可，同时指定时以后者为准。
                        当只有 output_dir 被指定时，将会以 title 作为图片名。
                        若同时不指定，则直接以 np.ndarray 形式返回图片，不进行保存。
                        在保存为文件时，若文件名中存在路径不适宜的非法字符将会被进行替换。
            cate_color_s:       <dict or None> 类别-颜色映射字典，将 cate_name 中的每个类别映射到具体颜色。
                                    默认为 None，自动生成颜色列表。

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
            diag_kind:          <str> 对角线图表的类型。
                                    支持：
                                        - "hist"（直方图）
                                        - "kde"（核密度图）
                                    默认为 "kde"。
    """
    paras = {
        "dpi": 200,
        "suffix": ".png",
        "b_generate_record": False,
        "b_show_plot": False,
        "b_bgr_image": True,
        "diag_kind": "kde"  # 设置对角线图直方图/密度图 {‘hist’, ‘kde’}
    }
    assert cate_name in data_s and len(set(x_name_ls).difference(set(data_s.keys()))) == 0
    if cate_color_s is None:
        temp = set(data_s[cate_name])
        cate_color_s = {k: v for k, v in zip(temp, generate_color_list(len(temp)))}
    assert set(cate_color_s.keys()) == set(data_s[cate_name])
    paras.update(kwargs)
    #
    _output_path = get_output_path(output_path=output_path, output_dir=output_dir, title=title, **kwargs)
    save_record(_func=plot_scatters_matrix, _name=__name,
                _output_path=_output_path if paras["b_generate_record"] else None,
                **paras)

    plt.clf()
    # 使用seaborn绘制散点图矩阵
    sns.pairplot(
        pd.DataFrame(data_s),
        diag_kind=paras["diag_kind"],  # 设置对角线图直方图/密度图 {‘hist’, ‘kde’}
        hue=cate_name,  # hue 表示根据该列的值进行分类
        palette=cate_color_s, x_vars=x_name_ls, y_vars=x_name_ls,  # x_vars，y_vars 指定子图的排列顺序
    )
    #
    plt.subplots_adjust(top=0.95)
    plt.suptitle(f'{title}', y=0.98, x=0.47)

    return save_plot(plt=plt, output_path=_output_path, dpi=paras["dpi"], suffix=paras["suffix"],
                     b_bgr_image=paras["b_bgr_image"], b_show_plot=paras["b_show_plot"])


if __name__ == '__main__':
    import os

    data_s_ = dict(
        x=[1, 2, 3, 4, 5],
        y=[2, 4, 6, 8, 10],
        z=[2, 4, 6, 8, 10],
        categories=['A', 'B', 'A', 'B', 'A'],
        title='test',
    )

    plot_scatters_matrix(
        data_s=data_s_, title='test_plot_scatters_matrix', x_name_ls=['y', 'x', 'z'], cate_name='categories',
        cate_color_s={'A': 'red', 'B': 'blue'},
        output_dir=os.path.join(os.path.dirname(__file__), "temp")
    )
