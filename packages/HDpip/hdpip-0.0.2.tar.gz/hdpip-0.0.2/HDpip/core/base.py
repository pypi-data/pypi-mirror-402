"""
- HDpip: A pip GUI based on maliang
- Copyright © 2025 寒冬利刃.
- License: MPL-2.0

本文件包含本包所有的基础功能，~~全是屎山💩~~。
"""

import pathlib
import os
import sys
import json
import platform
import pip
import subprocess
import functools

class HDpipError(Exception):
    """
    抛出一个HDpip错误，初始化函数可以接受一个`message`参数。

    例如：
    ```
    raise HDpip.core.base.HDpipError("炸了！")
    ```

    ***您不应该使用它**，如果您不是HDpip的开发者。*
    """

    def __init__(self, message = None) -> None:
        self.message = message
        super().__init__(self.message)

def unfinshed() -> None:
    """
    用于未完成功能的占位，使用`HDpipError`抛出一个错误。
    """

    raise HDpipError("\033[1m\033[91m不是，哥们，你写了这个功能吗？！\033[0m")


class Data():
    """
    接受一个`.json`文件（使用`open`函数打开文件，并使用`load`函数加载。），生成一个数据类。
    
    但是，您应该如此获得数据：
    ```
    d = Data()
    d.open("data.json")
    d.load() #这是必须的，因为在open后不会自动运行load函数。
    print(d.data[0][0])
    ```
    """

    def open(self, file: str | pathlib.Path, encoding: str = "utf-8") -> dict[str: str]:
        """
        绑定一个`.json`文件，且返回绑定的文件字典。
        
        :param self: `Data`类
        :param file: 一个指向`.json`文件的路径，如`data.json`
        :type file: str | pathlib.Path
        :param encoding: 编码字符串，如`utf-8`
        :type encoding: str
        :param mode: 文件打开模式，如`w+`
        :type mode: str
        :return: 文件字典
        :rtype: dict[str: str]
        """

        file = str(file)
        self.file = {"file": file, "encoding": encoding}
        return self.file
    
    def load(self) -> list | dict:
        """
        加载`.json`文件的数据至数据类并返回。
        
        :param self: `Data`类
        :return: 数据
        :rtype: list | dict
        """

        with open(**self.file, mode = "r") as f:
            self.data = json.load(f)
        return self.data
    
    def save(self) -> list | dict:
        """
        保存`.json`文件的数据至文件并返回。
        
        :param self: `Data`类
        :return: 数据
        :rtype: list | dict
        """

        with open(**self.file, mode = "w") as f:
            json.dump(self.data, f)
        return self.data
    
    def __iter__(self):
        return self.data.__iter__()
    
    def __next__(self):
        return self.data.__next__()
    
    def __getitem__(self, index):
        return self.data.__getitem__(index)
    
    def __setitem__(self, index, value):
        return self.data.__setitem__(index, value)

    def __delitem__(self, index):
        return self.data.__delitem__(index)

def getBaseDir() -> pathlib.Path:
    """
    获取HDpip的根目录，即`main.py`所在目录。
    
    :return: 路径
    :rtype: pathlib.Path
    """

    return pathlib.Path(__file__).parents[1]

def getPythonPath() -> pathlib.Path:
    """
    获取运行HDpip的Python的路径。
    
    :return: 路径
    :rtype: pathlib.Path
    """

    return pathlib.Path(sys.executable)

