import copy
from kevin_toolbox.computer_science.algorithm.registration import Registry
import kevin_toolbox.nested_dict_list as ndl


class Trigger:
    """
        触发器
            通过 self.update_by_state() 来接收并监视 state_dict，
            当 state_dict 全部或部分发生变化时，将会把【发生变化的部分】
            传入 self.bind() 绑定的函数中，并执行一次该函数。
    """

    def __init__(self, **kwargs):
        """
            参数：
                target_s:           <dict> 待绑定目标
                                        以名称 name 为键，以待绑定目标 target 为值
                                        主要调用 self.bind()
                init_state          <dict> 初始状态
                                        默认不设置，此时将在第一次调用 self.update_by_state() 时设置
        """
        # 默认参数
        paras = {
            #
            "target_s": dict(),
            "init_state": dict()
        }

        # 获取参数
        paras.update(kwargs)

        self.last_state = paras["init_state"]
        self.database = Registry(uid=None)
        for k, v in paras["target_s"].items():
            self.bind(name=k, target=v)

    def bind(self, name, target):
        """
            绑定触发目标
                触发目标有以下类型
                - 可以是实例（要求实例具有 update_by_state() 方法，将该方法作为真正的触发目标）
                - 函数

            参数：
                name:               <str> 名称，具体参见 for_nested_dict_list 中关于 name 的介绍
                target:             <obj/func> 待绑定目标
        """
        func = getattr(target, "update_by_state", None)
        target = target if func is None else func
        assert callable(target), \
            f'object {target} is not callable and has no update_by_state() method to be bound'
        assert isinstance(name, (str,))

        self.database.add(obj=target, name=name, b_force=True, b_execute_now=True)

    def unbind(self, name, b_not_exist_ok=True):
        """
            接触绑定

            参数：
                name:               <str> 待接触绑定目标的名称
                b_not_exist_ok:     <boolean> name 不存在时是否不报错
                                        默认为 True，不报错
        """

        try:
            self.database.get(name=name, b_pop=True)
        except:
            if not b_not_exist_ok:
                raise IndexError(f'name {name} not exists')

    def update_by_state(self, cur_state, target_names=None):
        """
            更新状态，决定是否触发

            参数：
                cur_state:          <dict> 状态
                target_names:       <list of str> 需要更新的目标
                                        默认为 None,此时将更新所有目标
        """
        assert isinstance(cur_state, (dict,))
        target_names = [""] if target_names is None else target_names
        assert isinstance(target_names, (list,))

        new_state = dict()
        for key, value in cur_state.items():
            if key not in self.last_state or self.last_state[key] != value:
                new_state[key] = value

        if len(new_state) > 0:
            # get funcs to update
            func_s = dict()
            for target_name in target_names:
                var = self.database.get(name=target_name, b_pop=False, default=None)
                if isinstance(var, (list, dict,)):
                    func_s.update({target_name + k: v for k, v in ndl.get_nodes(var=var, level=-1, b_strict=True)})
                else:
                    func_s[target_name] = var
            # update
            for func in func_s.values():
                if func is not None:
                    func(new_state)
            self.last_state.update(new_state)

        return new_state

    # ---------------------- 用于保存和加载触发器的状态 ---------------------- #

    def load_state_dict(self, state_dict):
        """
            加载触发器状态
        """
        self.last_state = state_dict["last_state"]

    def state_dict(self):
        """
            获取触发器状态
        """
        return {"last_state": copy.deepcopy(self.last_state)}

    def clear_state_dict(self):
        self.last_state.clear()
