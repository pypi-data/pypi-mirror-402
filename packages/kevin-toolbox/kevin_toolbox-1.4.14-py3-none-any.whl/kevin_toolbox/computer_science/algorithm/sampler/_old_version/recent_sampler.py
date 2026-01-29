class Recent_Sampler:
    """
        最近采样器：始终保留最近加入的 capacity 个样本
    """

    def __init__(self, **kwargs):
        """
            参数：
                capacity:                       <int> 缓冲区或窗口的容量
        """
        # 默认参数
        paras = {
            "capacity": 1,
        }

        # 获取并更新参数
        paras.update(kwargs)

        # 校验 capacity
        assert paras["capacity"] >= 1

        self.paras = paras
        self.cache = []  # 用列表来保存最近的样本
        self.state = self._init_state()  # state 只记录 total_nums

    @staticmethod
    def _init_state():
        """
            初始化状态，仅记录已添加的总样本数
        """
        return dict(
            total_nums=0,
        )

    def add(self, item, **kwargs):
        """
            添加单个数据 item 到采样器中。
            - 更新 total_nums 计数
            - 将 item 追加到 cache 末尾
            - 如果超出 capacity，则删除最旧的一个（即列表开头的元素）
        """
        self.state["total_nums"] += 1
        self.cache.append(item)
        if len(self.cache) > self.paras["capacity"]:
            self.cache.pop(0)

    def add_sequence(self, item_ls, **kwargs):
        """
            批量添加：对列表中每个元素多次调用 add
        """
        for item in item_ls:
            self.add(item, **kwargs)

    def get(self, **kwargs):
        """
            返回当前缓冲区中的数据列表（浅拷贝）。
        """
        return self.cache.copy()

    def clear(self):
        """
            清空已有数据和状态，重置采样器。
        """
        self.cache.clear()
        self.state = self._init_state()

    def __len__(self):
        """
            返回已添加的总样本数（state["total_nums"]），
            而不是当前缓冲区长度
        """
        return self.state["total_nums"]

    # ---------------------- 用于保存和加载状态 ---------------------- #

    def load_state_dict(self, state_dict):
        """
            加载状态
            - 清空当前缓冲区和 state
            - 恢复 state["total_nums"]
            - 恢复 cache 列表内容
            - 恢复 rng 状态
        """
        self.clear()
        self.state.update(state_dict["state"])
        self.cache.extend(state_dict["cache"])

    def state_dict(self, b_deepcopy=True):
        """
            获取当前状态，包含：
            - state: {"total_nums": ...}
            - cache: 当前缓冲区列表
        """
        temp = {
            "state": self.state,
            "cache": self.cache
        }
        if b_deepcopy:
            import kevin_toolbox.nested_dict_list as ndl
            temp = ndl.copy_(var=temp, b_deepcopy=True, b_keep_internal_references=True)
        return temp


# 测试示例
if __name__ == "__main__":
    # 创建一个容量为 5 的 Recent_Sampler
    sampler = Recent_Sampler(capacity=5)

    # 逐个添加 1 到 10 的数字
    for i in range(1, 11):
        sampler.add(i)
        print(f"添加 {i} 后缓冲区: {sampler.get()}")

    # 到这里，缓冲区中应该只保留最近加入的 5 个样本：6,7,8,9,10
    print("最终缓冲区:", sampler.get())  # 预期输出: [6,7,8,9,10]
    print("总共添加个数:", len(sampler))  # 预期输出: 10

    # 保存当前状态
    state = sampler.state_dict()
    print("状态字典:", state)

    # 清空后再恢复状态
    sampler.clear()
    print("清空后缓冲区:", sampler.get())  # 预期输出: []

    sampler.load_state_dict(state)
    print("恢复后缓冲区:", sampler.get())  # 预期输出: [6,7,8,9,10]
    print("恢复后总共添加个数:", len(sampler))  # 预期输出: 10
