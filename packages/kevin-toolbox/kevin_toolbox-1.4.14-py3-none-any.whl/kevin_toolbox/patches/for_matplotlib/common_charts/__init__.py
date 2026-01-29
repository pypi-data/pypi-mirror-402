# 在非 windows 系统下，尝试自动下载中文字体，并尝试自动设置字体
import sys

if not sys.platform.startswith("win"):
    import os
    from kevin_toolbox.env_info.variable_ import env_vars_parser

    font_setting_s = dict(
        b_auto_download=True,
        download_url="https://drive.usercontent.google.com/download?id=1wd-a4-AwAXkr7mHmB9BAIcGpAcqMrbqg&export=download&authuser=0",
        save_path="~/.kvt_data/fonts/SimHei.ttf"
    )
    font_setting_s.update()
    for k, v in list(font_setting_s.items()):
        font_setting_s[k] = env_vars_parser.parse(
            text=f"${{KVT_PATCHES:for_matplotlib:common_charts:font_settings:for_non-windows-platform:{k}}}",
            default=v
        )
    save_path = os.path.expanduser(font_setting_s["save_path"])

    if font_setting_s["b_auto_download"] and not os.path.isfile(save_path):
        from kevin_toolbox.network import download_file

        print(f'检测到当前系统非 Windows 系统，尝试自动下载中文字体...')
        download_file(
            output_dir=os.path.dirname(save_path),
            file_name=os.path.basename(save_path),
            url=font_setting_s["download_url"],
            b_display_progress=True
        )

    if os.path.isfile(save_path):
        import matplotlib.font_manager as fm
        import matplotlib.pyplot as plt

        # 注册字体
        fm.fontManager.addfont(save_path)
        # 获取字体名称
        font_name = fm.FontProperties(fname=save_path).get_name()

        # 全局设置默认字体
        plt.rcParams['font.family'] = font_name
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号 '-' 显示为方块的问题

from .plot_lines import plot_lines
from .plot_scatters import plot_scatters
from .plot_distribution import plot_distribution
from .plot_bars import plot_bars
from .plot_scatters_matrix import plot_scatters_matrix
from .plot_confusion_matrix import plot_confusion_matrix
from .plot_2d_matrix import plot_2d_matrix
from .plot_contour import plot_contour
from .plot_3d import plot_3d
from .plot_from_record import plot_from_record
# from .plot_raincloud import plot_raincloud
from .plot_mean_std_lines import plot_mean_std_lines
from .plot_heatmap import plot_heatmap
