import json
    
class DateTimeEncoder(json.JSONEncoder):
    """ 时间格式化为 ISO 8601 格式
        json dump 的时候，如果对象中包含时间类型，会引发错误
        原因是
        示例：json.dumps(vote.to_dict(), cls=DateTimeUtil.DateTimeEncoder)

    Args:
        json (obj): 时间类型被转义
    """
    def default(self, obj):
        from datetime import datetime
        if isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)



# class DateTimeEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, datetime):
#             return obj.strftime('%Y-%m-%dT%H:%M:%S.%fZ')  # 格式化为ISO 8601格式
#         return super(DateTimeEncoder, self).default(obj)
    
    
    