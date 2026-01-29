from .node import Node
from .sender import Sender
from .getter import Getter


class Graph:
    def __init__(self):
        self.getter_db = dict()
        self.sender_db = dict()
        self.node_db = dict()

    def add_node(self, exist_ok=False, uid=None, **kwargs):
        assert isinstance(uid, (str, type(None),)), \
            TypeError(f"uid should be string or None, but get a {type(uid)}!")

        if uid is None or uid not in self.node_db:
            # uid不存在，新建节点
            node = Node(uid=uid, **kwargs)
        else:
            # uid已存在
            if not exist_ok:
                raise Exception(f"Node {kwargs['uid']} already exists!")
            node = self.node_db[uid]
        return node