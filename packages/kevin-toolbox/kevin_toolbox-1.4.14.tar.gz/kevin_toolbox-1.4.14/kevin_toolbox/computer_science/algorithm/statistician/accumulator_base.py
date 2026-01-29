from kevin_toolbox.computer_science.algorithm.statistician import init_var
import kevin_toolbox.nested_dict_list as ndl


class Accumulator_Base(object):
    """
        累积型统计器的抽象基类

        包含以下变量：
            self.var            <torch.tensor / np.ndarray / int / float> 用于保存累积值
                                    使用 statistician._init_var() 函数进行初始化。
                                    有三种初始化累积值（指定输入数据的格式）方式：
                                        1. （在初始化实例时）显式指定数据的形状和所在设备等。
                                            data_format:        <dict of paras>
                                                    其中需要包含以下参数：
                                                        type_:              <str>
                                                                                "numpy":        np.ndarray
                                                                                "torch":        torch.tensor
                                                        shape:              <list of integers>
                                                        device:             <torch.device>
                                                        dtype:              <torch.dtype>
                                        2. （在初始化实例时）根据输入的数据，来推断出形状、设备等。
                                            like:               <torch.tensor / np.ndarray / int / float>
                                        3. 不在初始化实例时指定 data_format 和 like，此时将等到第一次调用 add()/add_sequence()
                                            时再根据输入来自动推断。
                                            要实现该方式，需要在 add() 中添加:
                                                if self.var is None:
                                                    self.var = self._init_var(like=var)
                                        以上三种方式，默认选用最后一种。
                                        如果三种方式同时被指定，则优先级与对应方式在上面的排名相同。
            self.state          <dict> 用于保存状态的字典
                                    其中包含以下字段：
                                        "total_nums":     <int> 用于统计一共调用了多少次 self.add() 方法去进行累积
            self.paras          <dict> 用于保存构建实例时的各个参数

        包含以下接口：
            add()               (*)添加单个数据
            add_sequence()      (*)添加一系列数据
            get()               (*)获取累积值
            clear()             清空已有数据（self.var）和状态（self.state）
            state_dict()        返回当前实例的状态（返回一个包含 self.var 和 self.state 的字典）
            load_state_dict()   通过接受 state_dict 来更新当前实例的状态

        有可能需要另外实现or覆写的函数：
            上面带有 (*)的接口
            _init_state() 方法
            _init_var() 方法
    """

    def __init__(self, **kwargs):
        """
            至少包含以下参数：
                data_format:            指定数据格式（对应方式1）
                like:                   指定数据格式（对应方式2）
        """
        # 默认参数
        paras = {
            # 指定输入数据的形状、设备
            "data_format": None,
            "like": None,
        }

        # 获取参数
        paras.update(kwargs)

        # 校验参数
        #
        self.paras = paras
        self.var = self._init_var(like=paras["like"], data_format=paras["data_format"])
        self.state = self._init_state()

    def add_sequence(self, var_ls, **kwargs):
        # for var in var_ls:
        #     self.add(var, **kwargs)
        raise NotImplementedError

    def add(self, var, **kwargs):
        """
            添加单个数据

            参数:
                var:                数据
        """
        # if self.var is None:
        #     self.var = self._init_var(like=var)
        # # 累积
        # self.state["total_nums"] += 1
        # # 对 self.var 做处理（需要具体实现）
        raise NotImplementedError

    def get(self, **kwargs):
        """
            获取当前累加的平均值
                当未有累积时，返回 None
        """
        # if len(self) == 0:
        #     return None
        # # 对 self.var 做处理并返回（需要具体实现）
        raise NotImplementedError

    @staticmethod
    def _init_state():
        """
            初始化状态
        """
        return dict(
            total_nums=0,
        )

    @staticmethod
    def _init_var(like=None, data_format=None):
        if like is not None:
            var = init_var.by_like(var=like)
        elif data_format is not None:
            var = init_var.by_data_format(**data_format)
        else:
            var = None
        return var

    def clear(self):
        self.var = self._init_var(like=self.var)
        self.state = self._init_state()

    def __len__(self):
        return self.state["total_nums"]

    # ---------------------- 用于保存和加载状态 ---------------------- #

    def load_state_dict(self, state_dict):
        """
            加载状态
        """
        self.clear()
        self.state.update(state_dict.get("state", dict()))
        if state_dict.get("var", None) is not None:
            if self.var is None:
                self.var = state_dict["var"]
            else:
                self.var *= 0
                self.var += state_dict["var"]

    def state_dict(self):
        """
            获取状态
        """
        return ndl.copy_(var={"state": self.state, "var": self.var}, b_deepcopy=True, b_keep_internal_references=True)
