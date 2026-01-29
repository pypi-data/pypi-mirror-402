from kevin_toolbox.data_flow.file import kevin_notation


def read(file_path=None, file_obj=None):
    """
        读取整个文件的快捷接口
    """
    assert file_path is not None or file_obj is not None

    with kevin_notation.Reader(file_path=file_path, chunk_size=-1, file_obj=file_obj) as reader:
        # metadata
        metadata = reader.metadata
        # content
        try:
            content = next(reader)
        except:
            content = {key: [] for key in metadata["column_name"]}
    return metadata, content
