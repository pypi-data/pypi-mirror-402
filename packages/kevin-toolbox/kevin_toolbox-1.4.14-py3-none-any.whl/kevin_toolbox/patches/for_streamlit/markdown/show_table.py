import streamlit as st
from kevin_toolbox.data_flow.file.markdown.table import find_tables
from kevin_toolbox.data_flow.file.markdown.link import find_links
from kevin_toolbox.computer_science.algorithm.for_dict import deep_update
from kevin_toolbox.patches.for_streamlit.markdown import show_image

DEFAULT_DISPLAY_MODE_S = {
    "table_with_image": "by_columns",  # 对于带有图片的表格选择哪种方式显示
    "default": "by_markdown"  # 对于其他表格选择哪种方式显示
}


def _show_table_by_columns(matrix, doc_dir, table_name, **kwargs):
    tab, _ = st.tabs([table_name, "[click to hide table]"])
    with tab:
        for row in matrix:
            col_ls = st.columns(len(row))
            for col, i in zip(col_ls, row):
                with col:
                    show_image(text=i, doc_dir=doc_dir)


METHOD_S = {
    "by_columns": _show_table_by_columns,
    "by_markdown": lambda text, **kwargs: st.markdown(text)
}


def show_table(text, doc_dir=None, display_mode_s=None):
    """
        对 st.markdown 中表格显示部分的改进，具有以下优点
            - 支持显示带有本地图片的表格
            - 支持以下几种方式来显示表格：
                - 用 st.columns 分列分行显示
                - 用 st.markdown 显示（不支持本地图片）
                - 用 st.data_editor 显示（TODO）
    """
    global DEFAULT_DISPLAY_MODE_S, METHOD_S
    display_mode_s = deep_update(stem=DEFAULT_DISPLAY_MODE_S.copy(), patch=display_mode_s if display_mode_s else dict())
    for v in display_mode_s.values():
        assert v in ["by_columns", "by_markdown"]  # "by_data_editor"

    table_ls, part_slices_ls, table_idx_ls = find_tables(text=text, b_compact_format=False)
    for idx, part_slices in enumerate(part_slices_ls):
        part = text[slice(*part_slices)]
        if idx in table_idx_ls:
            table_s = table_ls.pop(0)
            if len(find_links(text=part, b_compact_format=True, type_ls=["image"])) > 0:
                # 带有图片的表格
                method = METHOD_S[display_mode_s["table_with_image"]]
            else:
                method = METHOD_S[display_mode_s["default"]]
            method(text=part, matrix=table_s["matrix"], doc_dir=doc_dir, table_name=f'Table {idx}')
        else:
            # 是表格，且内部无图片，则直接显示
            show_image(text=part, doc_dir=doc_dir)

# 另一种显示表格的方式是通过 data_editor 来显示，但是对图片的显示效果不好
# TODO 可以选择是通过 data_editor 还是 columns，或者原始格式（对本地图片不处理或者使用 base64 代替）来显示表格
# # 创建一个 DataFrame
# data = {
#     'Description': ['This is an image.', "2"],
#     'Image': [f'data:image/png;base64,{convert_image_to_base64(temp)}', temp]  # 使用 Markdown 格式的图片
# }
#
# column_configuration = {
#     "Image": st.column_config.ImageColumn("Avatar", help="The user's avatar", width="large")
# }
#
# import pandas as pd
#
# df = pd.DataFrame(data)
#
# # 创建表格
# # st.table(df)
# st.data_editor(
#     df,
#     column_config=column_configuration,
#     use_container_width=True,
#     hide_index=True,
#     num_rows="fixed"
# )
