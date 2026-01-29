def getHTMLFromClipboard():
    """
    从剪贴板获取 HTML 数据。

    返回:
        str: 如果可用，返回剪贴板中的 HTML 数据。
    """
    import win32clipboard
    import win32con
    win32clipboard.OpenClipboard()
    fmt = win32clipboard.EnumClipboardFormats(0)
    fmtName = win32clipboard.GetClipboardFormatName(fmt)
    cdata = ""
    if fmtName == 'HTML Format':
        cdata = win32clipboard.GetClipboardData(fmt)
        cdata = cdata.decode('utf-8').strip('\x00')
        cdatas = cdata.split('\r\n')
        del cdatas[0:6]
        cdata = '\r\n'.join(cdatas)

    win32clipboard.CloseClipboard()

    return cdata


def getImageFromClipboard():
    """
    从剪贴板获取图像。

    返回:
        list: 如果可用，返回剪贴板中的图像列表。
    """
    from PIL import ImageGrab, Image

    paths = ImageGrab.grabclipboard()
    imgs = []
    if paths is not None:
        for path in paths:
            img = Image.open(path)
            imgs.append(img)
    return imgs
