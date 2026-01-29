import xml.etree.ElementTree as ET
from xml.parsers.expat import ExpatError

def is_valid_xml(src):
    """
        检查给定的字符串是否是一个有效的 XML 文档。

        参数：
        - src: 一个字符串，表示 XML 文档。

        返回：
        - 如果 src 是有效的 XML 文档，则返回 True；否则返回 False。
    """

    xml = False
    if not isinstance(src, str):
        print("错误: src 必须是字符串")
        return xml
    
    try:
        ET.fromstring(src)
        xml = True
    except (ExpatError, ET.ParseError) as e:
        print(f"XML 解析失败（可忽略）: {e}")
        pass
    except Exception as e:
        print(f"未知错误: {e}")
        pass
    
    return xml

