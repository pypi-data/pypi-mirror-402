import re
import types
import random
import string

from mxupy import IM

def str_to_dict(src):
    """ 将查询字符串转换成字典

    Returns:
        dict: 字典
    """
    # 原始字符串
    # s = "a=1&b=2&c=3"
    src = str(src)
    if src.startswith('?'):
        src = src[1:]

    # 将字符串分割成键值对
    pairs = src.split("&")
    # 创建字典
    dic = {}
    for pair in pairs:
        # 分割键和值
        key, value = pair.split("=")
        # 将键和值添加到字典中
        dic[key] = value
        
    return dic

def str_to_obj(src):
    """ 将查询字符串转换成字典

    Returns:
        dict: 字典
    """
    dic = str_to_dict(src)

    # 将字典转换为对象
    obj = types.SimpleNamespace(**dic)
    return obj

def has_onsecutive_duplicates(password):
    """ 检查密码是否为存在连续字符

    Args:
        password (str): 密码

    Returns:
        bool: 存在连续字符否
    """
    # 检测重复字符（如 AAAAAA）# 连续3次及以上重复
    if re.search(r'(.)\1{2,}', password):
        return True
    
    # 检测连续数字（如 123456）
    if re.search(r'(?:012|123|234|345|456|567|678|789|987|876|765|654|543|432|321|210)+', password):
        return True
    
    # 检测连续字母（如 abcdef）
    if re.search(r'(?:abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz|zyx|yxw|xwv|wvu|vut|uts|tsr|srq|rqp|qpo|pon|onm|nml|mlk|lkj|kji|jih|ihg|hgf|gfe|fed|edc|dcb|cba)+', password, re.IGNORECASE):
        return True
    
    # 检测键盘连续键（如 qwerty）
    keyboard_sequences = [
        'qwertyuiop', 'asdfghjkl', 'zxcvbnm',
        'poiuytrewq', 'lkjhgfdsa', 'mnbvcxz'
    ]
    for seq in keyboard_sequences:
        if seq in password.lower():
            return True
    
    return False

def check_password_strong(
    password: str,
    min_length: int = 8,
    require_uppercase: bool = True,
    require_lowercase: bool = True,
    require_digits: bool = True,
    require_special_chars: bool = True,
    onsecutive_duplicates: bool = True
) -> bool:
    """
    检查密码强度（支持参数化配置）
    
    Args:
        password: 待检查的密码
        min_length: 最小长度要求
        require_uppercase: 是否校验大写字母
        require_lowercase: 是否校验小写字母
        require_digits: 是否校验数字
        require_special_chars: 是否校验特殊字符
        onsecutive_duplicates: 是否校验连续字符
    Returns:
        bool: 是否符合强度要求
    """
    im = IM(True, '', password)
    
    code = 400
    special_chars = "!@#$%^&*"
    
    if len(password) < min_length:
        return im.set_error(f"密码长度不足, 需 {min_length} 个字符以上", code)
    if require_uppercase and not re.search(r"[A-Z]", password):
        return im.set_error("密码需要大写字母", code)
    if require_lowercase and not re.search(r"[a-z]", password):
        return im.set_error("密码需要小写字母", code)
    if require_digits and not re.search(r"[0-9]", password):
        return im.set_error("密码需要数字", code)
    if require_special_chars and not re.search(f'[{re.escape(special_chars)}]', password):
        return im.set_error(f"密码必须包含至少一个特殊字符 {special_chars}", code)
    if onsecutive_duplicates and has_onsecutive_duplicates(password):
        return im.set_error("密码不能包含连续字符", code)
        
    return im

def sanitize(data):
    """
    递归清理字符串
    
    Args:
        data: 待清理的数据
    
    Returns:
        dict|list|str: 清理后的数据
    """
    import bleach
    
    if isinstance(data, dict):
        return {k: sanitize(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize(item) for item in data]
    elif isinstance(data, str):
        return bleach.clean(data)
    
    return data



def generate_password(min_length=8, require_uppercase=True, require_lowercase=True, 
                      require_digits=True, require_special_chars=True, 
                      max_consecutive_duplicates=2):
    """
    生成符合强度要求的随机密码
    
    参数:
        min_length: 密码最小长度
        require_uppercase: 是否包含大写字母
        require_lowercase: 是否包含小写字母
        require_digits: 是否包含数字
        require_special_chars: 是否包含特殊字符
        max_consecutive_duplicates: 允许的最大连续重复字符数
        
    返回:
        生成的随机密码
    """
    # 定义字符集
    lowercase = string.ascii_lowercase if require_lowercase else ''
    uppercase = string.ascii_uppercase if require_uppercase else ''
    digits = string.digits if require_digits else ''
    special_chars = '!@#$%^&*' if require_special_chars else ''
    
    # 确保至少包含每种要求的字符类型
    all_chars = lowercase + uppercase + digits + special_chars
    if not all_chars:
        raise ValueError("至少需要启用一种字符类型")
    
    # 生成密码直到满足所有条件
    while True:
        password = []
        # 确保包含每种要求的字符类型
        if require_lowercase:
            password.append(random.choice(lowercase))
        if require_uppercase:
            password.append(random.choice(uppercase))
        if require_digits:
            password.append(random.choice(digits))
        if require_special_chars:
            password.append(random.choice(special_chars))
        
        # 填充剩余长度
        remaining_length = max(min_length - len(password), 0)
        password.extend(random.choices(all_chars, k=remaining_length))
        
        # 打乱顺序
        random.shuffle(password)
        password = ''.join(password)
        
        # 检查连续重复字符
        valid = True
        if max_consecutive_duplicates < len(password):
            for i in range(len(password) - max_consecutive_duplicates):
                if all(c == password[i] for c in password[i:i+max_consecutive_duplicates+1]):
                    valid = False
                    break
        
        if valid:
            return password
