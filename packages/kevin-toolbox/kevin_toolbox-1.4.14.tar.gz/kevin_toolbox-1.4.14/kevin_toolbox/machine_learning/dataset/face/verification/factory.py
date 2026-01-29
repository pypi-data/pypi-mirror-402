import numpy as np
import torch
from kevin_toolbox.patches.for_torch.compatible import tile as torch_tile
from kevin_toolbox.data_flow.core.reader import Unified_Reader_Base, UReader

SUPPORT_TO_GENERATE = {"scores", "labels", "samples"}


class Face_Verification_DataSet_Factory:
    """
        用于生成人脸识别 1:1 验证任务的数据集

        背景介绍：
            人脸识别任务中的 1:1 人脸验证，其实就可以看做一个二分类任务。
            我们将两个人脸图片之间的一次比较（注意这里的“比较”是名词，我们也可以将它看做由两个人脸图片组成的二元对），看做一个样本 sample。
            - 同一个人的比较，看做 positive sample
            - 不同人之间的比较，看做 negative sample

        人脸特征相关变量（按照 feature_id 进行排序，一一对应）：
            features:        list of feature
                                    人脸特征库
                                        shape [feature_nums, feature_dims]
            clusters:     list of feature' cluster id
                                    记录各个feature所属的cluster（亦即人）
                                        shape [feature_nums, 1]

        数据集相关变量（按照 sample_id 进行排序，一一对应）：
            samples:                list of feature_id pairs
                                    每个样本由一对 feature_id 构成，表示这两个feature之间的一次比较。
                                        shape [sample_nums, 2]
            scores:                 list of floats indicating similarities between feature pairs
                                    两个feature之间的相似度
                                        shape [sample_nums, 1]
            labels:                 list of labels describing whether it is a positive or negative sample
                                    描述是正样本还是负样本（亦即是不是同一个cluster/人）
                                        shape [sample_nums, 1]

        工作流程：
            根据 feature_id 来生成 samples
            根据 features 来生成 scores
            根据 clusters 来生成 labels

        用法：
            1. __init__() 在初始化时，输入人脸特征相关变量
                factory = Face_Verification_DataSet_Factory( features=xxx, clusters=xxx )
                    要求输入的 features 和 clusters 需要使用 Unified_Reader_Base 的实现来包裹
            2. 通过 generate_xxx 系列函数来生成数据集
                # 方式 1
                #   generate_by_block
                #   先根据以 feature_id 为行列的相互矩阵来构建 samples 样本对，
                #   在该矩阵中所有的 feature 两两结对，每个格点对应于一个 sample，
                #   然后可以通过指定矩阵中的一个子矩阵来决定要生成哪一部分的数据集。
                # 有两种指定方式：
                #   连续行列
                dataset = factory.generate_by_block(i_0, i_1, j_0, j_1)
                #   不连续行列
                dataset = factory.generate_by_block(i_ls, None, j_ls, None)
                #   也可以混合指定
                dataset = factory.generate_by_block(i_ls, None, j_0, j_1)

                # 方式 2
                #   generate_by_samples
                #   根据输入的 samples 来生成数据集
                dataset = factory.generate_by_samples(samples)

                # 返回的数据集是一个字典
                # dataset := {"scores": xxx, "labels": xxx, "samples": xxx}
                # 其中具体包含哪些字段，可以通过添加 need_to_generate 参数来指定
                # 目前支持的字段有： {"scores", "labels", "samples"}
                dataset = factory.generate_by_samples(samples, need_to_generate={"scores", "samples"})
    """

    def __init__(self, *args, **kwargs):
        """
            绑定人脸特征相关变量
            必要参数:
                features:               list of feature 人脸特征库
                                            shape [feature_nums, feature_dims]
            可选参数：
                feature_id:             list of feature' id
                                            shape [feature_nums, 1]
                                            不指定时，默认从0开始依次递增
                                            要求不能有重复
                clusters:               list of feature' cluster id 记录各个feature所属的cluster（亦即人）
                                            shape [feature_nums, 1]
                                            不指定时，默认将各个 feature 看作从属于各自独立的 cluster，亦即使用 feature_id 来填充
                注意：以上输入的数据都需要被 Unified_Reader_Base 包裹
                    而 Unified_Reader_Base 除了可以支持从内存变量中读取数据外，还支持从持久化的磁盘文件中读取数据
            其他参数：
                feature_ids_is_sequential:       boolean，feature_ids 是否以1为间距递增的
                                            默认 False
                                            具体作用参考 generate_by_samples() 中的介绍
        """

        # 默认参数
        paras = {
            # 人脸特征相关变量
            "features": None,
            "feature_ids": None,
            "clusters": None,
            # 补充
            "feature_ids_is_sequential": False,
        }

        # 获取参数
        paras.update(kwargs)

        # 校验参数
        # features [feature_nums, feature_dims]
        assert isinstance(paras["features"], (Unified_Reader_Base,))
        # feature_id [feature_nums, 1]
        if paras["feature_ids"] is not None:
            assert isinstance(paras["feature_ids"], (Unified_Reader_Base,))
        else:
            # 自动生成
            paras["feature_ids"] = UReader(var=np.arange(len(paras["features"])).reshape((-1, 1)))
            # 默认生成的 feature_ids 是连续的
            paras["feature_ids_is_sequential"] = True
        # clusters [feature_nums, 1]
        if paras["clusters"] is not None:
            assert isinstance(paras["clusters"], (Unified_Reader_Base,)) and len(
                paras["clusters"]) == len(paras["features"])
        else:
            # 自动生成
            paras["clusters"] = paras["feature_ids"]

        self.paras = paras

        # 计算设备（尽量使用gpu来加速计算）
        self.device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')

    @staticmethod
    def __check_paras_of_block(i_0, i_1, j_0, j_1, **kwargs):
        """
            检查 generate_by_block() 的输入参数
        """
        # (i_0, i_1, j_0, j_1)
        i_len = i_1 - i_0 if isinstance(i_0, (int,)) else len(i_0)
        j_len = j_1 - j_0 if isinstance(j_0, (int,)) else len(j_0)
        assert i_len > 0 and j_len > 0

        # pick_triangle
        pick_triangle = kwargs.get("pick_triangle", False)

        # include_diagonal
        include_diagonal = kwargs.get("include_diagonal", True)

        # need_to_generate
        need_to_generate = kwargs.get("need_to_generate", None)
        if need_to_generate is not None:
            assert isinstance(need_to_generate, (set,)) and need_to_generate.issubset(SUPPORT_TO_GENERATE), \
                ValueError(f"need_to_generate should be a subset of {SUPPORT_TO_GENERATE}")
        else:
            need_to_generate = SUPPORT_TO_GENERATE

        return i_len, j_len, pick_triangle, include_diagonal, need_to_generate

    def generate_by_block(self, i_0, i_1, j_0, j_1, **kwargs):
        """
            根据 feature_id 的相互矩阵来构建数据集
                先根据以 feature_id 为行列的相互矩阵来构建 samples 样本对，在该矩阵中所有的 feature 两两结对，
                每个格点对应于一个 sample，然后可以通过指定矩阵中的一个子矩阵来决定要生成哪一部分的数据集。

            范围参数：
                有两种指定方式：
                连续行列
                    generate_by_block(i_0, i_1, j_0, j_1)
                不连续行列
                    generate_by_block(i_ls, None, j_ls, None)
                也可以混合指定
                    generate_by_block(i_ls, None, j_0, j_1)

            其他参数：
                pick_triangle:      只取block的上三角
                include_diagonal:   当取上三角时，是否包含对角线
                                        默认为 True 包含
                                        仅当 pick_triangle=True 时该参数起效
                need_to_generate:   指定数据集中需要生成的字段
                                        目前支持的字段有： {"scores", "labels", "samples"}
                                        
            补充：
                当参数中额外指定有 scores, labels 或者 samples 时，将以参数中指定的值为准，不对该项进行计算
        """
        i_len, j_len, pick_triangle, include_diagonal, need_to_generate = self.__check_paras_of_block(i_0, i_1,
                                                                                                      j_0, j_1,
                                                                                                      **kwargs)
        res = dict()
        for key in need_to_generate:
            if key in kwargs:
                # 以参数指定的为准
                # 不需要进行计算
                res[key] = kwargs[key]
                continue

            # 计算 scores
            if key == "scores":
                # feature_outer [i_len, feature_dims]  and  [j_len, feature_dims]
                feature_outer_i = torch.tensor(self.paras["features"].read(i_0, i_1), device=self.device,
                                               dtype=torch.float32)
                feature_outer_j = torch.tensor(self.paras["features"].read(j_0, j_1), device=self.device,
                                               dtype=torch.float32)
                # scores [i_len, j_len, 1]
                res["scores"] = feature_outer_i.matmul(feature_outer_j.t()).unsqueeze(-1)
            # 计算 labels
            elif key == "labels":
                # cluster_outer [i_len, 1]  and  [j_len, 1]
                cluster_outer_i = torch.tensor(self.paras["clusters"].read(i_0, i_1), device=self.device,
                                               dtype=torch.float32)
                cluster_outer_j = torch.tensor(self.paras["clusters"].read(j_0, j_1), device=self.device,
                                               dtype=torch.float32)
                # labels [i_len, j_len, 1]
                res["labels"] = (cluster_outer_i.reshape(-1, 1) == cluster_outer_j.reshape(1, -1)).unsqueeze(-1)
            # 计算 samples
            elif key == "samples":
                # fid_outer [i_len, 1]  and  [j_len, 1]
                fid_outer_i = torch.tensor(self.paras["feature_ids"].read(i_0, i_1), device=self.device,
                                           dtype=torch.float32)
                fid_outer_j = torch.tensor(self.paras["feature_ids"].read(j_0, j_1), device=self.device,
                                           dtype=torch.float32)
                # samples [i_len, j_len, 2]
                res["samples"] = torch.stack(
                    (torch_tile(fid_outer_i, (1, j_len)), torch_tile(fid_outer_j.t(), (i_len, 1))), dim=2)

        # reshape 并转换为 np.array
        for key in need_to_generate:
            if pick_triangle:
                # 取上三角部分
                offset = 0 if include_diagonal else 1  # 是否包含对角线
                indices = tuple(torch.triu_indices(row=i_len, col=j_len, offset=offset))
                res[key] = res[key][indices].cpu().numpy()
            else:
                shape = [i_len * j_len] + list(res[key].shape[2:])
                res[key] = res[key].reshape(shape).cpu().numpy()

        return res

    def cal_size_of_block(self, i_0, i_1, j_0, j_1, **kwargs):
        """
            计算 generate_by_block() 将会产生的数据集的大小
            参数：
                与 generate_by_block() 完全相同
        """
        i_len, j_len, pick_triangle, include_diagonal, _ = self.__check_paras_of_block(i_0, i_1, j_0, j_1, **kwargs)
        if pick_triangle:
            offset = 0 if include_diagonal else 1
            size = (j_len - offset) * (j_len + 1 - offset)
            if i_len < j_len:
                size -= (j_len - i_len - offset) * (j_len - i_len + 1 - offset)
            size /= 2
        else:
            size = i_len * j_len
        return int(size)

    def __check_paras_of_samples(self, samples, **kwargs):
        """
            检查 generate_by_samples() 的输入参数
        """
        # samples
        assert samples.ndim == 2 and samples.shape[1] == 2, \
            Exception(f"Error: shape {samples.shape} of samples does not satisfy [sample_nums, 2]!")

        # need_to_generate
        need_to_generate = kwargs.get("need_to_generate", None)
        if need_to_generate is not None:
            assert isinstance(need_to_generate, (set,)) and need_to_generate.issubset(SUPPORT_TO_GENERATE), \
                ValueError(f"need_to_generate should be a subset of {SUPPORT_TO_GENERATE}")
        else:
            need_to_generate = SUPPORT_TO_GENERATE

        # feature_ids_is_sequential
        feature_id_is_sequential = kwargs.get("feature_id_is_sequential", self.paras["feature_ids_is_sequential"])
        return samples, need_to_generate, feature_id_is_sequential

    def generate_by_samples(self, samples, **kwargs):
        """
            根据输入的 samples 来生成数据集
                通过 samples 中的 feature_id 到 feature_ids 中找到对应的index，然后根据该index到 features 和 clusters 中取对应的值。

            范围参数：
                samples:            list of feature_id pairs
                                        np.array with dtype=np.int
                                        shape [sample_nums, 2]
            其他参数：
                need_to_generate:   参见 generate_by_block() 中的介绍。
                feature_ids_is_sequential:       boolean，feature_ids 是否以1为间距递增的
                                        默认 False
                                        当设定为 True 时，亦即 feature_ids 以1为间距递增的，
                                        那么我们在找到 features 中各个元素的 index 与它的 feature_id 之间的偏移关系后，
                                        对于任意的 feature_id，就可以直接根据找到的关系式 index = feature_id + offset，
                                        检索到对应的 feature = features[index]，提高检索效率。
                                        
            补充：
                当参数中额外指定有 scores, labels 或者 samples 时，将以参数中指定的值为准，不对该项进行计算
        """
        samples, need_to_generate, feature_id_is_sequential = self.__check_paras_of_samples(samples, **kwargs)

        # 获取 index
        if feature_id_is_sequential:
            offset = self.paras["feature_ids"].read(0)[0]
            samples_ = samples - offset
            index_ls_i, index_ls_j = list(samples_[:, 0]), list(samples_[:, 1])
        else:
            map_ = dict().fromkeys(samples.flat)  # { feature_id: index, ... }
            for key in map_.keys():
                map_[key] = self.paras["feature_ids"].find(key)
            #
            index_ls_i, index_ls_j = [], []
            for i, j in samples:
                index_ls_i.append(map_[i])
                index_ls_j.append(map_[j])

        res = dict()
        for key in need_to_generate:
            if key in kwargs:
                # 以参数指定的为准
                # 不需要进行计算
                res[key] = kwargs[key]
                continue

            # 计算 scores
            if key == "scores":
                # features [nums, feature_dims]
                features_i = torch.tensor(self.paras["features"].read(index_ls_i), device=self.device,
                                          dtype=torch.float32)
                features_j = torch.tensor(self.paras["features"].read(index_ls_j), device=self.device,
                                          dtype=torch.float32)
                # scores [nums, 1]
                scores = torch.sum(features_i * features_j, dim=1, keepdim=True)
                res["scores"] = scores.cpu().numpy()
            # 计算 labels
            elif key == "labels":
                # clusters [nums, 1]
                clusters_i = torch.tensor(self.paras["clusters"].read(index_ls_i), device=self.device,
                                          dtype=torch.float32)
                clusters_j = torch.tensor(self.paras["clusters"].read(index_ls_j), device=self.device,
                                          dtype=torch.float32)
                # labels [nums, 1]
                labels = clusters_i == clusters_j
                res["labels"] = labels.cpu().numpy()
            # 计算 samples
            elif key == "samples":
                # samples [nums, 2]
                res["samples"] = samples

        return res
