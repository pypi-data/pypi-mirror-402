# 针对唯一标识符的单例模式
class Singleton_for_uid:
    """
        针对唯一标识符的单例模式
        对于一个给定的 uid 只会进行一次实例的生成，以后再对同一个 uid 调用 Singleton_for_uid() 进行实例生成，返回的只有以前生成的实例。
    """
    __instances = dict()  # {uid:<instance>, ...}
    __counter = 0
    class_name = ""

    def __new__(cls, *args, **kwargs):
        """
            __new__函数返回的实例，将作为self参数被传入到__init__函数。
                如果__new__函数返回一个已经存在的实例（不论是哪个类的），__init__还是会被调用的，所以要特别注意__init__中对变量的赋值。
        """
        uid = kwargs.get("uid", None)
        exist_ok = kwargs.get("exist_ok", True)
        assert isinstance(uid, (str, type(None),)), \
            TypeError(f"uid should be string or None, but get a {type(uid)}!")

        if uid in Singleton_for_uid.__instances:
            if exist_ok:
                # 返回已有实例，__init__不会被调用
                return Singleton_for_uid.__instances.get(uid)
            else:
                raise Exception(f"uid {uid} already exists!")
        else:
            # 传入 __init__
            return super().__new__(cls)

    def __init__(self, *args, **kwargs):
        try:
            getattr(self, "uid")
        except :
            pass
        else:
            return
        uid = kwargs.get("uid", None)
        assert isinstance(uid, (str, type(None),)), \
            TypeError(f"uid should be string or None, but get a {type(uid)}!")

        if uid is None:
            # 生成一个未被注册的 uid
            while True:
                uid = f"{Singleton_for_uid.class_name}_{Singleton_for_uid.__counter}"
                if uid not in Singleton_for_uid.__instances:
                    break
                Singleton_for_uid.__counter += 1
        self.uid = uid
        # 注册
        Singleton_for_uid.__instances[self.uid] = self

    @staticmethod
    def register_out(*args, **kwargs):
        """
            建议先使用本函数，将实例从静态变量__instances中删除，然后再使用 del 来删除实例。
                由于在实现单例模式时，需要使用静态变量来记录实例。
                因此无法直接通过 del 来消除对于某个实例的所有引用，来触发gc垃圾回收机制。

            建议与 del 联用：
                ins_to_del = Singleton_for_uid.register_out( uid=ins_uid )
                del ins_to_del
        """
        uid = kwargs.get('uid', None)
        assert uid in Singleton_for_uid.__instances, \
            Exception(f"uid {uid} not exists!")
        return Singleton_for_uid.__instances.pop(uid)

    @staticmethod
    def get_instances():
        return Singleton_for_uid.__instances


if __name__ == '__main__':
    class Node(Singleton_for_uid):
        Singleton_for_uid.class_name = "Node"

        def __init__(self, *args, **kwargs):
            super(Node, self).__init__(*args, **kwargs)

        def __del__(self):
            print("deleting ", self)


    "删除"
    node = Node(uid="ins_1")
    Node.register_out(uid=node.uid)
    del node
    print(2333)
    # deleting  <__main__.Singleton_for_uid object at 0x7f150c270b50>
    # 2333
    # 在 print 之前成功触发 del

    "测试单例模式"
    node_1 = Node(uid="111")
    node_2 = Node(uid="111")
    node_3 = Node()
    print(id(node_1), id(node_2), id(node_3))
    print(Node.get_instances())
    # 140482309115472 140482309115472 140482309115536
    # {'111': <__main__.Node object at 0x7fc49621ce50>, 'Node_0': <__main__.Node object at 0x7fc49621ce90>}

    node_4 = Node(uid="111", exist_ok=False)
