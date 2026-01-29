import os
import json
import mxupy as mu

config_files = {}
def read_config(file_name='config.json'):
    """ 
        读取配置信息

    Args:
        file_name (str): 文件名称

    Returns:
        json: 配置信息
    """
    # 防止对文件多次请求
    j = config_files.get(file_name)
    if j:
        return j
    
    text = mu.readAllText(os.path.join(mu.appPath(), file_name))
    j = json.loads(text) if text else {}
    config_files[file_name] = j
    
    return j
