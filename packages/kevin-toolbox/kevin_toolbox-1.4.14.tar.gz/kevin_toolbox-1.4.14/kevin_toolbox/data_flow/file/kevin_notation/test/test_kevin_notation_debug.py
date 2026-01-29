import pytest
import os
from kevin_toolbox.data_flow.file import kevin_notation
from kevin_toolbox.patches.for_test import check_consistency
from kevin_toolbox.data_flow.file.kevin_notation.test.test_data.data_all import metadata_ls, content_ls, file_path_ls

data_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "test_data")


@pytest.mark.parametrize("expected_metadata, expected_content, file_path",
                         zip(metadata_ls, content_ls, file_path_ls))
def test_write(expected_metadata, expected_content, file_path):
    print("test write()")

    """
    当写入的列的元素不一致时，是否能正常报错
    """

    # 新建
    file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "test_data/temp", os.path.basename(file_path))

    # 字典方式写入
    if len(expected_content) > 1:
        with pytest.raises(AssertionError):
            list(expected_content.values())[0].clear()
            kevin_notation.write(metadata=expected_metadata, content=expected_content, file_path=file_path)


def test_read():
    """
        测试在不启用注释时，能否正确读取带有 // 的值
            bug 原因：由于之前的版本默认启用"//"作为注释符号，因此导致无法正确读取带有"//"的值
            解决：在 Kevin_Notation_Reader 和 Kevin_Notation_Writer 取消默认使用注释，并限定只有在 metadata 中显式指定注释标志符才会启用
    """
    input_file = os.path.join(data_dir, "data_2.kvt")
    metadata, content = kevin_notation.read(file_path=input_file)
    check_consistency(
        {'image_path': ['a//image1.jpg'], 'label': [0]}, content
    )
