from kevin_toolbox.patches.for_streamlit.markdown import show_table


def show(text, doc_dir=None):
    """
        st.markdown 的改进版，具有以下优点
            - 对于带有图片的表格，用分列分行显示
            - 能够正确显示本地的图片
    """
    show_table(text=text, doc_dir=doc_dir)
