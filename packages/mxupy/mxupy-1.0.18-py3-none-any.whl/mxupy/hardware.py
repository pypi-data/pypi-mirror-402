import platform
from datetime import datetime
import mxupy as mu

def getAllLocalIPs():
    import socket
    try:
        # 获取所有网络接口
        interfaces = socket.getaddrinfo(socket.gethostname(), None, family=socket.AF_INET)
        # 提取IP地址
        ips = [info[4][0] for info in interfaces]
        return ips
    except Exception as e:
        print(f"无法获取本机IP: {e}")
        return None


def getDiskInfo():
    """
    获取磁盘信息。

    返回:
        dict: 包含磁盘信息的字典。
    """
    import psutil

    infostr = ['', '']
    mu.sprt(infostr)
    # Disk Information
    print("=" * 40, "Disk Details", "=" * 40)
    print("Partitions and Usage:")
    # get all disk partitions
    partitions = psutil.disk_partitions()
    partitions_info = []
    for partition in partitions:
        print(f"=== Device: {partition.device} ===")
        print(f"  Mountpoint: {partition.mountpoint}")
        print(f"  File system type: {partition.fstype}")
        try:
            partition_usage = psutil.disk_usage(partition.mountpoint)
            partition_info = {
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "file_system_type": partition.fstype,
                "total_size": mu.formatBytes(partition_usage.total),
                "used": mu.formatBytes(partition_usage.used),
                "free": mu.formatBytes(partition_usage.free),
                "percentage": partition_usage.percent
            }
            partitions_info.append(partition_info)
            print(f"  Total Size: {partition_info['total_size']}")
            print(f"  Used: {partition_info['used']}")
            print(f"  Free: {partition_info['free']}")
            print(f"  Percentage: {partition_info['percentage']}%")
        except PermissionError:
            # this can be catched due to the disk that
            # isn't ready
            continue
    # get IO statistics since boot
    disk_io = psutil.disk_io_counters()
    disk_io_info = {
        "total_read": mu.formatBytes(disk_io.read_bytes),
        "total_write": mu.formatBytes(disk_io.write_bytes)
    }
    print(f"Total read: {disk_io_info['total_read']}")
    print(f"Total write: {disk_io_info['total_write']}")

    mu.eprt(infostr)

    # 添加用户友好的描述
    desc_parts = []
    for partition in partitions_info:
        desc_parts.append(f"设备 {partition['device']} ({partition['file_system_type']}) 总容量: {partition['total_size']}, 已使用: {partition['used']}, 可用: {partition['free']} ({partition['percentage']}%)")
    desc_parts.append(f"启动以来总读取: {disk_io_info['total_read']}, 总写入: {disk_io_info['total_write']}")
    desc = "\n".join(desc_parts)

    return {
        "partitions": partitions_info,
        "disk_io": disk_io_info,
        "desc": desc
    }


def getCPUInfo():
    """
    获取 CPU 信息。

    返回:
        dict: 包含 CPU 信息的字典。
    """

    import psutil
    infostr = ['', '']
    mu.sprt(infostr)
    print("=" * 40, "CPU Details", "=" * 40)

    # number of cores
    physical_cores = psutil.cpu_count(logical=False)
    total_cores = psutil.cpu_count(logical=True)
    print("Physical cores:", physical_cores)
    print("Total cores:", total_cores)
    
    # CPU frequencies
    cpufreq = psutil.cpu_freq()
    print(f"Max Frequency: {cpufreq.max:.2f}Mhz")
    print(f"Min Frequency: {cpufreq.min:.2f}Mhz")
    print(f"Current Frequency: {cpufreq.current:.2f}Mhz")
    
    # CPU usage
    cpu_usage_per_core = []
    print("CPU Usage Per Core:")
    for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
        cpu_usage_per_core.append({f"Core {i}": percentage})
        print(f"Core {i}: {percentage}%", end=', ')
    total_cpu_usage = psutil.cpu_percent()
    print(f"\nTotal CPU Usage: {total_cpu_usage}%")
    
    cpu_info = {
        "physical_cores": physical_cores,
        "total_cores": total_cores,
        "cpu_frequency": {
            "max": round(cpufreq.max, 2),
            "min": round(cpufreq.min, 2),
            "current": round(cpufreq.current, 2)
        },
        "cpu_usage_per_core": cpu_usage_per_core,
        "total_cpu_usage": total_cpu_usage
    }
    
    mu.eprt(infostr)

    # 添加用户友好的描述
    desc = f"CPU物理核心数: {physical_cores}, 逻辑核心数: {total_cores}\n"
    desc += f"CPU频率 - 最大: {cpufreq.max:.2f}MHz, 最小: {cpufreq.min:.2f}MHz, 当前: {cpufreq.current:.2f}MHz\n"
    desc += f"CPU总使用率: {total_cpu_usage}%\n"
    # desc += "各核心使用情况:\n"
    # for i, core_info in enumerate(cpu_usage_per_core):
    #     for core_name, usage in core_info.items():
    #         desc += f"  {core_name}: {usage}%\n"

    return {
        **cpu_info,
        "desc": desc.strip()
    }


