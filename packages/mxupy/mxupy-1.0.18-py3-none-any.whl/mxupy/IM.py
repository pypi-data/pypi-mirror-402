import pydantic
from pydantic import BaseModel
from typing import Any
import json
import mxupy as mu
from datetime import datetime, date


class IM(BaseModel):
    """ 一般函数执行后返回的结果类

    Args:
        BaseModel (pydantic.BaseModel): 用于前端调用后端时，对返回的结果类进行校验

    Raises:
        TypeError: 未知类型

    Returns:
        IM: 结果类
    """
    msg: str = pydantic.Field('', description="API message")
    data: Any = pydantic.Field(None, description="API data")
    code: int = pydantic.Field(200, description="API status code")
    type: str = pydantic.Field('', description="API status type")
    success: bool = pydantic.Field(True, description="API status")
    status: str = pydantic.Field('', description="API status detail")

    def __init__(self, success=True, msg='', data=None, code=200, type='', status=''):
        """ 初始化结果

        Args:
            success (bool, optional): 成功否
            msg (str, optional): 消息
            data (any, optional): 数据
            code (int, optional): 编码，success时默认为200，反之默认为500
            type (str, optional): 用户自定义类型，比如：add|update
            status (str, optional): 状态详情
        """
        super().__init__()

        self.success = success
        self.msg = msg
        self.data = data
        self.type = type
        self.status = status
        self.code = code if success and code == 200 else 500

    def __getstate__(self):
        return {'type': self.type, 'msg': self.msg}

    def __str__(self):
        return self.to_string()

    @property
    def error(self):
        """ 失败否，与成功否相反

        Returns:
            bool: 失败否
        """
        return not self.success

    def set_error(self, msg=None, code=500, type='', status=''):
        """ 设置为失败

        Args:
            msg (str, optional): 消息
            code (int, optional): 编码
            type (str, optional): 类型
            status (str, optional): 状态详情

        Returns:
            IM: 结果类
        """
        self.success = False
        self.msg = msg if msg else self.msg
        self.code = code
        self.type = type
        self.status = status

        return self

    def set_success(self, data=None, code=200, msg=None, type='', status=''):
        """ 设置为成功

        Args:
            data (any, optional): 数据
            code (int, optional): 编码
            msg (str, optional): 消息
            type (str, optional): 类型
            status (str, optional): 状态详情


        Returns:
            IM: 结果类
        """
        self.success = True
        self.data = data
        self.code = code
        self.msg = msg
        self.type = type
        self.status = status

        return self

    def datetime_handler(self, x):
        if isinstance(x, datetime) or isinstance(x, date):
            return x.isoformat()
        raise TypeError("Unknown type")

    def dumps(self):
        return json.dumps(mu.toSerializable(self), default=self.datetime_handler)

    def to_string(self) -> str:
        return f"{self.code}：{self.msg}-{self.data}" if self.success else f"{self.code}：{self.msg}"

    @staticmethod
    def from_dict(obj):
        """从字典或IM对象创建IM对象"""
        # 如果已经是IM对象，直接返回
        if isinstance(obj, IM):
            return obj

        # 如果是字典，从字典创建IM对象
        if isinstance(obj, dict):
            im = IM()
            im.success = obj.get('success')
            im.msg = obj.get('msg')
            im.data = obj.get('data')
            im.code = obj.get('code')
            im.type = obj.get('type')
            im.status = obj.get('status', '')
            return im

        # 如果都不是，抛出异常
        raise TypeError("Object must be either IM instance or dict")

    @staticmethod
    def to_dict(obj):
        """将IM对象或字典转换为字典，如果是IM对象则包含 error 属性"""
        # 如果已经是字典，直接返回
        if isinstance(obj, dict):
            return obj

        # 如果是IM对象，转换为字典
        if isinstance(obj, IM):
            return {
                'success': obj.success,
                'msg': obj.msg,
                'data': obj.data,
                'type': obj.type,
                'code': obj.code,
                'error': obj.error,
                'status': obj.status
            }

        # 如果都不是，抛出异常
        raise TypeError("Object must be either IM instance or dict")