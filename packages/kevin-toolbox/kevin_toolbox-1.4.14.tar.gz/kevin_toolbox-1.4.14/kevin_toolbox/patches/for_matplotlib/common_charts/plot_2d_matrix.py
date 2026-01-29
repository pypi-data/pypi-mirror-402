import copy
import warnings
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from kevin_toolbox.patches.for_matplotlib.common_charts.utils import save_plot, save_record, get_output_path
from kevin_toolbox.patches.for_matplotlib.variable import COMMON_CHARTS
from kevin_toolbox.env_info.version import compare

__name = ":common_charts:plot_matrix"

if compare(v_0=sns.__version__, operator="<", v_1='0.13.0'):
    warnings.warn("seaborn version is too low, it may cause the heat map to not be drawn properly,"
                  " please upgrade to 0.13.0 or higher")


@COMMON_CHARTS.register(name=__name)
def plot_2d_matrix(matrix, title, row_label="row", column_label="column", x_tick_labels=None, y_tick_labels=None,
                   output_dir=None, output_path=None, replace_zero_division_with=0, **kwargs):
    """
        计算并绘制混淆矩阵

        参数：
            matrix:             <np.ndarray> 矩阵
            row_label:          <str> 行标签。
            column_label:       <str> 列标签。
            title:              <str> 绘图标题，同时用于保存图片的文件名。
            output_dir:         <str or None>
                图像保存的输出目录。如果同时指定了 output_path，则以 output_path 为准。
                若 output_dir 和 output_path 均未指定，则图像将直接通过 plt.show() 显示而不会保存到文件。

            output_dir:         <str> 图片输出目录。
            output_path:        <str> 图片输出路径。
                        以上两个只需指定一个即可，同时指定时以后者为准。
                        当只有 output_dir 被指定时，将会以 title 作为图片名。
                        若同时不指定，则直接以 np.ndarray 形式返回图片，不进行保存。
                        在保存为文件时，若文件名中存在路径不适宜的非法字符将会被进行替换。
            replace_zero_division_with:     <float> 在归一化混淆矩阵时，如果遇到除0错误的情况，将使用该值进行替代。
                                    建议使用 np.nan 或 0，默认值为 0。

        其他可选参数：
            dpi:                <int> 图像保存的分辨率。
            suffix:             <str> 图片保存后缀。
                                    目前支持的取值有 ".png", ".jpg", ".bmp"，默认为第一个。
            normalize:          <str or None> 指定归一化方式。
                                    可选值包括：
                                        "row"（按行归一化）
                                        "column"（按列归一化）
                                        "all"（整体归一化）
                                    默认为 None 表示不归一化。
            value_fmt:          <str> 矩阵元素数值的显示方式。
            b_return_matrix:    <bool> 是否在返回值中包含（当使用 normalize 操作时）修改后的矩阵。
                                    默认为 False。
            b_generate_record:  <boolean> 是否保存函数参数为档案。
                                    默认为 False，当设置为 True 时将会把函数参数保存成 [output_path].record.tar。
                                    后续可以使用 plot_from_record() 函数或者 Serializer_for_Registry_Execution 读取该档案，并进行修改和重新绘制。
                                    该参数仅在 output_dir 和 output_path 非 None 时起效。
            b_show_plot:        <boolean> 是否使用 plt.show() 展示图片。
                                    默认为 False
            b_bgr_image:        <boolean> 以 np.ndarray 形式返回图片时，图片的channel顺序是采用 bgr 还是 rgb。
                                    默认为 True
    """
    paras = {
        "dpi": 200,
        "suffix": ".png",
        "b_generate_record": False,
        "b_show_plot": False,
        "b_bgr_image": True,
        "normalize": None,  # "true", "pred", "all",
        "b_return_matrix": False,  # 是否输出混淆矩阵

    }
    paras.update(kwargs)
    matrix = np.asarray(matrix)
    paras.setdefault("value_fmt",
                     '.2%' if paras["normalize"] is not None or np.issubdtype(matrix.dtype, np.floating) else 'd')
    #
    _output_path = get_output_path(output_path=output_path, output_dir=output_dir, title=title, **kwargs)
    save_record(_func=plot_2d_matrix, _name=__name,
                _output_path=_output_path if paras["b_generate_record"] else None,
                **paras)
    matrix = copy.deepcopy(matrix)

    # replace with nan
    if paras["normalize"] is not None:
        if paras["normalize"] == "all":
            if matrix.sum() == 0:
                matrix[matrix == 0] = replace_zero_division_with
            matrix = matrix / matrix.sum()
        else:
            check_axis = 1 if paras["normalize"] == "row" else 0
            temp = np.sum(matrix, axis=check_axis, keepdims=False)
            for i in range(len(temp)):
                if temp[i] == 0:
                    if check_axis == 0:
                        matrix[:, i] = replace_zero_division_with
                    else:
                        matrix[i, :] = replace_zero_division_with
            matrix = matrix / np.sum(matrix, axis=check_axis, keepdims=True)

    # 绘制混淆矩阵热力图
    plt.clf()
    plt.figure(figsize=(8, 6))
    sns.heatmap(matrix, annot=True, fmt=paras["value_fmt"],
                xticklabels=x_tick_labels if x_tick_labels is not None else "auto",
                yticklabels=y_tick_labels if y_tick_labels is not None else "auto",
                cmap='viridis')

    plt.xlabel(f'{column_label}')
    plt.ylabel(f'{row_label}')
    plt.title(f'{title}')

    save_plot(plt=plt, output_path=_output_path, dpi=paras["dpi"], suffix=paras["suffix"])

    if paras["b_return_matrix"]:
        return _output_path, matrix
    else:
        return _output_path


if __name__ == '__main__':
    import os

    # 示例真实标签和预测标签
    A = np.random.randint(0, 5, (5, 5))
    print(A)

    plot_2d_matrix(
        matrix=np.random.randint(0, 5, (5, 5)),
        title="2D Matrix",
        output_dir=os.path.join(os.path.dirname(__file__), "temp"),
        replace_zero_division_with=-1,
        # normalize="row"
    )
