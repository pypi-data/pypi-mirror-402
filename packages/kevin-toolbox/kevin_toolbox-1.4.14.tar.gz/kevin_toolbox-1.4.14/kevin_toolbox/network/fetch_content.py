import warnings
from kevin_toolbox.network import get_response


def fetch_content(url=None, response=None, decoding=None, chunk_size=None, **kwargs):
    """
        从 URL/response 中获取内容

        参数：
            url:                <str> 请求的 URL 地址。
            response:           响应。
                        以上两个参数只需要指定其一即可，建议使用后者。
            decoding:           <str> 响应内容的解码方式
                                    默认为 None，返回原始的字节流。
                                    一些常用的可选值：
                                        "utf-8"
            chunk_size:         <int> 采用分块方式读取内容时，块的大小
                                    默认为 None，此时不使用分块读取，而直接读取所有内容
                        注意！当 chunk_size 非 None 时，decoding 将失效

        返回：
            当 chunk_size 为 None 时：
                str: 请求成功后的响应内容。如果 decoding 为 None，则返回 bytes 类型数据。
            当 chunk_size 非 None 时：
                读取内容的生成器。
    """
    assert url is not None or response is not None
    if url is not None:
        response = response or get_response(url=url, **kwargs)
    assert response is not None

    if chunk_size is None:
        content = response.data
        if decoding:
            content = content.decode(decoding)
        return content
    else:
        if decoding:
            warnings.warn(f'当 chunk_size 非 None 时，decoding 参数将失效。')
        return __generator(response, chunk_size)


def __generator(response, chunk_size):
    while True:
        chunk = response.read(chunk_size)
        if not chunk:
            break
        yield chunk


if __name__ == "__main__":
    url_ = "https://i.pinimg.com/736x/28/6a/b1/286ab1eb816dc59a1c72374c75645d80.jpg"  # "https://www.google.com/"
    print(len(fetch_content(url=url_, decoding=None)))
    for i, j in enumerate(fetch_content(url=url_, chunk_size=50000)):
        print(i, len(j))
