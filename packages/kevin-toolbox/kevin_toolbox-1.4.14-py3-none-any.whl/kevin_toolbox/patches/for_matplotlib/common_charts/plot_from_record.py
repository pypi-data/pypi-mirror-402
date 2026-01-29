from kevin_toolbox.patches.for_matplotlib.variable import COMMON_CHARTS


def plot_from_record(input_path, **kwargs):
    """
        从 record 中恢复并绘制图像
            支持通过 **kwargs 对其中部分参数进行覆盖
    """
    from kevin_toolbox.computer_science.algorithm.registration import Serializer_for_Registry_Execution

    serializer = Serializer_for_Registry_Execution()
    serializer.load(input_path)
    serializer.record_s["kwargs"].update(kwargs)
    return serializer.recover()()


if __name__ == '__main__':
    import os

    plot_from_record(input_path=os.path.join(os.path.dirname(__file__), "temp/好-吧.png.record.tar"),
                     output_dir=os.path.join(os.path.dirname(__file__), "temp/recover"))
