from kevin_toolbox.data_flow.file.markdown.table import Table_Format, get_format
from kevin_toolbox.data_flow.file.markdown.table.convert import matrix_to_complete, complete_to_matrix


def simple_to_complete(content_s):
    return {i: {"title": k, "values": v} for i, (k, v) in enumerate(content_s.items())}


def complete_to_simple(content_s):
    temp = {v_s["title"] for v_s in content_s.values()}
    if len(temp) != len(set(temp)):
        raise AssertionError(f'Fail to convert SIMPLE_DICT to COMPLETE_DICT, because there are some duplicate titles.')
    content_s = {v_s["title"]: v_s["values"] for v_s in content_s.values()}
    return content_s


CONVERT_PROCESS_S = {
    (Table_Format.COMPLETE_DICT, Table_Format.SIMPLE_DICT): complete_to_simple,  # (from, to): process
    (Table_Format.COMPLETE_DICT, Table_Format.MATRIX): lambda x: complete_to_matrix(content_s=x),
    (Table_Format.SIMPLE_DICT, Table_Format.COMPLETE_DICT): simple_to_complete,
    (Table_Format.SIMPLE_DICT, Table_Format.MATRIX): lambda x: complete_to_matrix(content_s=simple_to_complete(x)),
    (Table_Format.MATRIX, Table_Format.COMPLETE_DICT): lambda x: matrix_to_complete(**x),
    (Table_Format.MATRIX, Table_Format.SIMPLE_DICT): lambda x: complete_to_simple(content_s=matrix_to_complete(**x))
}


def convert_format(content_s, output_format, input_format=None):
    """
        在各种表格格式之间进行转换
            ！！注意！！这些转换虽然不会改变表格的内容，但是可能会导致格式信息的丢失

        参数：
            content_s:          <表格内容>
            input_format:       <str> 描述输入的格式。
                                    默认为 None，将根据 content_s 实际格式进行推断。
            output_format:      <str/list of str> 输出的目标格式。
                                    当输入是一个 tuple/list 时，将输出其中任一格式，具体规则为：
                                        - 当 input_format 不在可选的输出格式中时，优先按照第一个输出格式进行转换
                                        - 当 input_format 在可选的输出格式中时，不进行转换。
    """
    if input_format is None:
        input_format = get_format(content_s=content_s)
    input_format = Table_Format(input_format)
    if not isinstance(output_format, (list, tuple,)):
        output_format = [output_format]
    output_format = [Table_Format(i) for i in output_format]

    if input_format in output_format:
        return content_s
    else:
        return CONVERT_PROCESS_S[(input_format, output_format[0])](content_s)
