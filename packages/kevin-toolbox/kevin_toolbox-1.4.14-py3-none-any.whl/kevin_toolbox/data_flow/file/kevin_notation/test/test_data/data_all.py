import os

metadata_ls, content_ls, file_path_ls = [], [], []
from .data_0 import metadata, content

metadata_ls.append(metadata)
content_ls.append(content)
file_path_ls.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "data_0.kvt"))


from .data_1 import metadata, content

metadata_ls.append(metadata)
content_ls.append(content)
file_path_ls.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "data_1.kvt"))
