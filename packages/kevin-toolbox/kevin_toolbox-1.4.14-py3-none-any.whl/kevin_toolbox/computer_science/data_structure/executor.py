class Executor:
    """
        执行器
            允许以静态方式描述并保存一个执行过程，
            然后在你需要的地方再进行调用。

        用法：
            1.定义执行过程
                executor = Executor( func = <function>,
                                        args = <list/tuple>,
                                        kwargs = <dict>,
                                        f_args = <list of functions>,
                                        f_kwargs = <dict of (key, function) pairs>)
                # 其中 func 是执行过程的主体函数
                # args 和 kwargs 是运行该函数时，要输入的参数
                # f_args 和 f_kwargs 的前缀 f_ 是 fixtures 固件的缩写
                #     固件内包含一系列的函数
                #     这些函数会在 func 执行前被首先执行，然后将得到的结果更新到参数中
                #     对于 f_args，执行后的结果会被 append 到 args 后面
                #     对于 f_kwargs，其中的 value 被执行后的结果将替换原来的 value，然后 update 到 kwargs 中
                # 使用 fixtures 的一大优势，就是可以让一些参数可以等到函数需要执行前再生成，从而节约资源
            2.调用执行过程
                executor.run()
                # 等效于 executor()
            3.修改执行过程
                当初始化的定义完成后，你还可以通过以下方式来修改执行过程：
                executor.set_paras( args=xx, ... )
                或者在使用过程中动态修改函数的输入参数：
                executor.run( input, reverse=True, xxx )  # 这里的参数 input, reverse 仅用作举例
                # 等效于：
                #       executor.set_paras( args=[input, ], kwargs=dict(reverse=True), ... )
                #       executor()

        注意！！
            对于 fixtures 中的函数，在定义函数时，函数体中如果涉及有外部的变量，
            则务必注意这些外部变量可能被修改，从而引起函数的行为发生不可预期的变化，
            例如：
                >> k=2
                >> y=lambda x:x**int(k)
                >> y(2)
                # 4
                >> k=4
                >> y(2)
                # 16
            解决方法：
                使用 Executor 来构造 fixtures 中的函数，同时使用 deepcopy 对参数进行隔离。
    """

    def __init__(self, **kwargs):
        f'{self.set_paras.__doc__}'

        # 默认参数
        self.paras = {
            # 必要参数
            "func": None,
            #
            "args": list(),
            "f_args": list(),
            "kwargs": dict(),
            "f_kwargs": dict(),
        }
        self.set_paras(**kwargs)

    def set_paras(self, **kwargs):
        """
            定义执行过程

            参数：
                func:                   <callable function> 函数
                args:                   <list/tuple> 参数
                f_args:                 <list of functions> “待解释”参数
                                            这里面的函数会在 func 执行前被首先执行，然后将得到的结果更新到参数 args 中。
                kwargs:                 <dict> 位置参数
                f_kwargs:               <dict of (key, function) pairs> “待解释”位置参数。
                                            这里面的函数会在 func 执行前被首先执行，然后将得到的结果更新到位置参数 kwargs 中。
        """
        # 默认参数
        paras = self.paras.copy()

        # 获取参数
        paras.update(kwargs)

        # 校验参数
        # func
        assert paras["func"] is None or callable(paras["func"]), \
            f'func should be callable, but get a {type(paras["func"])}'
        # args
        assert isinstance(paras["args"], (list, tuple,)) and isinstance(paras["f_args"], (list, tuple,))
        for i, f in enumerate(paras["f_args"]):
            assert callable(f), \
                f"element {i} in f_args should be callable, but get a {type(f)}"
        # kwargs
        assert isinstance(paras["kwargs"], (dict,)) and isinstance(paras["f_kwargs"], (dict,))
        for k, v in paras["f_kwargs"].items():
            assert callable(v) and isinstance(k, (str,)), \
                f"item {k} in f_kwargs should be (str, callable) pairs, but get a ({type(k)}, {type(v)})"

        # update paras
        self.paras = paras

    def parse(self):
        assert callable(self.paras["func"]), \
            Exception(f"you should invoke set_paras() first, before calling parse()")

        # 获取函数
        func = self.paras["func"]

        # 获取参数
        args_, kwargs_ = [], dict()
        if "args" in self.paras:
            args_.extend(self.paras["args"])
        if "kwargs" in self.paras:
            kwargs_.update(self.paras["kwargs"])

        # evaluate the fixtures
        if "f_args" in self.paras:
            for f in self.paras["f_args"]:
                args_.append(f())
        if "f_kwargs" in self.paras:
            for k, v in self.paras["f_kwargs"].items():
                kwargs_[k] = v()

        return func, args_, kwargs_

    def run(self, *args, **kwargs):
        """
            调用执行过程
        """
        func, args_, kwargs_ = self.parse()
        assert callable(func), \
            Exception(f"you should invoke set_paras() first, before calling run()")

        # 根据当前输入动态更新参数
        if len(args) > 0:
            args_ = args
        kwargs_.update(kwargs)

        # 执行
        return func(*args_, **kwargs_)

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)


if __name__ == '__main__':
    #
    executor = Executor(func=lambda x, y: print(x + y), args=[1], kwargs={"y": 3})
    print("executor")
    executor()
    #
    executor = Executor(func=lambda x, y: print(x, y), f_args=[lambda: 3], f_kwargs={"y": lambda: 4})
    print("executor using fixtures")
    executor()
