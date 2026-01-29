import os
import pytest
from kevin_toolbox.env_info.variable_ import Env_Vars_Parser
from kevin_toolbox.patches.for_test import check_consistency


@pytest.mark.parametrize(
    "input_text, expected",
    [
        # 验证 ${<cfg_name>:<var_name>} 的情况
        (
                "666/123${SYS:HOME}/afasf/${/xxx.../xxx.json:111:222}336",
                ["666/123", ("SYS", [':'], ['HOME']), "/afasf/", ("/xxx.../xxx.json", [':', ':'], ['111', '222']),
                 "336"]
        ),
        # 验证 ${<cfg_name>} 和 ${:<var_name>} 的混合情况
        (
                "start${CFG}middle${:VAR}end",
                ["start", ("CFG", [], []), "middle", ('', [':'], ['VAR']), "end"]
        ),
        (
                "${:VAR}",
                [('', [':'], ['VAR'])]
        ),
        (
                "${CFG}",
                [("CFG", [], [])]
        ),
        (
                "{:VAR}",
                ["{:VAR}"]
        ),
    ]
)
def test_split_string_in_env_vars_parser(input_text, expected):
    result = Env_Vars_Parser.split_string(input_text)
    check_consistency(result, expected)


def test_env_vars_parser_0():
    env_cfg_file = os.path.expanduser("~/.kvt_cfg/.temp.json")
    from kevin_toolbox.data_flow.file import json_
    json_.write(content={"dataset_dir": ["~/data", "~/dataset"], "version": "001"}, file_path=env_cfg_file)
    input_text = "/root/${KVT_TEMP:dataset_dir@1}/${KVT_TEMP:version}/${HOME}/${SYS:HOME}"
    expected = "/".join(["/root/~/dataset/001", ] + [os.path.expanduser("~")] * 2)

    #
    parser = Env_Vars_Parser()
    result = parser(input_text)
    check_consistency(expected, result)
