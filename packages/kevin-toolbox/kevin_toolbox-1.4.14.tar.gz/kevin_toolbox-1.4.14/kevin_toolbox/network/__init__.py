import urllib3
from urllib3.exceptions import InsecureRequestWarning

# 禁用不安全请求警告（例如当 verify=False 时）
urllib3.disable_warnings(InsecureRequestWarning)

from .get_response import get_response
from .fetch_metadata import fetch_metadata
from .fetch_content import fetch_content
from .download_file import download_file
