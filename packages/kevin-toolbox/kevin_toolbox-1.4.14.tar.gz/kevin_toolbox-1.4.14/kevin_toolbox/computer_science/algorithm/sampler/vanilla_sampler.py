from kevin_toolbox.patches.for_numpy.random import get_rng, get_rng_state, set_rng_state


class Vanilla_Sampler:
    def __init__(self, **kwargs):
        """
            一般的序列采样采样

            参数：
                target_nums:            <int> 采样数量。
                b_allow_duplicates:     <boolean> 是否允许重复采样。
                                            默认为 False
                seed, rng:              设定随机发生器
        """

        # 默认参数
        paras = {
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

        self.paras = paras
        self.sequence = []
        self.rng = get_rng(seed=paras["seed"], rng=paras["rng"])

    def add(self, item):
        self.sequence.append(item)

    def add_sequence(self, item_ls):
        self.sequence.extend(item_ls)

    def get(self):
        if len(self.sequence) <= self.paras["target_nums"]:
            res = self.sequence
        else:
            res = self.rng.choice(self.sequence, self.paras["target_nums"], replace=self.paras["b_allow_duplicates"])
        return res

    def clear(self):
        self.sequence.clear()

    def __len__(self):
        return len(self.sequence)

    # ---------------------- 用于保存和加载状态 ---------------------- #

    def load_state_dict(self, state_dict):
        """
            加载状态
        """
        self.clear()
        self.sequence.extend(state_dict["sequence"])
        set_rng_state(state=state_dict["rng_state"], rng=self.rng)

    def state_dict(self, b_deepcopy=True):
        """
            获取状态
        """
        temp = {"sequence": self.sequence, "rng_state": get_rng_state(rng=self.rng)}
        if b_deepcopy:
            import kevin_toolbox.nested_dict_list as ndl
            temp = ndl.copy_(var=temp, b_deepcopy=True, b_keep_internal_references=True)
        return temp
