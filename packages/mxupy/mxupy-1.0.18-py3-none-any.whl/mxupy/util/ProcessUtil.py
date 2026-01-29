import os
import sys
from mxupy import IM,perror
import subprocess
import threading
import asyncio
processes = {}



def _proc_log_output(proc: subprocess.Popen, status_queue: asyncio.Queue):
    """
    把子进程 stdout/stderr 逐行放到 queue（线程内）
    """
    try:
        ''' 
        tqdm  默认就是用  \r  回车符把光标拉回行首再覆盖，所以你的代码永远等不到  \n ，也就永远  status_queue.put_nowait  不出去。思路：别等  \n ，把“遇到  \r  就当成一行结束”即可。
        '''
        buf = bytearray()
        while True:
            # 一次读 4096，性能比 read(1) 高得多
            chunk = proc.stdout.read(4096)
            if not chunk: # 子进程结束
                break
            buf.extend(chunk)

            # 把缓冲区里所有“完整行”都抛出去
            while True:
                # 找最早出现的行尾符号
                nl = buf.find(b'\n')
                cr = buf.find(b'\r')
                if nl == -1 and cr == -1: # 没找到完整行，继续读
                    break
                eol = min(nl if nl != -1 else len(buf),
                        cr if cr != -1 else len(buf))
                line_bytes = buf[:eol+1] # 把 \r 或 \n 也带上
                del buf[:eol+1]

                # 解码并丢到队列
                status_queue.put_nowait(IM(type='data',
                                    data=line_bytes.decode(errors='ignore')))

        # 子进程结束后，把剩余内容也抛出去（可能没有换行）
        if buf:
            status_queue.put_nowait(IM(type='data',
                                data=buf.decode(errors='ignore')))

        if proc.pid in processes:
            del processes[proc.pid]

        status_queue.put_nowait(IM(type="stop", data={"pid": proc.pid}))
        status_queue.put_nowait(None)  # 结束标记
        

    except Exception as e:
        msg=str(e)
        status_queue.put_nowait(IM(type="error", msg=msg))
        
    finally:
        proc.wait()
        status_queue.put_nowait(None)  # 结束标记

def run(appInfo,status_queue):
    """
    SSE 端点，实时输出子进程所有日志
    """
    try:
        appInfo=appInfo["params"]
        type=appInfo.get("type","cmd")
        command = appInfo["command"]
        args = appInfo["args"]

        if type=="python":
            command = os.path.abspath(command)
            cmd = [sys.executable, command]  # 你的脚本
            cmd.extend(args)
        else:
            cmd = [command]
            cmd.extend(args)

        kwargs = dict(
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
            universal_newlines=False,   # 原始字节
        )
        if os.name == "nt":
            # Windows：隐藏窗口，保证 tqdm 彩色输出
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd, **kwargs)
        # 将进程添加到全局变量中
        processes[proc.pid] = proc

        t = threading.Thread(target=_proc_log_output,args=(proc, status_queue), daemon=True)
        t.start()

        # 首先返回进程PID
        status_queue.put_nowait(IM(type="start", data={"pid": proc.pid}))

        return IM(True,data={"pid":proc.pid})

    except Exception as e:
        msg=str(e)
        status_queue.put_nowait(IM(type="error", msg=msg))
        return IM(False,perror('ProcessUtil.run',e))


def kill(pid):
    """
    终止指定PID的进程
    """
    try:
        if pid in processes:
            proc = processes[pid]
            if proc.poll() is None:  # 进程仍在运行
                proc.terminate()
                try:
                    proc.wait(timeout=5)  # 等待最多5秒
                except subprocess.TimeoutExpired:
                    # 如果超时，强制杀死进程
                    proc.kill()
                    proc.wait()  # 等待进程完全终止
            # 从全局变量中移除
            del processes[pid]
            return IM(True, f'Process with PID {pid} terminated.')
        else:
            return IM(False, f'No process with PID {pid} found.')
    except Exception as e:
        return IM(False,perror('kill_proc',e))

def list():
    """
    列出所有正在运行的进程
    """
    # 清理已经结束但仍在字典中的进程
    dead_processes = []
    for pid, proc in processes.items():
        if proc.poll() is not None:  # 进程已经结束
            dead_processes.append(pid)

    for pid in dead_processes:
        del processes[pid]

    # 返回当前活动进程列表
    active_processes = {}
    for pid, proc in processes.items():
        active_processes[pid] = {
            "pid": pid,
            "returncode": proc.returncode
        }
    return active_processes