"""
- HDpip: A pip GUI based on maliang
- Copyright © 2025 寒冬利刃.
- License: MPL-2.0

本文件包含本包使用的所有pip API。
"""

import json
import pathlib
import yaml
import subprocess
import urllib.parse

try:
    from . import base
except ImportError:
    import base

def getPip(python: str | pathlib.Path = base.getPythonPath()) -> str:
    """
    获取指定Python对应的pip执行头（例如`"D:\\Program Files\\Python310\\python.exe" -m pip`。），默认为运行HDpip的，您也可以直接使用变量`HDpip.core.pip.pip_head`。
    
    :param python: 指定的Python
    :type python: str | pathlib.Path
    :return: pip执行头
    :rtype: str
    """
    return f"\"{python}\" -m pip"

pip_head = getPip()

def version(pip_head: str = pip_head) -> dict[str: str, str: pathlib.Path]:
    """
    返回运行`pip -V`的结果，参见`HDpip.core.base.shell()`。
    
    结果应为如下字典：
    ```
    {
        "pip_version": base.Version("25.3"), 
        "pip_path": pathlib.Path("D:\\Program Files\\Python310\\lib\\site-packages\\pip"), 
        "python_version": base.Version("3.10")
    }
    ```
    
    :param pip_head: pip执行头
    :type pip_head: str
    :return: 数据字典
    :rtype: dict[str: base.Version, str: pathlib.Path]
    """
    
    string = base.shellDecode(base.shell(f"{pip_head} -V", False).stdout.read())
    string = base.multipleSpilt(string, ["pip ", " from ", " (python ", ")\r\r\n"])
    string_ = []
    for i in string:
        if not i == "":
            string_.append(i)
    result = {
        "pip_version": base.Version(string_[0]), 
        "pip_path": pathlib.Path(string_[1]), 
        "python_version": base.Version(string_[2])
    }
    return result

def list(option: str | None = None, pip_head: str = pip_head) -> list:
    """
    返回运行`pip list --format=json`的结果，参见`HDpip.core.base.shell()`。

    结果应为如下列表：
    ```
    [
        {"name": "pip", "version": "25.3"}, 
        {"name": "HDpip", "version": "0.0.0"}, 
        ...
    ]
    ```
    
    :param pip_head: pip执行头
    :type pip_head: str
    :return: 包列表
    :rtype: list
    """

    if not (option is None or option == ""):
        option = f" {option}"
    return json.loads(base.shellDecode(base.shell(f"{pip_head} list --format=json{option}", False).stdout.read()))

def show(package: str, pip_head: str = pip_head) -> dict:
    """
    返回运行`pip show`的结果，参见`HDpip.core.base.shell()`。

    结果应为如下字典：
    ```
    {
        "Name": "HDpip", 
        "Version": "0.0.0", 
        ...

    }
    ```
    
    :param package: 要获取信息的包
    :type package: str
    :param pip_head: pip执行头
    :type pip_head: str
    :return: 包信息
    :rtype: dict
    """
    
    return yaml.safe_load(base.shellDecode(base.shell(f"{pip_head} show {package}", False).stdout.read()))

def getPackageDir(package: str, pythonPath: pathlib.Path  | str = base.getPythonPath()) -> pathlib.Path:
    """
    返回包路径。
    
    :param package: 包名
    :type package: str
    :return: 包路径
    :rtype: pathlib.Path
    """
    
    pythonPath = pathlib.Path(pythonPath)

    if not base.isDev():
        return (base.getBaseDir().parent / package).resolve()
    else:
        return (pythonPath.parent / "Lib" / "site-packages"/ package).resolve()

def install(package: str, callback = print, index: str | None = None, pip_head: str = pip_head) -> subprocess.Popen:
    """
    返回运行`pip install`的结果，参见`HDpip.core.base.shell()`。
    
    :param package: 包名
    :type package: str
    :param callback: 回调函数
    :param index: 索引（镜像）
    :type index: str | None
    :param pip_head: pip执行头
    :return: 管道
    :rtype: subprocess.Popen
    """

    if not (index is None or index == ""):
        host = urllib.parse.urlparse(index).netloc
        option = f" -i {index} --trusted-host {host}"
    return base.shell(f"{pip_head} install {package}{option}", True, callback)

def uninstall(package: str, callback = print, pip_head: str = pip_head) -> subprocess.Popen:
    """
    返回运行`pip uninstall`的结果，参见`HDpip.core.base.shell()`。
    
    :param package: 包名
    :type package: str
    :param callback: 回调函数
    :param pip_head: pip执行头
    :return: 管道
    :rtype: subprocess.Popen
    """

    return base.shell(f"{pip_head} uninstall {package} --yes")