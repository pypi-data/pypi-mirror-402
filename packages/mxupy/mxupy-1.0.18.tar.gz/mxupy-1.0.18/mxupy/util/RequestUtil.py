import requests
from mxupy import IM

def get_ip():
    """ 获取公网ip

    Returns:
        str: 公网ip
    """
    try:
        response = requests.get('https://ipinfo.io/ip')
        if response.status_code == 200:
            return response.text
        else:
            return "0.0.0.0"
    except:
        return "0.0.0.0"
    
def get_user_id(request):
    """ 获取会话用户id

    Returns:
        str: 公网ip
    """
    current_user = request.state.current_user
    userId = current_user["userId"]
    return userId

def remote_call(func):
    """
    远程调用函数，返回结果。
    
    get 示例：
    url = "http://192.168.2.19:8089/tts/query?code=123"
    im = remote_call(lambda: requests.get(url))

    post 示例1：
    url = "http://192.168.2.19:8089/tts/do1?code=123"
    json = {
        "audio_url": "1.mp3",
        "video_url": "1.mp4",
    }
    headers = {
        'Content-Type': 'application/json'
    }
    im = remote_call(lambda: requests.post(url, json=json, headers=headers))
    
    post 示例2：
    url = "http://192.168.2.19:8089/tts/do2?code=123"
    data = {
        'text': text,
        'prompt_text': model.text
    }
    im = mu.remote_call(lambda: requests.post(url, data=data))

    Args:
        func: 请求函数，返回 requests.Response 对象。

    Returns:
        IM: 包含错误信息的对象。
    """
    im = IM()
    
    try:
        
        response = func()
        response.raise_for_status()
        im.data = response.text
        return im
    
    except requests.exceptions.HTTPError as e:
        print("HTTP 错误:", e)
        return IM(False, f"HTTP错误: {e}", None, 500, 'HTTPError')
    except requests.exceptions.ConnectionError as e:
        print("连接错误:", e)
        return IM(False, f"连接错误: {e}", None, 500, 'ConnectionError')
    except requests.exceptions.Timeout as e:
        print("超时错误:", e)
        return IM(False, f"超时错误: {e}", None, 500, 'TimeoutError')
    except requests.exceptions.RequestException as e:
        print("请求错误:", e)
        return IM(False, f"请求错误: {e}", None, 500, 'RequestException')
    except Exception as e:
        print("未知错误:", e)
        return IM(False, f"未知错误: {e}", None, 500, 'UnexpectedError')

if __name__ == '__main__':
    print(get_ip())
    
    url = "http://192.168.2.19:8089/tts/query?code=123"
    im = remote_call(lambda: requests.get(url))
    
    
    