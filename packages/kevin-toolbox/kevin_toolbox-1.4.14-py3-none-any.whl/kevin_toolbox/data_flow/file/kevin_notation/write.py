from kevin_toolbox.data_flow.file import kevin_notation


def write(metadata, content, file_path):
    """
        写入整个文件的快捷接口
    """
    if "column_num" in metadata:
        metadata=metadata.copy()
        metadata.pop("column_num")
    with kevin_notation.Writer(file_path=file_path, mode="w", sep=metadata.get("sep", "\t")) as writer:
        writer.write_metadata(metadata=metadata)
        if isinstance(content, (dict,)):
            writer.write_contents(column_dict=content, b_single_line=False)  # 字典方式写入
        else:
            writer.write_contents(row_ls=content, b_single_line=False)  # 列表方式写入
