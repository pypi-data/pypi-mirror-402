import numpy as np
import torch
from kevin_toolbox.data_flow.core.reader import Unified_Reader_Base, UReader

normalize = lambda x: x / np.sum(x ** 2, axis=1, keepdims=True) ** 0.5  # 归一化


class Dummy_Data_Factory:
    """
        用于生成人脸识别的伪数据

        背景介绍：
            在人脸识别任务中，我们假设每个人 human 都有一个表征 feature。
            而各个人在不同角度、环境、姿态下得到的人脸表征 feature 称为探针 probe。
            因此人脸识别实际上可以看做 probe feature 与 human feature 的匹配问题。

            有时候我们并不知道所有 human 的 feature，而只知道一部分。
            我们就将已知的 human feature 构成一个人脸库 gallery。
            判断 probe 是否在 gallery 中也可以看做一个二分类任务。

        实例化时输入的变量（特征库）：
            humans:                本征特征。
                                        shape [human_nums, dims_of_feature]
            gallery:               特征库中哪些是已知的。
                                        shape [human_nums, 1]
                                        已知的（亦即是库内人脸将被标记为1，反之为0）
        以上均可根据以下参数来随机生成：
            human_nums:             不同 human 的数量
            gallery_nums:           人脸库中 human 的数量
            dims_of_feature:        特征的维度

        构造数据集时输入的参数：
            probe_nums:             探针样本的数量
            noise_significance:     生成探针样本时，添加噪声的比例

        构造数据集时生成的变量（按照 probe_id 进行排序，一一对应）：
            probes（features）:     人脸样本。
                                        从 humans 中独立随机抽取 probe_nums 次，将抽得的特征再加以噪声糅合而成
                                        shape [probe_nums, dims_of_feature]
            clusters:               probe 所属的 human_id
                                        shape [probe_nums, 1]
            in_gallery:             probe 是否在 gallery 中
                                        shape [probe_nums, 1]

        用法：
            1. __init__() 在初始化时，输入相关变量
                factory = Dummy_Data_Factory( human_nums=xxx, gallery_nums=xxx )
            2. 通过 generate 函数来生成数据集
                dataset = factory.generate( nums=xxx, noise_significance=xxx,  need_to_generate=xxx)
                # 返回的数据集是一个字典
                # dataset := {"features": xxx, "clusters": xxx, "in_gallery": xxx}
                # 其中具体包含哪些字段，可以通过添加 need_to_generate 参数来指定
    """

    def __init__(self, *args, **kwargs):
        """
            构建人脸特征库
            参数:
                humans:             本征特征。
                                        shape [human_nums, dims_of_feature]
                                        需要被 Unified_Reader_Base 包裹
                                        不指定时，根据 human_nums 随机生成
                human_nums:         不同 human 的数量
                dims_of_feature:    特征的维度

                gallery:            human 是否在 gallery 中
                                        shape [human_nums, 1]
                                        不指定时，根据 gallery_nums 随机生成
                gallery_nums:       人脸库中 human 的数量
                                        默认等于 human_nums
        """

        # 默认参数
        paras = {
            # human
            "humans": None,
            "human_nums": None,
            "dims_of_feature": 256,
            # gallery
            "gallery": None,
            "gallery_nums": None,
        }

        # 获取参数
        paras.update(kwargs)

        # 计算设备（尽量使用gpu来加速计算）
        self.device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')

        # 校验参数
        # human [human_nums, dims_of_feature]
        if paras["humans"] is None:
            assert isinstance(paras["human_nums"], (int,))
            if isinstance(paras["dims_of_feature"], (int,)):
                paras["dims_of_feature"] = [paras["dims_of_feature"]]
            paras["dims_of_feature"] = list(paras["dims_of_feature"])
            # 构建人脸特征库
            paras["humans"] = UReader(var=normalize(
                np.random.uniform(0, 1, [paras["human_nums"]] + paras["dims_of_feature"]).astype(np.float32)))
        assert isinstance(paras["humans"], (Unified_Reader_Base,))

        # gallery [human_nums, 1]
        if paras["gallery"] is None:
            assert isinstance(paras["gallery_nums"], (int,))
            rand_index = np.random.choice(np.arange(paras["human_nums"]), size=paras["gallery_nums"], replace=False)
            gallery = np.zeros(shape=[paras["human_nums"], 1])
            gallery[tuple(rand_index),] = 1
            paras["gallery"] = UReader(var=gallery)
        assert isinstance(paras["gallery"], (Unified_Reader_Base,))

        self.paras = paras

    def generate(self, nums, **kwargs):
        """
            生成人脸数据集

            参数：
                nums:               样本的数量
                noise_significance:     生成探针样本时，添加噪声的比例
                need_to_generate:   指定数据集中需要生成的字段
                                        目前支持的字段有： {"features", "clusters", "in_gallery"}
        """

        __support_to_generate = {"features", "clusters", "in_gallery"}
        need_to_generate = kwargs.get("need_to_generate", __support_to_generate)
        assert isinstance(need_to_generate, (set,)) and need_to_generate.issubset(__support_to_generate)

        noise_significance = kwargs.get("noise_significance", 0.2)
        assert 0 <= noise_significance <= 1

        res = dict()

        # 计算 clusters
        clusters = np.random.randint(0, len(self.paras["humans"]), [nums, 1])

        if "clusters" in need_to_generate:
            res["clusters"] = clusters  # shape: [ nums, 1 ]

        # 计算 features
        if "features" in need_to_generate:
            true_features = self.paras["humans"].read(list(clusters.reshape(-1)))
            noise = np.random.uniform(0, 1, true_features.shape)
            features = noise_significance * noise + (1 - noise_significance) * true_features  # 为probe中的特征添加噪声，使其偏离真实值
            features = normalize(features)  # 归一化
            res["features"] = features  # shape: [ nums, dims_of_feature ]

        # 计算 in_gallery
        if "in_gallery" in need_to_generate:
            in_gallery = self.paras["gallery"].read(list(clusters.reshape(-1)))
            res["in_gallery"] = in_gallery  # shape: [ nums, 1 ]

        return res
