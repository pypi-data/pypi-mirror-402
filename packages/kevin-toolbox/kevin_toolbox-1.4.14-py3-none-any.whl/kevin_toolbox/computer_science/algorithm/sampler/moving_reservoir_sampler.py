from kevin_toolbox.computer_science.algorithm.sampler import analog_resample, Reservoir_Sampler


class Moving_Reservoir_Sampler:
    def __init__(self, **kwargs):
        """
            滑动水库采样
                将对最近历史窗口内数据进行均匀采样

            参数：
                target_nums:            <int> 采样数量。
                b_allow_duplicates:       <boolean> 是否允许重复采样。
                                            默认为 False
                kernel_size:            <int> 滑动窗口的大小。
                                            需要大于 target_nums。
                seed, rng:              设定随机发生器
        """
        # 默认参数
        paras = {
            "kernel_size": 2,
            "target_nums": 1,
            "b_allow_duplicates": False,
            #
            "seed": None,
            "rng": None,
        }

        # 获取参数
        paras.update(kwargs)

        # 校验参数
        assert isinstance(paras["target_nums"], (int,)) and paras["target_nums"] >= 0
        assert isinstance(paras["kernel_size"], (int,)) and paras["kernel_size"] >= paras["target_nums"]

        self.paras = paras

        self.rs_old = Reservoir_Sampler(target_nums=self.paras["target_nums"], b_keep_order=False, seed=paras["seed"],
                                        rng=paras["rng"])
        self.rs = Reservoir_Sampler(target_nums=self.paras["target_nums"], b_keep_order=False, seed=paras["seed"],
                                    rng=paras["rng"])

    def add(self, item, **kwargs):
        if len(self.rs) >= self.paras["kernel_size"]:
            self.rs_old, self.rs = self.rs, self.rs_old
            self.rs.clear()
            self.rs_old.samples.sort(key=lambda x: x[-1])  # 对历史按照 stamp 进行排序
        self.rs.add(item=(item, len(self.rs)), **kwargs)

    def add_sequence(self, item_ls, **kwargs):
        for item in item_ls:
            self.add(item, **kwargs)

    def get(self, **kwargs):
        samples_old = [item for item, stamp in self.rs_old.get(**kwargs) if stamp >= len(self.rs)]
        samples_cur = [item for item, _ in self.rs.get(**kwargs)[:self.paras["target_nums"] - len(samples_old)]]
        res = samples_old + samples_cur
        if self.paras["b_allow_duplicates"]:
            res = analog_resample(samples=res, rng=self.rs.rng,
                                  total_nums=min(len(self.rs) + len(self.rs_old), self.paras["kernel_size"]))
        return res

    def clear(self):
        self.rs.clear()
        self.rs_old.clear()

    def __len__(self):
        return len(self.rs) + len(self.rs_old)

    # ---------------------- 用于保存和加载状态 ---------------------- #

    def load_state_dict(self, state_dict):
        """
            加载状态
        """
        self.clear()
        self.rs.load_state_dict(state_dict["rs"])
        self.rs_old.load_state_dict(state_dict["rs_old"])

    def state_dict(self, b_deepcopy=True):
        """
            获取状态
        """
        temp = {"rs": self.rs.state_dict(b_deepcopy=b_deepcopy),
                "rs_old": self.rs_old.state_dict(b_deepcopy=b_deepcopy)}
        return temp