@functools.total_ordering
class Version():
    """
    强大的版本类，基本实现了所有我要用的功能。
    
    ~~我对它很满意。😎——寒冬利刃~~

    **开始**

    >>> version = Version("0.1.0")
    "0.1.0"
    >>> version = Version([0, 1, 0])
    "0.1.0"
    >>> version = Version((0, 1, 0))

    其实有不标准的写法，*但是合法*。

    >>> version = Version([0, "1", 0])

    **转换**

    >>> str(version)
    "0.1.0"

    >>> list(version)
    [0, 1, 0]

    >>> tuple(version)
    (0, 1, 0)

    当然，我不推荐使用`tuple`形式。

    **格式化**

    请传入另一个`Version`类，或者可以转换为`Version`类的，然后会将它们等长化。

    >>> version_ = Version("1")
    "1"
    >>> version.format(version_)
    (Version("0.1.0"), Version("1.0.0"))

    >>> version.format("2")
    (Version("0.1.0"), Version("2.0.0"))

    **富比较**

    >>> version == version_
    False
    >>> version <= version_
    True

    特别地，对于*约等于*（默认比较前两位）。

    >>> version.isCloseTo("0.1.1")
    True

    **多重富比较**

    >>> version.multipleCompare(">0.0.0,<2,~=0.1.1,!=0.1.5")
    True

    >>> version.multipleCompare([">0.0.0", "<2", "~=0.1.1", "!=0.1.5"])
    True

    如你所见，`~=`和`!=`**都是支持的**。

    对于`==`模式，可以不写`==`，如`version.multipleCompare("0.1.0,>0.0.0")`，但为何不直接用富比较呢？

    **键操作**

    *只能读取！*

    比如`for`循环：

    ```
    for i in version:
        print(i)
    ```

    像列表一样：
    >>> version[1]
    1
    """

    def __init__(self, raw: str | tuple[str, int] | list[str, int]):
        self._list = []
        if isinstance(raw, str):
            self._list = raw.split(".")
        elif isinstance(raw, tuple):
            self._list = list(raw)
        elif isinstance(raw, list):
            self._list = raw
        elif raw.__class__ == "Version":
            self = raw
        else:
            self =  NotImplemented
            raise TypeError(f"版本支持str或tuple[str, int]或list[str, int]类型，但您输入的是{type(raw).__name__}类型！")
        for i in range(0, len(self._list)):
            self._list[i] = int(self._list[i])
        
        self._str = ""
        for i in range(0, len(self._list)):
            self._str += str(self._list[i])
            if not i == len(self._list) - 1:
                self._str += "."
        
        self._tuple = tuple(self._list)
    
    def __len__(self):
        return self._list.__len__()
    
    def __list__(self):
        return self._list

    def __str__(self):
        return self._str
    
    def __tuple__(self):
        return self._tuple
    
    def __iter__(self):
        return self._list.__iter__()
    
    def __next__(self):
        return self._list.__next__()
    
    def __getitem__(self, index):
        return self._list.__getitem__(index)
    
    def __setitem__(self, index, value):
        raise HDpipError(f"您在尝试设置Version类的键，\033[1m\033[91m但是这是被禁止的！\033[0m")

    def __delitem__(self, index):
        raise HDpipError(f"您在尝试删除Version类的键，\033[1m\033[91m但是这是被禁止的！\033[0m")
    
    def format(self, value: str | tuple[int, str] | list[str, int]) -> tuple:
        """
        请传入另一个`Version`类，或者可以转换为`Version`类的，然后会将它们等长化。

        >>> version = Version("0.1.0")
        "0.1.0"

        >>> version_ = Version("1")
        "1"
        >>> version.format(version_)
        (Version("0.1.0"), Version("1.0.0"))

        >>> version.format("2")
        (Version("0.1.0"), Version("2.0.0"))
        
        :param self: `Version`类
        :param value: 另一个版本
        :type value: Version | str | tuple[int, str] | list[str, int]
        :return: 版本元组
        :rtype: tuple[Version] | NotImplemented
        """

        if not isinstance(value, Version):
            try:
                value = Version(value)
            except Exception:
                return NotImplemented
        if len(self._list) == len(value._list):
            return (Version(self._list), Version(value._list))
        elif len(self._list) < len(value._list):
            self_ = self._list
            while len(self_) < len(value._list):
                self_.append(0)
            return (Version(self_), Version(value._list))
        elif len(self._list) > len(value._list):
            value_ = value._list
            while len(self._list) > len(value_):
                value_.append(0)
            return (Version(self._list), Version(value_))

    def __eq__(self, value):
        _format = self.format(value)
        if _format == NotImplemented:
            return NotImplemented
        elif isinstance(_format, tuple):
            ls, lv = _format
        return ls._list == lv._list
    
    def __lt__(self, value):
        _format = self.format(value)
        if _format == NotImplemented:
            return NotImplemented
        elif isinstance(_format, tuple):
            ls, lv = _format
        for i1, i2 in zip(ls._list, lv._list):
            if i1 < i2:
                return True
            elif i1 > i2:
                return False
            elif i1 == i2:
                pass
        return False
    
    def isCloseTo(self, value: str | tuple[int, str] | list[str, int]) -> bool:
        """
        富比较中的约等于（默认比较前两位），但您**必须如此调用**：

        >>> version = Version("0.1.0")
        "0.1.0"
        >>> version.isCloseTo("0.1.1")
        True
        
        :param self: `Version`类
        :param value: 另一个版本
        :type value: Version | str | tuple[int, str] | list[str, int]
        :return: 结果
        :rtype: bool | NotImplemented
        """

        _format = self.format(value)
        if _format == NotImplemented:
            return NotImplemented
        elif isinstance(_format, tuple):
            ls, lv = _format
        
        return ls._list[:2] == lv._list[:2]
    
    def multipleCompare(self, standard: str | list[str]) -> bool:
        """
        多重富比较，即开即用。

        >>> version = Version("0.1.0")
        "0.1.0"
        
        >>> version.multipleCompare(">0.0.0,<2,~=0.1.1,!=0.1.5")
        True

        >>> version.multipleCompare([">0.0.0", "<2", "~=0.1.1", "!=0.1.5"])
        True

        如你所见，`~=`和`!=`**都是支持的**。

        对于`==`模式，可以不写`==`，如`version.multipleCompare("0.1.0,>0.0.0")`，但为何不直接用富比较呢？
        
        :param self: `Version`类
        :param standard: 富比较标准
        :type standard: str | list[str]
        :return: 结果
        :rtype: bool | NotImplemented
        """

        if isinstance(standard, str):
            standard = standard.split(",")
        for i in standard:
            mode = i[:2]
            if not mode in ["==", "!=", "~=", ">=", "<="]:
                mode = i[:1]
                if not mode in [">", "<"]:
                    mode = "=="
                    value = Version(i)
                else:
                    value = Version(i[1:])
            else:
                value = Version(i[2:])
            _format = self.format(value)
            if _format == NotImplemented:
                return NotImplemented
            elif isinstance(_format, tuple):
                ls, lv = _format

            if mode == "==":
                if not ls == lv:
                    return False
            elif mode == "!=":
                if not ls != lv:
                    return False
            elif mode == "~=":
                if not ls.isCloseTo(lv):
                    return False
            elif mode == ">":
                if not ls > lv:
                    return False
            elif mode == "<":
                if not ls < lv:
                    return False
            elif mode == ">=":
                if not ls >= lv:
                    return False
            elif mode == "<=":
                if not ls <= lv:
                    return False
        return True

