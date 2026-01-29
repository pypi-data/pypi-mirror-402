# import psutil

# def cpu_percent():
#     """ cpu百分比

#     Returns:
#         float: 百分比
#     """
#     cpu_usage = psutil.cpu_percent(interval=1)
#     return cpu_usage
# # 内存使用情况
# memory = psutil.virtual_memory()
# print(f"Total Memory: {memory.total / (1024 ** 3):.2f} GB")
# print(f"Available Memory: {memory.available / (1024 ** 3):.2f} GB")
# print(f"Used Memory: {memory.used / (1024 ** 3):.2f} GB")
# print(f"Memory Usage: {memory.percent}%")