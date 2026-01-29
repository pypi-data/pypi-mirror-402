import re


def find_links(text, b_compact_format=True, type_ls=None):
    """
        查找文本中的链接

        参数:
            text:               <str> 文本
            b_compact_format:   <bool> 是否只返回 link 部分
                                    默认为 True，此时返回 link_ls，其中每个元素是一个链接
                                    当设置为 False，此时返回 (link_ls, part_slices_ls, link_idx_ls)，
                                        其中 part_slices_ls 是链接和链接前后文本在 text 中对应的 slice，
                                        而 link_idx_ls 指出了 part_slices_ls 中第几个元素对应的是链接，
                                        link_idx_ls 与 link_ls 依次对应。
            type_ls:              <list of str> 找出哪种类型的链接
                                    默认为 None，此时表示找出所有类型的链接。
                                    支持以下取值：
                                        "url", "image"
    """

    matches = re.finditer(r'\[(.*?)\]\((.*?)(?:\s*["\'](.*?)["\'])?\)', text, re.DOTALL)

    link_ls = []
    part_slices_ls = []
    link_idx_ls = []
    start = 0
    for match in matches:
        link_start, link_end = match.start(), match.end()
        #
        if text[link_start - 1] == "!":
            type_ = "image"
            link_start -= 1
        else:
            type_ = "url"
        #
        if type_ls is not None and type_ not in type_ls:
            continue
        #
        part_slices_ls.append([start, link_start])
        # 图片本身
        link_s = dict(
            type_=type_,
            name=match.group(1),
            target=match.group(2),
            title=match.group(3) if match.group(3) else None
        )
        link_idx_ls.append(len(part_slices_ls))
        link_ls.append(link_s)
        part_slices_ls.append([link_start, link_end])
        # 更新起始位置
        start = match.end()

    last = text[start:]
    if last:
        part_slices_ls.append([start, len(text)])

    if b_compact_format:
        return link_ls
    else:
        return link_ls, part_slices_ls, link_idx_ls


if __name__ == "__main__":
    markdown_text = """
    Here is an image:
    ![This is a picture of a cat](http://example.com/cat.jpg "A cute cat")
    And another one:
    ![This is a picture of a dog](http://example.com/dog.jpg 'A cute dog')
    And one without alt text:
    [](http://example.com/placeholder.jpg)
    And one without title:
    ![<image_name>](<image_path>)
    """
    from kevin_toolbox.data_flow.file import markdown

    print(markdown.generate_list(find_links(text=markdown_text, b_compact_format=True)))

    link_ls_, part_slices_ls_, link_idx_ls_ = find_links(text=markdown_text, b_compact_format=False, type_ls=["url"])

    print(link_ls_)
    for part_slices in part_slices_ls_:
        print(part_slices)
        print(markdown_text[part_slices[0]:part_slices[1]])
