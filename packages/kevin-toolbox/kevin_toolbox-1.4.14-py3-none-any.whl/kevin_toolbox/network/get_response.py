import urllib3
from urllib.parse import quote
from kevin_toolbox.computer_science.algorithm.decorator import retry
from kevin_toolbox.network.variable import DEFAULT_HEADERS

# 全局 PoolManager 实例，设置 cert_reqs='CERT_NONE' 可关闭 SSL 证书验证
http = urllib3.PoolManager(cert_reqs='CERT_NONE')


def get_response(url, data=None, headers=None, method=None, retries=3, delay=0.5, b_verbose=False, stream=True,
                 **kwargs):
    """
        获取 url 的响应

        参数：
            url:                <str> 请求的 URL 地址。
            data:               <bytes, optional> 请求发送的数据，如果需要传递数据，必须是字节类型。
            headers:            <dict> 请求头字典。
                                    默认为 DEFAULT_HEADERS。
            method:             <str> HTTP 请求方法，如 "GET", "POST" 等。
            retries:            <int> 重试次数
                                    默认重试3次
            delay:              <int/float> 每次重试前等待的秒数。
                                    默认0.5秒
            b_verbose:          <boolean> 进行多次重试时是否打印详细日志信息。
                                    默认为 False。

        返回：
            响应。 urllib3.response.HTTPResponse object
    """
    headers = headers or DEFAULT_HEADERS

    url = quote(url, safe='/:?=&')
    worker = retry(retries=retries, delay=delay, logger="default" if b_verbose else None)(func=__worker)
    response = worker(url, data, headers, method, stream)
    return response


def __worker(url, data, headers, method, stream):
    method = method if method is not None else "GET"
    response = http.request(method, url, body=data, headers=headers, preload_content=not stream)
    if response.status >= 400:
        raise Exception(f"HTTP 请求失败，状态码：{response.status}")
    return response


if __name__ == "__main__":
    url_ = "https://i.pinimg.com/736x/28/6a/b1/286ab1eb816dc59a1c72374c75645d80.jpg"  # "https://www.google.com/"
    a = get_response(url=url_, b_verbose=True)
    print(a)
