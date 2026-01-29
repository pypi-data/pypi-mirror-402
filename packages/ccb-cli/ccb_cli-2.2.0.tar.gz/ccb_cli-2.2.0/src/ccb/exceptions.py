"""
自定义异常类模块
"""


class ComicBookError(Exception):
    """所有CCB异常的基类。

    Attributes:
        message (str): 异常消息
    """

    pass


class UnsupportedFormatError(ComicBookError):
    """当输入或输出格式不被支持时抛出。

    Attributes:
        message (str): 异常消息
    """

    pass


class ArchiveError(ComicBookError):
    """当压缩或解压操作失败时抛出。

    Attributes:
        message (str): 异常消息
    """

    pass


class ConversionError(ComicBookError):
    """当转换操作失败时抛出。

    Attributes:
        message (str): 异常消息
    """

    pass
