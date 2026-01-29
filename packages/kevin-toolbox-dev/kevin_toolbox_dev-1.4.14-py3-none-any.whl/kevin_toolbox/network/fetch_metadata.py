import os
import re
import time
import mimetypes
from urllib.parse import quote
from urllib.parse import urlsplit, unquote
from kevin_toolbox.network import get_response


def fetch_metadata(url=None, response=None, default_suffix=".bin", default_name=None, **kwargs):
    """
        从 URL/response 中获取文件名、后缀（扩展名）、大小等元信息

        参数：
            url:                <str> 请求的 URL 地址。
            response:           响应。
                        以上两个参数建议同时指定。
            default_suffix:     <str> 默认后缀。
            default_name:       <str> 默认文件名。
                                    默认为 None，表示使用当前时间戳作为默认文件名。
                    只有从 URL/response 中无法获取出 suffix 和 name 时才会使用上面的默认值作为填充

        返回：
            dict with keys ['content_length', 'content_type', 'content_disp', 'suffix', 'name']
    """
    assert url is not None or response is not None
    if url is not None:
        response = response or get_response(url=url, **kwargs)
    assert response is not None
    default_name = f'{time.time()}' if default_name is None else default_name

    metadata_s = {"content_length": None, "content_type": None, "content_disp": None, "suffix": None, "name": None}
    name, suffix = None, None
    # 尝试直接从url中获取文件名和后缀
    if url is not None:
        url = quote(url, safe='/:?=&')
        basename = unquote(os.path.basename(urlsplit(url).path))
        name, suffix = os.path.splitext(basename)
    # 尝试从更加可信的响应头中获取文件名和后缀
    content_length = response.headers.get("Content-Length", None)
    metadata_s["content_length"] = int(content_length) if content_length and content_length.isdigit() else None
    #
    content_type = response.headers.get("Content-Type", None)
    metadata_s["content_type"] = content_type
    if content_type:
        suffix = mimetypes.guess_extension(content_type.split(";")[0].strip()) or suffix
    #
    content_disp = response.headers.get("Content-Disposition", None)
    metadata_s["content_disp"] = content_disp
    if content_disp:
        temp_ls = re.findall('filename="([^"]+)"', content_disp)
        if temp_ls:
            name, temp = os.path.splitext(temp_ls[0])
            suffix = temp or suffix
    metadata_s["name"] = name or default_name
    metadata_s["suffix"] = suffix or default_suffix

    return metadata_s


# 示例用法
if __name__ == "__main__":
    url_ = "https://i.pinimg.com/736x/28/6a/b1/286ab1eb816dc59a1c72374c75645d80.jpg"  # "https://www.google.com/"
    print(fetch_metadata(url=url_))