def getPythonVersion() -> Version:
    """
    获取运行HDpip的Python的版本。
    
    :return: 版本
    :rtype: Version
    """

    return Version(platform.python_version_tuple())

def getPipVersion() -> Version:
    """
    获取运行HDpip的Python所对应的pip的版本。
    
    :return: 版本
    :rtype: Version
    """

    return Version(pip.__version__)

def openInExplorer(path: str | pathlib.Path) -> None:
    """
    在文件资源管理器中打开一个文件夹或文件（Windows下选中，Linux或MacOS下打开父文件夹。）。
    
    :param path: 要打开的文件夹
    :type path: str | pathlib.Path
    """

    path = pathlib.Path(path).resolve()
    system = platform.system()
    if system != "Windows" and path.is_file():
        path = path.parent.resolve()
    
    try:
        if system == "Windows":
            if path.is_file():
                os.system(f"explorer /select, \"{path}\"")
            else:
                os.startfile(path)
        elif system == "Linux":
            os.system(f"xdg-open \"{path}\"")
        elif system == "Darwin":
            os.system(f"open \"{path}\"")
        else:
            raise HDpipError(f"不支持的系统：{system}！")
    except Exception as error:
        raise HDpipError(f"打开\"{path}\"失败！\n错误如下：\n{error}")

def shell(command: str, realtime: bool = True, callback = print) -> subprocess.Popen:
    """
    使用系统shell运行一条指令，每输出一行，如果启用实时模式，运行以更新行为输入的回调函数，并返回管道。

    **注意，*禁止运行交互式命令！***

    例如：
    ```
    with open("result.txt", "a", encoding = "utf-8") as file:
        print(HDpip.core.base.shell(
            "ping 127.0.0.1", 
            lambda line: file.write(f"{line}\n")
        ).returncode)
    ```
    
    :param command: 命令
    :type command: str
    :param realtime: 实时模式
    :type realtime: bool
    :param callback: 回调函数
    :return: 管道
    :rtype: subprocess.Popen
    """
    
    popen = subprocess.Popen(
        command, 
        stdout = subprocess.PIPE, 
        universal_newlines = realtime
    )
    if realtime:
        for line in popen.stdout:
            callback(line.strip())
    popen.wait()
    return popen

def shellDecode(raw: str | bytes) -> str:
    """
    对`HDpip.core.base.shell`的输出进行解码。
    
    :param raw: 原始数据
    :type raw: str | bytes
    :return: 解码结果
    :rtype: str
    """

    return bytes(raw).decode("cp936")

def multipleSpilt(string: str, spilt_symbol: str | list[str]) -> list[str]:
    """
    按照多个分隔符分割字符串，请输入如同`"|,."`或`["|", "."]`的分隔符，`str`模式以`,`分割列表。
    
    :param string: 字符串
    :type string: str
    :param spilt_symbol: 分隔符字符串或列表
    :type spilt_symbol: str | list[str]
    :return: 结果
    :rtype: list[str]
    """
    if isinstance(spilt_symbol, str):
        spilt_symbol = spilt_symbol.split(",")

    if len(spilt_symbol) == 0:
        HDpipError("分隔符列表不能为空！")
    elif len(spilt_symbol) > 1:
        for i in range(1, len(spilt_symbol)):
            string = string.replace(spilt_symbol[i], spilt_symbol[0])
    return string.split(spilt_symbol[0])

def isDev() -> bool:
    """
    检测是否是开发模式，如果启用，请在父目录创建`dev`文件。

    ***您不应该使用它**，如果您不是HDpip的开发者。*
    
    :return: 是否是开发模式
    :rtype: bool
    """

    return (pathlib.Path(f"{getBaseDir}").parent / "dev").resolve().is_file()