def getGPUInfo(idx=0):
    """
    获取 GPU 信息。

    参数:
        idx (int, 可选): GPU 索引，默认为 0。

    返回:
        dict: 包含 GPU 信息的字典。
    """
    import GPUtil

    from tabulate import tabulate
    infostr = ['', '']
    mu.sprt(infostr)
    print("=" * 40, "GPU Details", "=" * 40)

    gpus = GPUtil.getGPUs()
    gpu_list = []
    for i, gpu in enumerate(gpus):
        if i != idx:
            continue
        # get the GPU id
        gpu_id = gpu.id
        # name of GPU
        gpu_name = gpu.name
        # get % percentage of GPU usage of that GPU
        gpu_load = gpu.load*100
        # get free memory in MB format
        gpu_free_memory = mu.formatBytes(gpu.memoryFree*1024*1024)
        # get used memory
        gpu_used_memory = mu.formatBytes(gpu.memoryUsed*1024*1024)
        # get total memory
        gpu_total_memory = mu.formatBytes(gpu.memoryTotal*1024*1024)
        # get GPU temperature in Celsius
        gpu_temperature = gpu.temperature
        gpu_uuid = gpu.uuid
        
        gpu_info = {
            "id": gpu_id,
            "name": gpu_name,
            "load": gpu_load,
            "free_memory": gpu_free_memory,
            "used_memory": gpu_used_memory,
            "total_memory": gpu_total_memory,
            "temperature": gpu_temperature,
            "uuid": gpu_uuid
        }
        gpu_list.append(gpu_info)

    print(tabulate([(g["id"], g["name"], f"{g['load']:.1f}%", g["free_memory"], g["used_memory"], g["total_memory"], f"{g['temperature']} °C", g["uuid"]) for g in gpu_list], 
                   headers=("id", "name", "load", "free memory", "used memory", "total memory", "temperature", "uuid")))

    mu.eprt(infostr)

    # 添加用户友好的描述
    desc_parts = []
    for gpu in gpu_list:
        desc_parts.append(f"GPU {gpu['name']} (ID: {gpu['id']})")
        desc_parts.append(f"  显存 - 总计: {gpu['total_memory']}, 已用: {gpu['used_memory']}, 可用: {gpu['free_memory']}")
        desc_parts.append(f"  负载: {gpu['load']:.1f}%, 温度: {gpu['temperature']}°C")
    desc = "\n".join(desc_parts) if desc_parts else "未检测到GPU"

    return {
        "gpus": gpu_list,
        "desc": desc
    }


def getSystemInfo():
    """
    获取系统信息。

    返回:
        dict: 包含系统信息的字典。
    """

    import psutil
    uname = platform.uname()

    boot_time_timestamp = psutil.boot_time()

    info_dict = {
        "system": uname.system,
        "node_name": uname.node,
        "release": uname.release,
        "version": uname.version,
        "machine": uname.machine,
        "processor": uname.processor,
        "boot_time": datetime.fromtimestamp(boot_time_timestamp).strftime('%Y/%m/%d %H:%M:%S')
    }

    # 添加用户友好的描述
    desc = f"系统: {uname.system} {uname.release}\n"
    desc += f"计算机名: {uname.node}\n"
    desc += f"处理器: {uname.processor}\n"
    desc += f"系统启动时间: {datetime.fromtimestamp(boot_time_timestamp).strftime('%Y/%m/%d %H:%M:%S')}"

    return {
        **info_dict,
        "desc": desc
    }


def getMemoryInfo():
    """
    获取内存信息。

    返回:
        dict: 包含内存信息的字典。
    """

    import psutil
    infostr = ['', '']
    mu.sprt(infostr)
    print("=" * 40, "Memory Details", "=" * 40)

    virtual_memory = psutil.virtual_memory()
    swap_memory = psutil.swap_memory()

    memory_info = {
        "virtual_memory": {
            "total": mu.formatBytes(virtual_memory.total),
            "available": mu.formatBytes(virtual_memory.available),
            "used": mu.formatBytes(virtual_memory.used),
            "usage_percentage": virtual_memory.percent
        },
        "swap_memory": {
            "total": mu.formatBytes(swap_memory.total),
            "used": mu.formatBytes(swap_memory.used),
            "free": mu.formatBytes(swap_memory.free),
            "usage_percentage": swap_memory.percent
        }
    }

    print("Virtual Memory:\n", memory_info["virtual_memory"])
    print("Swap Memory:\n", memory_info["swap_memory"])

    mu.eprt(infostr)

    # 添加用户友好的描述
    desc = f"物理内存 - 总计: {memory_info['virtual_memory']['total']}, 已用: {memory_info['virtual_memory']['used']}, 可用: {memory_info['virtual_memory']['available']} ({memory_info['virtual_memory']['usage_percentage']}%)\n"
    desc += f"交换内存 - 总计: {memory_info['swap_memory']['total']}, 已用: {memory_info['swap_memory']['used']}, 可用: {memory_info['swap_memory']['free']} ({memory_info['swap_memory']['usage_percentage']}%)"

    return {
        **memory_info,
        "desc": desc
    }


if __name__ == '__main__':

    # print(getSystemInfo())
    # print(getGPUInfo())
    # print(getMemoryInfo())
    # print(getCPUInfo())
    # print(getDiskInfo())
    print(getAllLocalIPs())